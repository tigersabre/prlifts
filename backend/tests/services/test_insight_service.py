"""
test_insight_service.py
PRLifts Backend Tests

Unit tests for the insight service:
  - validate_insight_response: length and forbidden phrase constraints
  - load_forbidden_phrases: file loading
  - process_insight_job: full pipeline including failure paths
  - MockAnthropicClient / get_anthropic_client factory

See docs/PROMPT_EVAL_CASES.md — Cases 1–10 for insight validation expectations.
See docs/AI_RESPONSE_EXAMPLES.md — good and bad response examples.
See GitHub Issue #39 for acceptance criteria.
"""

import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AI_PROVIDERS_MOCKED", "true")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-supabase-jwt-secret-for-unit-tests")

from app.repositories.job_repository import (  # noqa: E402
    AIRequestLogRecord,
    JobRecord,
    PromptTemplateRecord,
)
from app.services.insight_service import (  # noqa: E402
    _INSIGHT_FALLBACK,
    _NO_TEMPLATE_ERROR,
    MockAnthropicClient,
    RealAnthropicClient,
    get_anthropic_client,
    load_forbidden_phrases,
    process_insight_job,
    validate_insight_response,
)

# ── Constants ─────────────────────────────────────────────────────────────────

_USER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_WORKOUT_ID = UUID("11111111-1111-1111-1111-111111111111")
_JOB_ID = UUID("22222222-2222-2222-2222-222222222222")
_TEMPLATE_ID = UUID("33333333-3333-3333-3333-333333333333")
_NOW = datetime(2026, 4, 29, 12, 0, 0, tzinfo=UTC)

_VALID_INSIGHT = (
    "Solid session — you completed your workout and built the foundation "
    "for long-term strength gains."
)
_DEFAULT_TEMPLATE = PromptTemplateRecord(
    id=_TEMPLATE_ID,
    feature="insight",
    version="1.0",
    prompt_text="Generate insight for workout {workout_id}.",
    is_active=True,
    created_at=_NOW,
    deactivated_at=None,
)


# ── Fake repositories ─────────────────────────────────────────────────────────


class FakeJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[UUID, JobRecord] = {
            _JOB_ID: JobRecord(
                id=_JOB_ID,
                user_id=_USER_ID,
                job_type="insight",
                status="pending",
                result=None,
                error_message=None,
                created_at=_NOW,
                started_at=None,
                completed_at=None,
                expires_at=_NOW + timedelta(minutes=5),
            )
        }

    async def create(self, user_id: UUID, job_type: str) -> JobRecord:
        raise NotImplementedError

    async def get_by_id(self, job_id: UUID) -> JobRecord | None:
        return self._jobs.get(job_id)

    async def update(self, job_id: UUID, updates: dict[str, Any]) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            return
        for key, val in updates.items():
            object.__setattr__(job, key, val)

    async def expire_stale(self, now: datetime) -> int:
        return 0


class FakePromptTemplateRepository:
    def __init__(
        self, template: PromptTemplateRecord | None = _DEFAULT_TEMPLATE
    ) -> None:
        self._template = template

    async def get_active(self, feature: str) -> PromptTemplateRecord | None:
        if self._template and self._template.feature == feature:
            return self._template
        return None


class FakeAIRequestLogRepository:
    def __init__(self) -> None:
        self.logs: list[AIRequestLogRecord] = []

    async def create(
        self,
        user_id: UUID,
        prompt_template_id: UUID | None,
        job_id: UUID | None,
        endpoint: str,
        model: str,
        response: str | None,
        duration_ms: int,
        quality_score: float | None,
    ) -> AIRequestLogRecord:
        record = AIRequestLogRecord(
            id=uuid4(),
            user_id=user_id,
            prompt_template_id=prompt_template_id,
            job_id=job_id,
            endpoint=endpoint,
            response=response,
            model=model,
            quality_score=quality_score,
            duration_ms=duration_ms,
            created_at=_NOW,
            expires_at=_NOW + timedelta(days=30),
        )
        self.logs.append(record)
        return record


# ── validate_insight_response ─────────────────────────────────────────────────


class TestValidateInsightResponse:
    def test_valid_response_passes(self) -> None:
        valid, reason = validate_insight_response(_VALID_INSIGHT, [])
        assert valid is True
        assert reason == ""

    def test_response_too_short_fails(self) -> None:
        valid, reason = validate_insight_response("Short.", [])
        assert valid is False
        assert "too short" in reason

    def test_response_too_long_fails(self) -> None:
        long_text = "A" * 281
        valid, reason = validate_insight_response(long_text, [])
        assert valid is False
        assert "too long" in reason

    def test_exactly_min_length_passes(self) -> None:
        text = "A" * 10
        valid, _ = validate_insight_response(text, [])
        assert valid is True

    def test_exactly_max_length_passes(self) -> None:
        text = "A" * 280
        valid, _ = validate_insight_response(text, [])
        assert valid is True

    def test_forbidden_phrase_fails(self) -> None:
        text = "You should lose weight to reach your goals."
        valid, reason = validate_insight_response(text, ["lose weight"])
        assert valid is False
        assert "lose weight" in reason

    def test_forbidden_phrase_case_insensitive(self) -> None:
        text = "This will help you Burn Fat efficiently today."
        valid, reason = validate_insight_response(text, ["burn fat"])
        assert valid is False
        assert "burn fat" in reason

    def test_multiple_forbidden_phrases_first_match_fails(self) -> None:
        text = "Slim down and lose weight with this session."
        valid, reason = validate_insight_response(text, ["slim down", "lose weight"])
        assert valid is False

    def test_empty_forbidden_list_passes_content(self) -> None:
        text = "You could burn fat and lose weight with this workout."
        valid, _ = validate_insight_response(text, [])
        assert valid is True

    def test_whitespace_stripped_before_length_check(self) -> None:
        text = "  " + "A" * 10 + "  "
        valid, _ = validate_insight_response(text, [])
        assert valid is True

    # Prompt eval case 8 — strict length constraint
    def test_prompt_eval_case_8_strict_length(self) -> None:
        text_281 = "A" * 281
        valid, reason = validate_insight_response(text_281, [])
        assert valid is False
        assert "too long" in reason

    # Prompt eval case 6 — weight loss forbidden phrases
    def test_prompt_eval_case_6_weight_loss_phrases(self) -> None:
        phrases = ["lose weight", "burn fat", "slim down", "thinner", "calories burned"]
        responses = [
            "Slim down with this HIIT session.",
            "You can burn fat with today's effort.",
            "Great calories burned today.",
        ]
        for text in responses:
            valid, _ = validate_insight_response(text, phrases)
            assert valid is False, f"Expected failure for: {text}"

    # Prompt eval case 7 — medical language
    def test_prompt_eval_case_7_medical_language(self) -> None:
        phrases = ["you have", "you should see a doctor"]
        text = "You have patellofemoral syndrome based on your knee notes."
        valid, _ = validate_insight_response(text, phrases)
        assert valid is False


# ── load_forbidden_phrases ────────────────────────────────────────────────────


class TestLoadForbiddenPhrases:
    def test_loads_real_file(self) -> None:
        phrases = load_forbidden_phrases()
        assert len(phrases) > 0
        assert "lose weight" in phrases

    def test_all_phrases_lowercased(self) -> None:
        phrases = load_forbidden_phrases()
        for phrase in phrases:
            assert phrase == phrase.lower()

    def test_missing_file_returns_empty_list(self) -> None:
        phrases = load_forbidden_phrases(Path("/nonexistent/path/phrases.txt"))
        assert phrases == []

    def test_custom_file_loaded_correctly(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write("burn fat\nlose weight\n# this is a comment\n\n  slim down  \n")
            tmp_path = Path(tmp.name)
        try:
            phrases = load_forbidden_phrases(tmp_path)
            assert "burn fat" in phrases
            assert "lose weight" in phrases
            assert "slim down" in phrases
            assert "# this is a comment" not in phrases
        finally:
            tmp_path.unlink()


# ── MockAnthropicClient ───────────────────────────────────────────────────────


class TestMockAnthropicClient:
    def test_returns_configured_response(self) -> None:
        client = MockAnthropicClient(mock_response="Custom insight text here.")
        msgs = [{"role": "user", "content": "prompt"}]
        resp = client.create_message("model", 100, msgs)
        assert resp.content == "Custom insight text here."

    def test_returns_token_counts(self) -> None:
        client = MockAnthropicClient()
        msgs = [{"role": "user", "content": "prompt"}]
        resp = client.create_message("model", 100, msgs)
        assert resp.input_tokens > 0
        assert resp.output_tokens > 0

    def test_raises_configured_exception(self) -> None:
        client = MockAnthropicClient(raise_on_call=RuntimeError("API down"))
        with pytest.raises(RuntimeError, match="API down"):
            client.create_message("model", 100, [])

    def test_default_response_passes_validation(self) -> None:
        client = MockAnthropicClient()
        msgs = [{"role": "user", "content": "prompt"}]
        resp = client.create_message("model", 100, msgs)
        phrases = load_forbidden_phrases()
        valid, _ = validate_insight_response(resp.content, phrases)
        assert valid is True


# ── get_anthropic_client factory ──────────────────────────────────────────────


class TestGetAnthropicClient:
    def test_returns_mock_when_mocked_true(self) -> None:
        client = get_anthropic_client("fake-key", mocked=True)
        assert isinstance(client, MockAnthropicClient)

    def test_returns_real_when_mocked_false(self) -> None:
        client = get_anthropic_client("sk-ant-fake", mocked=False)
        assert isinstance(client, RealAnthropicClient)


# ── process_insight_job ───────────────────────────────────────────────────────


class TestProcessInsightJob:
    def _make_repos(
        self,
        template: PromptTemplateRecord | None = _DEFAULT_TEMPLATE,
        mock_response: str = _VALID_INSIGHT,
        raise_on_call: Exception | None = None,
    ) -> tuple[
        FakeJobRepository,
        FakePromptTemplateRepository,
        FakeAIRequestLogRepository,
        MockAnthropicClient,
    ]:
        return (
            FakeJobRepository(),
            FakePromptTemplateRepository(template),
            FakeAIRequestLogRepository(),
            MockAnthropicClient(
                mock_response=mock_response, raise_on_call=raise_on_call
            ),
        )

    @pytest.mark.asyncio
    async def test_successful_job_sets_complete(self) -> None:
        job_repo, prompt_repo, ai_log_repo, ai_client = self._make_repos()
        await process_insight_job(
            job_id=_JOB_ID,
            user_id=_USER_ID,
            workout_id=_WORKOUT_ID,
            job_repo=job_repo,
            prompt_repo=prompt_repo,
            ai_log_repo=ai_log_repo,
            ai_client=ai_client,
            forbidden_phrases=[],
        )
        job = job_repo._jobs[_JOB_ID]
        assert job.status == "complete"
        assert job.result is not None
        assert "insight" in job.result
        assert job.result["workout_id"] == str(_WORKOUT_ID)

    @pytest.mark.asyncio
    async def test_ai_request_log_written_on_success(self) -> None:
        job_repo, prompt_repo, ai_log_repo, ai_client = self._make_repos()
        await process_insight_job(
            job_id=_JOB_ID,
            user_id=_USER_ID,
            workout_id=_WORKOUT_ID,
            job_repo=job_repo,
            prompt_repo=prompt_repo,
            ai_log_repo=ai_log_repo,
            ai_client=ai_client,
            forbidden_phrases=[],
        )
        assert len(ai_log_repo.logs) == 1
        log = ai_log_repo.logs[0]
        assert log.prompt_template_id == _TEMPLATE_ID
        assert log.job_id == _JOB_ID
        assert log.endpoint == "insight"
        assert log.response == _VALID_INSIGHT

    @pytest.mark.asyncio
    async def test_no_active_template_sets_failed(self) -> None:
        job_repo, _, ai_log_repo, ai_client = self._make_repos()
        prompt_repo = FakePromptTemplateRepository(template=None)
        await process_insight_job(
            job_id=_JOB_ID,
            user_id=_USER_ID,
            workout_id=_WORKOUT_ID,
            job_repo=job_repo,
            prompt_repo=prompt_repo,
            ai_log_repo=ai_log_repo,
            ai_client=ai_client,
            forbidden_phrases=[],
        )
        job = job_repo._jobs[_JOB_ID]
        assert job.status == "failed"
        assert job.error_message == _NO_TEMPLATE_ERROR

    @pytest.mark.asyncio
    async def test_api_error_sets_failed_with_fallback(self) -> None:
        job_repo, prompt_repo, ai_log_repo, ai_client = self._make_repos(
            raise_on_call=ConnectionError("timeout")
        )
        await process_insight_job(
            job_id=_JOB_ID,
            user_id=_USER_ID,
            workout_id=_WORKOUT_ID,
            job_repo=job_repo,
            prompt_repo=prompt_repo,
            ai_log_repo=ai_log_repo,
            ai_client=ai_client,
            forbidden_phrases=[],
        )
        job = job_repo._jobs[_JOB_ID]
        assert job.status == "failed"
        assert job.error_message == _INSIGHT_FALLBACK

    @pytest.mark.asyncio
    async def test_api_error_writes_ai_log_with_null_response(self) -> None:
        job_repo, prompt_repo, ai_log_repo, ai_client = self._make_repos(
            raise_on_call=RuntimeError("cloud error")
        )
        await process_insight_job(
            job_id=_JOB_ID,
            user_id=_USER_ID,
            workout_id=_WORKOUT_ID,
            job_repo=job_repo,
            prompt_repo=prompt_repo,
            ai_log_repo=ai_log_repo,
            ai_client=ai_client,
            forbidden_phrases=[],
        )
        assert len(ai_log_repo.logs) == 1
        assert ai_log_repo.logs[0].response is None

    @pytest.mark.asyncio
    async def test_forbidden_phrase_sets_failed(self) -> None:
        bad_response = "You can burn fat and lose weight with this workout today."
        job_repo, prompt_repo, ai_log_repo, ai_client = self._make_repos(
            mock_response=bad_response
        )
        await process_insight_job(
            job_id=_JOB_ID,
            user_id=_USER_ID,
            workout_id=_WORKOUT_ID,
            job_repo=job_repo,
            prompt_repo=prompt_repo,
            ai_log_repo=ai_log_repo,
            ai_client=ai_client,
            forbidden_phrases=["burn fat", "lose weight"],
        )
        job = job_repo._jobs[_JOB_ID]
        assert job.status == "failed"
        assert job.error_message == _INSIGHT_FALLBACK

    @pytest.mark.asyncio
    async def test_forbidden_phrase_still_writes_ai_log(self) -> None:
        bad_response = "You can burn fat with this workout today consistently."
        job_repo, prompt_repo, ai_log_repo, ai_client = self._make_repos(
            mock_response=bad_response
        )
        await process_insight_job(
            job_id=_JOB_ID,
            user_id=_USER_ID,
            workout_id=_WORKOUT_ID,
            job_repo=job_repo,
            prompt_repo=prompt_repo,
            ai_log_repo=ai_log_repo,
            ai_client=ai_client,
            forbidden_phrases=["burn fat"],
        )
        assert len(ai_log_repo.logs) == 1
        assert ai_log_repo.logs[0].response == bad_response

    @pytest.mark.asyncio
    async def test_response_too_long_sets_failed(self) -> None:
        long_response = "A" * 281
        job_repo, prompt_repo, ai_log_repo, ai_client = self._make_repos(
            mock_response=long_response
        )
        await process_insight_job(
            job_id=_JOB_ID,
            user_id=_USER_ID,
            workout_id=_WORKOUT_ID,
            job_repo=job_repo,
            prompt_repo=prompt_repo,
            ai_log_repo=ai_log_repo,
            ai_client=ai_client,
            forbidden_phrases=[],
        )
        job = job_repo._jobs[_JOB_ID]
        assert job.status == "failed"
        assert job.error_message == _INSIGHT_FALLBACK

    @pytest.mark.asyncio
    async def test_response_too_short_sets_failed(self) -> None:
        short_response = "Too short"
        job_repo, prompt_repo, ai_log_repo, ai_client = self._make_repos(
            mock_response=short_response
        )
        await process_insight_job(
            job_id=_JOB_ID,
            user_id=_USER_ID,
            workout_id=_WORKOUT_ID,
            job_repo=job_repo,
            prompt_repo=prompt_repo,
            ai_log_repo=ai_log_repo,
            ai_client=ai_client,
            forbidden_phrases=[],
        )
        job = job_repo._jobs[_JOB_ID]
        assert job.status == "failed"

    @pytest.mark.asyncio
    async def test_job_set_processing_before_api_call(self) -> None:
        statuses: list[str] = []

        class TrackingJobRepo(FakeJobRepository):
            async def update(self, job_id: UUID, updates: dict[str, Any]) -> None:
                if updates.get("status") == "processing":
                    statuses.append("processing_seen")
                await super().update(job_id, updates)

        job_repo = TrackingJobRepo()
        _, prompt_repo, ai_log_repo, ai_client = self._make_repos()
        await process_insight_job(
            job_id=_JOB_ID,
            user_id=_USER_ID,
            workout_id=_WORKOUT_ID,
            job_repo=job_repo,
            prompt_repo=prompt_repo,
            ai_log_repo=ai_log_repo,
            ai_client=ai_client,
            forbidden_phrases=[],
        )
        assert "processing_seen" in statuses

    @pytest.mark.asyncio
    async def test_template_format_key_error_sets_failed(self) -> None:
        bad_template = PromptTemplateRecord(
            id=_TEMPLATE_ID,
            feature="insight",
            version="1.0",
            prompt_text="Generate insight for {nonexistent_key}.",
            is_active=True,
            created_at=_NOW,
            deactivated_at=None,
        )
        job_repo = FakeJobRepository()
        prompt_repo = FakePromptTemplateRepository(template=bad_template)
        ai_log_repo = FakeAIRequestLogRepository()
        ai_client = MockAnthropicClient()
        await process_insight_job(
            job_id=_JOB_ID,
            user_id=_USER_ID,
            workout_id=_WORKOUT_ID,
            job_repo=job_repo,
            prompt_repo=prompt_repo,
            ai_log_repo=ai_log_repo,
            ai_client=ai_client,
            forbidden_phrases=[],
        )
        job = job_repo._jobs[_JOB_ID]
        assert job.status == "failed"
        assert job.error_message == _INSIGHT_FALLBACK
