"""
job_repository.py
PRLifts Backend

Repository protocols for the job, prompt_template, and ai_request_log tables.
All three are managed together because they form the AI async job pipeline:
a Job is created, a PromptTemplate is fetched to drive it, and an AIRequestLog
is written when it completes.

See docs/SCHEMA.md — job, prompt_template, ai_request_log tables.
See docs/JOB_CATALOG.md — JOB-001 cleanup_expired_jobs.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


@dataclass
class JobRecord:
    """Mirrors one row from the job table."""

    id: UUID
    user_id: UUID
    job_type: str
    status: str
    result: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    expires_at: datetime


@dataclass
class PromptTemplateRecord:
    """Mirrors one row from the prompt_template table."""

    id: UUID
    feature: str
    version: str
    prompt_text: str
    is_active: bool
    created_at: datetime
    deactivated_at: datetime | None


@dataclass
class AIRequestLogRecord:
    """Mirrors one row from the ai_request_log table."""

    id: UUID
    user_id: UUID
    prompt_template_id: UUID | None
    job_id: UUID | None
    endpoint: str
    response: str | None
    model: str
    quality_score: float | None
    duration_ms: int
    created_at: datetime
    expires_at: datetime


class JobRepository(Protocol):
    """Abstract persistence interface for the job table."""

    async def create(self, user_id: UUID, job_type: str) -> JobRecord: ...

    async def get_by_id(self, job_id: UUID) -> JobRecord | None: ...

    async def update(self, job_id: UUID, updates: dict[str, Any]) -> None: ...

    async def expire_stale(self, now: datetime) -> int:
        """
        Sets pending/processing jobs past their expires_at to 'expired'.

        Returns the number of rows updated. See docs/JOB_CATALOG.md JOB-001.
        """
        ...


class PromptTemplateRepository(Protocol):
    """Abstract persistence interface for the prompt_template table."""

    async def get_active(self, feature: str) -> PromptTemplateRecord | None: ...


class AIRequestLogRepository(Protocol):
    """Abstract persistence interface for the ai_request_log table."""

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
    ) -> AIRequestLogRecord: ...


async def get_job_repository() -> JobRepository:
    """
    FastAPI dependency marker for JobRepository.

    Override in tests:
        app.dependency_overrides[get_job_repository] = lambda: FakeJobRepository()

    Raises:
        RuntimeError: Always — must be overridden before any request is served.
    """
    raise RuntimeError(
        "get_job_repository has no default implementation. "
        "Wire a real implementation in main.py or override in tests."
    )


async def get_prompt_template_repository() -> PromptTemplateRepository:
    """
    FastAPI dependency marker for PromptTemplateRepository.

    Raises:
        RuntimeError: Always — must be overridden before any request is served.
    """
    raise RuntimeError(
        "get_prompt_template_repository has no default implementation. "
        "Wire a real implementation in main.py or override in tests."
    )


async def get_ai_request_log_repository() -> AIRequestLogRepository:
    """
    FastAPI dependency marker for AIRequestLogRepository.

    Raises:
        RuntimeError: Always — must be overridden before any request is served.
    """
    raise RuntimeError(
        "get_ai_request_log_repository has no default implementation. "
        "Wire a real implementation in main.py or override in tests."
    )
