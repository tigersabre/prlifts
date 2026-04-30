"""
insight_service.py
PRLifts Backend

AI workout insight background task and supporting utilities.

process_insight_job is enqueued as a FastAPI BackgroundTask on POST /v1/jobs.
It fetches the active PromptTemplate for 'insight', calls Claude, validates the
response, updates the Job record, and writes an AIRequestLog entry.

Response validation:
  - Length: 10–280 characters (configurable via AI_RESPONSE_MAX_LENGTH env var)
  - Forbidden phrases: checked against config/ai_forbidden_phrases.txt

When AI_PROVIDERS_MOCKED=true (test environment) a MockAnthropicClient is used
so no real API calls are made in tests. See docs/ENV_CONFIG.md.

See docs/ARCHITECTURE.md — AI Operations Async Pattern.
See docs/JOB_CATALOG.md — background job lifecycle.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID

import anthropic as _anthropic

from app.repositories.job_repository import (
    AIRequestLogRepository,
    JobRepository,
    PromptTemplateRepository,
)

logger = logging.getLogger(__name__)

_FORBIDDEN_PHRASES_PATH = (
    Path(__file__).parent.parent.parent / "config" / "ai_forbidden_phrases.txt"
)
_INSIGHT_MIN_LENGTH = 10
_INSIGHT_MAX_LENGTH = 280
_INSIGHT_FALLBACK = (
    "We couldn't generate your workout insight right now. "
    "Check back after your next session."
)
_NO_TEMPLATE_ERROR = "Service temporarily unavailable. Please try again later."


# ── AI client abstraction ──────────────────────────────────────────────────────


@dataclass
class AnthropicResponse:
    """Minimal wrapper around a Claude API response."""

    content: str
    input_tokens: int
    output_tokens: int


class AnthropicClientProtocol(Protocol):
    """
    Abstract interface for the Anthropic Claude client.

    Production uses RealAnthropicClient; tests inject MockAnthropicClient.
    """

    def create_message(
        self,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
    ) -> AnthropicResponse: ...


class RealAnthropicClient:
    """
    Thin wrapper around the Anthropic SDK that satisfies AnthropicClientProtocol.
    """

    def __init__(self, api_key: str) -> None:
        self._client = _anthropic.Anthropic(api_key=api_key)

    def create_message(
        self,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
    ) -> AnthropicResponse:
        params: list[_anthropic.types.MessageParam] = [
            {"role": m["role"], "content": m["content"]} for m in messages
        ]
        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=params,
        )
        first_block = response.content[0]
        if not isinstance(first_block, _anthropic.types.TextBlock):
            raise ValueError(f"Unexpected content block type: {type(first_block)}")
        return AnthropicResponse(
            content=first_block.text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )


class MockAnthropicClient:
    """
    In-memory mock for the Anthropic client. Used when AI_PROVIDERS_MOCKED=true.

    Returns a configurable canned response without making any network calls.
    Defaults to a short, passing insight that clears all validation gates.
    """

    def __init__(
        self,
        mock_response: str = (
            "Solid session today — you completed your workout and kept "
            "the consistency that builds long-term progress."
        ),
        raise_on_call: Exception | None = None,
    ) -> None:
        self._mock_response = mock_response
        self._raise_on_call = raise_on_call

    def create_message(
        self,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
    ) -> AnthropicResponse:
        if self._raise_on_call is not None:
            raise self._raise_on_call
        return AnthropicResponse(
            content=self._mock_response,
            input_tokens=100,
            output_tokens=len(self._mock_response.split()),
        )


def get_anthropic_client(api_key: str, *, mocked: bool) -> AnthropicClientProtocol:
    """
    Factory that returns the appropriate client based on environment config.

    Args:
        api_key: CLAUDE_API_KEY from settings (ignored when mocked).
        mocked: True when AI_PROVIDERS_MOCKED=true in environment.

    Returns:
        MockAnthropicClient in test environment, RealAnthropicClient otherwise.
    """
    if mocked:
        return MockAnthropicClient()
    return RealAnthropicClient(api_key=api_key)


# ── Forbidden phrase / length validation ──────────────────────────────────────


def load_forbidden_phrases(path: Path = _FORBIDDEN_PHRASES_PATH) -> list[str]:
    """
    Reads the forbidden phrases list from config/ai_forbidden_phrases.txt.

    Each non-empty, non-comment line is a phrase (case-insensitive matching).
    Returns an empty list if the file is missing — callers should log a warning.
    """
    if not path.exists():
        logger.warning(
            "Forbidden phrases file not found",
            extra={"path": str(path)},
        )
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [ln.strip().lower() for ln in lines if ln.strip() and not ln.startswith("#")]


def validate_insight_response(
    text: str,
    forbidden_phrases: list[str],
    *,
    min_length: int = _INSIGHT_MIN_LENGTH,
    max_length: int = _INSIGHT_MAX_LENGTH,
) -> tuple[bool, str]:
    """
    Validates a Claude insight response against length and content constraints.

    Args:
        text: The raw response text from Claude.
        forbidden_phrases: List of lowercase phrases that must not appear.
        min_length: Minimum character count (inclusive).
        max_length: Maximum character count (inclusive).

    Returns:
        (True, "") when valid.
        (False, reason) when invalid — reason describes the failure.
    """
    stripped = text.strip()
    if len(stripped) < min_length:
        return False, f"response too short: {len(stripped)} chars (min {min_length})"
    if len(stripped) > max_length:
        return False, f"response too long: {len(stripped)} chars (max {max_length})"

    lower = stripped.lower()
    for phrase in forbidden_phrases:
        if phrase in lower:
            return False, f"forbidden phrase detected: '{phrase}'"

    return True, ""


# ── Background task ───────────────────────────────────────────────────────────


async def process_insight_job(
    job_id: UUID,
    user_id: UUID,
    workout_id: UUID,
    job_repo: JobRepository,
    prompt_repo: PromptTemplateRepository,
    ai_log_repo: AIRequestLogRepository,
    ai_client: AnthropicClientProtocol,
    forbidden_phrases: list[str],
) -> None:
    """
    Executes an insight job asynchronously as a FastAPI BackgroundTask.

    Sequence:
      1. Mark job as processing.
      2. Fetch the active PromptTemplate for 'insight' feature.
      3. Build workout context and call Claude.
      4. Validate the response (length + forbidden phrases).
      5. Update job to complete or failed.
      6. Write AIRequestLog entry.

    Failures at any step set the job to failed with a user-safe message.
    No exceptions are propagated — all errors are captured to the job record.

    Args:
        job_id: The Job to process.
        user_id: Owner of the job.
        workout_id: The workout this insight is for.
        job_repo: JobRepository for status updates.
        prompt_repo: PromptTemplateRepository to fetch the active template.
        ai_log_repo: AIRequestLogRepository for the audit log entry.
        ai_client: Anthropic client (real or mock).
        forbidden_phrases: Lowercase phrases that must not appear in the response.
    """
    from app.ai_models import AIModels

    await job_repo.update(job_id, {"status": "processing"})

    template = await prompt_repo.get_active("insight")
    if template is None:
        logger.error(
            "No active insight prompt template found",
            extra={"job_id": str(job_id), "user_id": str(user_id)},
        )
        await job_repo.update(
            job_id,
            {"status": "failed", "error_message": _NO_TEMPLATE_ERROR},
        )
        return

    context = {
        "workout_id": str(workout_id),
    }
    try:
        user_message = template.prompt_text.format(**context)
    except KeyError as exc:
        logger.error(
            "Prompt template formatting failed",
            extra={"job_id": str(job_id), "key_error": str(exc)},
        )
        await job_repo.update(
            job_id,
            {"status": "failed", "error_message": _INSIGHT_FALLBACK},
        )
        return

    start_ms = time.monotonic()
    ai_response_text: str | None = None
    try:
        msg: dict[str, Any] = {"role": "user", "content": user_message}
        ai_response = ai_client.create_message(
            model=AIModels.CLAUDE,
            max_tokens=1000,
            messages=[msg],
        )
        ai_response_text = ai_response.content
    except Exception as exc:
        elapsed_ms = int((time.monotonic() - start_ms) * 1000)
        logger.error(
            "Claude API call failed",
            extra={
                "job_id": str(job_id),
                "user_id": str(user_id),
                "error": str(exc),
            },
        )
        await _write_ai_log(
            ai_log_repo=ai_log_repo,
            user_id=user_id,
            prompt_template_id=template.id,
            job_id=job_id,
            model=AIModels.CLAUDE,
            response=None,
            duration_ms=elapsed_ms,
            quality_score=None,
        )
        await job_repo.update(
            job_id,
            {"status": "failed", "error_message": _INSIGHT_FALLBACK},
        )
        return

    elapsed_ms = int((time.monotonic() - start_ms) * 1000)
    valid, reason = validate_insight_response(ai_response_text, forbidden_phrases)

    if not valid:
        logger.warning(
            "Insight response failed validation",
            extra={
                "job_id": str(job_id),
                "user_id": str(user_id),
                "reason": reason,
            },
        )
        await _write_ai_log(
            ai_log_repo=ai_log_repo,
            user_id=user_id,
            prompt_template_id=template.id,
            job_id=job_id,
            model=AIModels.CLAUDE,
            response=ai_response_text,
            duration_ms=elapsed_ms,
            quality_score=None,
        )
        await job_repo.update(
            job_id,
            {"status": "failed", "error_message": _INSIGHT_FALLBACK},
        )
        return

    await _write_ai_log(
        ai_log_repo=ai_log_repo,
        user_id=user_id,
        prompt_template_id=template.id,
        job_id=job_id,
        model=AIModels.CLAUDE,
        response=ai_response_text,
        duration_ms=elapsed_ms,
        quality_score=None,
    )
    await job_repo.update(
        job_id,
        {
            "status": "complete",
            "result": {
                "insight": ai_response_text.strip(),
                "workout_id": str(workout_id),
            },
        },
    )

    logger.info(
        "Insight job complete",
        extra={"job_id": str(job_id), "user_id": str(user_id)},
    )


async def _write_ai_log(
    ai_log_repo: AIRequestLogRepository,
    user_id: UUID,
    prompt_template_id: UUID,
    job_id: UUID,
    model: str,
    response: str | None,
    duration_ms: int,
    quality_score: float | None,
) -> None:
    try:
        await ai_log_repo.create(
            user_id=user_id,
            prompt_template_id=prompt_template_id,
            job_id=job_id,
            endpoint="insight",
            model=model,
            response=response,
            duration_ms=duration_ms,
            quality_score=quality_score,
        )
    except Exception as exc:
        logger.error(
            "Failed to write AIRequestLog",
            extra={"job_id": str(job_id), "error": str(exc)},
        )
