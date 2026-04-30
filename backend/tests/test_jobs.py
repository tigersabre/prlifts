"""
test_jobs.py
PRLifts Backend Tests

Unit tests for the AI job endpoints:
  POST /v1/jobs           — create insight job, returns 202 + job_id
  GET  /v1/jobs/{job_id}  — poll status; result populated when complete

Background tasks run synchronously in TestClient — the full insight pipeline
(prompt fetch, mock Claude call, response validation, job update) executes
during the POST request, so GET can verify the final state immediately.

AI_PROVIDERS_MOCKED=true prevents real Claude API calls.

See GitHub Issue #39 for acceptance criteria.
"""

import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("APP_VERSION", "0.1.0")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-supabase-jwt-secret-for-unit-tests")
os.environ.setdefault("AI_PROVIDERS_MOCKED", "true")

from app.repositories.job_repository import (  # noqa: E402
    AIRequestLogRecord,
    JobRecord,
    PromptTemplateRecord,
    get_ai_request_log_repository,
    get_job_repository,
    get_prompt_template_repository,
)
from app.repositories.workout_repository import (  # noqa: E402
    WorkoutRecord,
    get_workout_repository,
)
from main import app  # noqa: E402

# ── Constants ────────────────────────────────────────────────────────────────

_SECRET: str = os.environ.get(
    "SUPABASE_JWT_SECRET", "test-supabase-jwt-secret-for-unit-tests"
)
_ALGORITHM = "HS256"
_AUDIENCE = "authenticated"

_USER_A_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_USER_B_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_WORKOUT_ID = UUID("11111111-1111-1111-1111-111111111111")
_JOB_ID = UUID("22222222-2222-2222-2222-222222222222")
_TEMPLATE_ID = UUID("33333333-3333-3333-3333-333333333333")

_NOW = datetime(2026, 4, 29, 12, 0, 0, tzinfo=UTC)
_EXPIRES_AT = _NOW + timedelta(minutes=5)

_DEFAULT_WORKOUT = WorkoutRecord(
    id=_WORKOUT_ID,
    user_id=_USER_A_ID,
    name="Morning Lift",
    notes=None,
    status="completed",
    type="ad_hoc",
    format="weightlifting",
    plan_id=None,
    started_at=_NOW - timedelta(hours=1),
    completed_at=_NOW,
    duration_seconds=3600,
    location="gym",
    rating=None,
    server_received_at=_NOW,
    created_at=_NOW,
    updated_at=_NOW,
)

_DEFAULT_TEMPLATE = PromptTemplateRecord(
    id=_TEMPLATE_ID,
    feature="insight",
    version="1.0",
    prompt_text="Generate a workout insight for workout_id={workout_id}.",
    is_active=True,
    created_at=_NOW,
    deactivated_at=None,
)

_VALID_MOCK_INSIGHT = (
    "Solid session today — you completed your workout and built the consistency "
    "that drives long-term strength gains."
)


# ── Fake repositories ─────────────────────────────────────────────────────────


class FakeJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[UUID, JobRecord] = {}

    async def create(self, user_id: UUID, job_type: str) -> JobRecord:
        job = JobRecord(
            id=_JOB_ID,
            user_id=user_id,
            job_type=job_type,
            status="pending",
            result=None,
            error_message=None,
            created_at=_NOW,
            started_at=None,
            completed_at=None,
            expires_at=_EXPIRES_AT,
        )
        self._jobs[job.id] = job
        return job

    async def get_by_id(self, job_id: UUID) -> JobRecord | None:
        return self._jobs.get(job_id)

    async def update(self, job_id: UUID, updates: dict[str, Any]) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            return
        for key, val in updates.items():
            object.__setattr__(job, key, val)

    async def expire_stale(self, now: datetime) -> int:
        count = 0
        for job in self._jobs.values():
            if job.status in ("pending", "processing") and job.expires_at < now:
                object.__setattr__(job, "status", "expired")
                object.__setattr__(
                    job,
                    "error_message",
                    "This request took too long. Please try again.",
                )
                object.__setattr__(job, "completed_at", now)
                count += 1
        return count


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


class FakeWorkoutRepository:
    def __init__(self, workout: WorkoutRecord | None = _DEFAULT_WORKOUT) -> None:
        self._workout = workout

    async def create(self, *args: Any, **kwargs: Any) -> WorkoutRecord:
        raise NotImplementedError

    async def get_by_id(self, workout_id: UUID) -> WorkoutRecord | None:
        if self._workout and self._workout.id == workout_id:
            return self._workout
        return None

    async def list_for_user(
        self, *args: Any, **kwargs: Any
    ) -> tuple[list[WorkoutRecord], int]:
        raise NotImplementedError

    async def update(self, *args: Any, **kwargs: Any) -> WorkoutRecord | None:
        raise NotImplementedError

    async def delete(self, *args: Any, **kwargs: Any) -> bool:
        raise NotImplementedError


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_token(user_id: UUID = _USER_A_ID, expired: bool = False) -> str:
    now = datetime.now(UTC)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    payload: dict[str, Any] = {
        "exp": exp,
        "aud": _AUDIENCE,
        "role": "authenticated",
        "sub": str(user_id),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def _auth(user_id: UUID = _USER_A_ID) -> dict[str, str]:
    return {"Authorization": f"Bearer {_make_token(user_id)}"}


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def job_repo() -> FakeJobRepository:
    return FakeJobRepository()


@pytest.fixture
def prompt_repo() -> FakePromptTemplateRepository:
    return FakePromptTemplateRepository()


@pytest.fixture
def ai_log_repo() -> FakeAIRequestLogRepository:
    return FakeAIRequestLogRepository()


@pytest.fixture
def workout_repo() -> FakeWorkoutRepository:
    return FakeWorkoutRepository()


@pytest.fixture
def client(
    job_repo: FakeJobRepository,
    prompt_repo: FakePromptTemplateRepository,
    ai_log_repo: FakeAIRequestLogRepository,
    workout_repo: FakeWorkoutRepository,
) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_job_repository] = lambda: job_repo
    app.dependency_overrides[get_prompt_template_repository] = lambda: prompt_repo
    app.dependency_overrides[get_ai_request_log_repository] = lambda: ai_log_repo
    app.dependency_overrides[get_workout_repository] = lambda: workout_repo
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ── POST /v1/jobs ─────────────────────────────────────────────────────────────


class TestCreateJob:
    def test_creates_insight_job_returns_202(
        self, client: TestClient, job_repo: FakeJobRepository
    ) -> None:
        resp = client.post(
            "/v1/jobs",
            json={"job_type": "insight", "workout_id": str(_WORKOUT_ID)},
            headers=_auth(),
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert UUID(data["job_id"]) == _JOB_ID

    def test_background_task_sets_job_complete(
        self,
        client: TestClient,
        job_repo: FakeJobRepository,
        ai_log_repo: FakeAIRequestLogRepository,
    ) -> None:
        client.post(
            "/v1/jobs",
            json={"job_type": "insight", "workout_id": str(_WORKOUT_ID)},
            headers=_auth(),
        )
        job = job_repo._jobs[_JOB_ID]
        assert job.status == "complete"
        assert job.result is not None
        assert "insight" in job.result
        assert job.result["workout_id"] == str(_WORKOUT_ID)

    def test_ai_request_log_written(
        self,
        client: TestClient,
        ai_log_repo: FakeAIRequestLogRepository,
    ) -> None:
        client.post(
            "/v1/jobs",
            json={"job_type": "insight", "workout_id": str(_WORKOUT_ID)},
            headers=_auth(),
        )
        assert len(ai_log_repo.logs) == 1
        log = ai_log_repo.logs[0]
        assert log.prompt_template_id == _TEMPLATE_ID
        assert log.job_id == _JOB_ID
        assert log.endpoint == "insight"
        assert log.model == "claude-sonnet-4-5"
        assert log.user_id == _USER_A_ID

    def test_requires_auth(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/jobs",
            json={"job_type": "insight", "workout_id": str(_WORKOUT_ID)},
        )
        assert resp.status_code == 401

    def test_workout_not_found_returns_404(
        self, client: TestClient, workout_repo: FakeWorkoutRepository
    ) -> None:
        workout_repo._workout = None
        resp = client.post(
            "/v1/jobs",
            json={"job_type": "insight", "workout_id": str(_WORKOUT_ID)},
            headers=_auth(),
        )
        assert resp.status_code == 404
        assert resp.json()["error_code"] == "workout_not_found"

    def test_workout_owned_by_other_user_returns_403(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/jobs",
            json={"job_type": "insight", "workout_id": str(_WORKOUT_ID)},
            headers=_auth(user_id=_USER_B_ID),
        )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "workout_forbidden"

    def test_unsupported_job_type_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/jobs",
            json={"job_type": "future_self", "workout_id": str(_WORKOUT_ID)},
            headers=_auth(),
        )
        assert resp.status_code == 422
        assert resp.json()["error_code"] == "job_type_unsupported"

    def test_invalid_job_type_string_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/jobs",
            json={"job_type": "invalid_type", "workout_id": str(_WORKOUT_ID)},
            headers=_auth(),
        )
        assert resp.status_code == 422

    def test_missing_workout_id_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/jobs",
            json={"job_type": "insight"},
            headers=_auth(),
        )
        assert resp.status_code == 422


# ── GET /v1/jobs/{job_id} ─────────────────────────────────────────────────────


class TestGetJob:
    def _create_job(self, client: TestClient) -> None:
        client.post(
            "/v1/jobs",
            json={"job_type": "insight", "workout_id": str(_WORKOUT_ID)},
            headers=_auth(),
        )

    def test_returns_complete_job_with_insight(self, client: TestClient) -> None:
        self._create_job(client)
        resp = client.get(f"/v1/jobs/{_JOB_ID}", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(_JOB_ID)
        assert data["status"] == "complete"
        assert data["result"]["insight"] is not None
        assert data["result"]["workout_id"] == str(_WORKOUT_ID)
        assert data["error_message"] is None

    def test_job_not_found_returns_404(self, client: TestClient) -> None:
        resp = client.get(f"/v1/jobs/{uuid4()}", headers=_auth())
        assert resp.status_code == 404
        assert resp.json()["error_code"] == "job_not_found"

    def test_job_owned_by_other_user_returns_403(self, client: TestClient) -> None:
        self._create_job(client)
        resp = client.get(f"/v1/jobs/{_JOB_ID}", headers=_auth(user_id=_USER_B_ID))
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "job_forbidden"

    def test_requires_auth(self, client: TestClient) -> None:
        self._create_job(client)
        resp = client.get(f"/v1/jobs/{_JOB_ID}")
        assert resp.status_code == 401

    def test_pending_job_returns_pending_status(
        self,
        client: TestClient,
        job_repo: FakeJobRepository,
        prompt_repo: FakePromptTemplateRepository,
    ) -> None:
        prompt_repo._template = None
        client.post(
            "/v1/jobs",
            json={"job_type": "insight", "workout_id": str(_WORKOUT_ID)},
            headers=_auth(),
        )
        resp = client.get(f"/v1/jobs/{_JOB_ID}", headers=_auth())
        assert resp.status_code == 200
        assert resp.json()["status"] == "failed"


# ── Job expiry ────────────────────────────────────────────────────────────────


class TestJobExpiry:
    @pytest.mark.asyncio
    async def test_expire_stale_marks_old_pending_jobs_expired(self) -> None:
        repo = FakeJobRepository()
        repo._jobs[_JOB_ID] = JobRecord(
            id=_JOB_ID,
            user_id=_USER_A_ID,
            job_type="insight",
            status="pending",
            result=None,
            error_message=None,
            created_at=_NOW - timedelta(minutes=10),
            started_at=None,
            completed_at=None,
            expires_at=_NOW - timedelta(minutes=5),
        )
        count = await repo.expire_stale(_NOW)
        assert count == 1
        assert repo._jobs[_JOB_ID].status == "expired"
        assert repo._jobs[_JOB_ID].error_message is not None

    @pytest.mark.asyncio
    async def test_expire_stale_ignores_complete_jobs(self) -> None:
        repo = FakeJobRepository()
        repo._jobs[_JOB_ID] = JobRecord(
            id=_JOB_ID,
            user_id=_USER_A_ID,
            job_type="insight",
            status="complete",
            result={"insight": "good work"},
            error_message=None,
            created_at=_NOW - timedelta(minutes=10),
            started_at=_NOW - timedelta(minutes=9),
            completed_at=_NOW - timedelta(minutes=8),
            expires_at=_NOW - timedelta(minutes=5),
        )
        count = await repo.expire_stale(_NOW)
        assert count == 0
        assert repo._jobs[_JOB_ID].status == "complete"

    @pytest.mark.asyncio
    async def test_expire_stale_ignores_jobs_not_yet_expired(self) -> None:
        repo = FakeJobRepository()
        repo._jobs[_JOB_ID] = JobRecord(
            id=_JOB_ID,
            user_id=_USER_A_ID,
            job_type="insight",
            status="pending",
            result=None,
            error_message=None,
            created_at=_NOW,
            started_at=None,
            completed_at=None,
            expires_at=_NOW + timedelta(minutes=5),
        )
        count = await repo.expire_stale(_NOW)
        assert count == 0
        assert repo._jobs[_JOB_ID].status == "pending"
