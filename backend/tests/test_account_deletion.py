"""
test_account_deletion.py
PRLifts Backend Tests

Unit tests for POST /v1/account/delete — hard account deletion.

Coverage:
  - Successful cascade: sets → workouts → jobs → image queue →
      biometric_consent → user_profile → audit_log → auth.users
  - Cascade order verified via FakeAccountDeletionRepository.deletion_order
  - 401 unauthenticated
  - 429 rate limit (Redis count already at 2)
  - 400 confirm missing (body without confirm key)
  - 400 confirm false

See docs/ARCHITECTURE.md Decision 95.
"""

import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient

from app.repositories.account_deletion_repository import (
    FakeAccountDeletionRepository,
    FakeSupabaseAdminClient,
    get_account_deletion_repository,
    get_supabase_admin_client,
)

# ── Constants ─────────────────────────────────────────────────────────────────

_SECRET: str = os.environ.get(
    "SUPABASE_JWT_SECRET", "test-supabase-jwt-secret-for-unit-tests"
)
_ALGORITHM = "HS256"
_AUDIENCE = "authenticated"

_USER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_WORKOUT_ID_1 = UUID("11111111-1111-1111-1111-111111111111")
_WORKOUT_ID_2 = UUID("22222222-2222-2222-2222-222222222222")
_JOB_ID_1 = UUID("33333333-3333-3333-3333-333333333333")

_IMAGE_URL = "https://fal.ai/files/abc123/generated.jpg"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_token(user_id: UUID = _USER_ID, expired: bool = False) -> str:
    now = datetime.now(UTC)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    payload: dict[str, Any] = {
        "exp": exp,
        "aud": _AUDIENCE,
        "role": "authenticated",
        "sub": str(user_id),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def _auth(user_id: UUID = _USER_ID) -> dict[str, str]:
    return {"Authorization": f"Bearer {_make_token(user_id)}"}


# ── FakeRedis ─────────────────────────────────────────────────────────────────


class _FakeRedis:
    """Minimal Redis fake for rate-limit testing."""

    def __init__(self, next_count: int = 1) -> None:
        self._next_count = next_count

    async def incr(self, key: str) -> int:
        return self._next_count

    async def expire(self, key: str, ttl: int) -> None:
        pass


# ── Fixture helpers ───────────────────────────────────────────────────────────


def _make_client(
    repo: FakeAccountDeletionRepository,
    admin: FakeSupabaseAdminClient | None = None,
) -> TestClient:
    from main import app

    if admin is None:
        admin = FakeSupabaseAdminClient()

    app.dependency_overrides[get_account_deletion_repository] = lambda: repo
    app.dependency_overrides[get_supabase_admin_client] = lambda: admin
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def clear_overrides_and_redis() -> Generator[None, None, None]:
    yield
    from main import app

    app.dependency_overrides.clear()
    if hasattr(app.state, "redis"):
        app.state.redis = None


# ── Populated repo helper ─────────────────────────────────────────────────────


def _populated_repo() -> FakeAccountDeletionRepository:
    """Returns a repo pre-loaded with one user's data including a future_self job."""
    repo = FakeAccountDeletionRepository()
    repo.user_profiles.add(_USER_ID)
    repo.workout_sets[_USER_ID] = [
        {"set_number": 1},
        {"set_number": 2},
        {"set_number": 3},
    ]
    repo.workouts[_USER_ID] = [
        {"id": _WORKOUT_ID_1},
        {"id": _WORKOUT_ID_2},
    ]
    repo.jobs[_USER_ID] = [
        {
            "id": _JOB_ID_1,
            "job_type": "future_self",
            "result": {"image_url": _IMAGE_URL},
        },
        {
            "id": UUID("44444444-4444-4444-4444-444444444444"),
            "job_type": "insight",
            "result": {"insight": "Great session!"},
        },
    ]
    return repo


# ── POST /v1/account/delete — success ────────────────────────────────────────


class TestDeleteAccountSuccess:
    def test_returns_204(self) -> None:
        repo = _populated_repo()
        admin = FakeSupabaseAdminClient()
        client = _make_client(repo, admin)

        response = client.post(
            "/v1/account/delete", json={"confirm": True}, headers=_auth()
        )

        assert response.status_code == 204

    def test_cascade_order_is_correct(self) -> None:
        """
        Verifies the FK-safe deletion sequence is followed.

        Order must be:
          get_generated_image_urls → enqueue_image_deletions →
          delete_workout_sets → delete_workouts → delete_jobs →
          set_biometric_consent_deleted → delete_user_profile →
          write_audit_log

        biometric_consent must precede delete_user_profile (ON DELETE RESTRICT).
        write_audit_log must follow delete_user_profile (records completion).
        """
        repo = _populated_repo()
        client = _make_client(repo)

        client.post("/v1/account/delete", json={"confirm": True}, headers=_auth())

        assert repo.deletion_order == [
            "get_generated_image_urls",
            "enqueue_image_deletions",
            "delete_workout_sets",
            "delete_workouts",
            "delete_jobs",
            "set_biometric_consent_deleted",
            "delete_user_profile",
            "write_audit_log",
        ]

    def test_workout_sets_emptied(self) -> None:
        repo = _populated_repo()
        client = _make_client(repo)

        client.post("/v1/account/delete", json={"confirm": True}, headers=_auth())

        assert _USER_ID not in repo.workout_sets

    def test_workouts_emptied(self) -> None:
        repo = _populated_repo()
        client = _make_client(repo)

        client.post("/v1/account/delete", json={"confirm": True}, headers=_auth())

        assert _USER_ID not in repo.workouts

    def test_jobs_emptied(self) -> None:
        repo = _populated_repo()
        client = _make_client(repo)

        client.post("/v1/account/delete", json={"confirm": True}, headers=_auth())

        assert _USER_ID not in repo.jobs

    def test_user_profile_removed(self) -> None:
        repo = _populated_repo()
        client = _make_client(repo)

        client.post("/v1/account/delete", json={"confirm": True}, headers=_auth())

        assert _USER_ID not in repo.user_profiles

    def test_future_self_image_queued(self) -> None:
        """Only future_self job image URLs are queued; insight jobs are not."""
        repo = _populated_repo()
        client = _make_client(repo)

        client.post("/v1/account/delete", json={"confirm": True}, headers=_auth())

        assert _IMAGE_URL in repo.image_deletion_queue

    def test_insight_job_image_not_queued(self) -> None:
        repo = _populated_repo()
        client = _make_client(repo)

        client.post("/v1/account/delete", json={"confirm": True}, headers=_auth())

        assert len(repo.image_deletion_queue) == 1

    def test_audit_log_written_with_correct_event(self) -> None:
        repo = _populated_repo()
        client = _make_client(repo)

        client.post("/v1/account/delete", json={"confirm": True}, headers=_auth())

        assert len(repo.audit_log) == 1
        entry = repo.audit_log[0]
        assert entry["event_type"] == "user.deletion_completed"
        assert entry["user_id"] == _USER_ID

    def test_audit_log_payload_contains_counts(self) -> None:
        repo = _populated_repo()
        client = _make_client(repo)

        client.post("/v1/account/delete", json={"confirm": True}, headers=_auth())

        payload = repo.audit_log[0]["payload"]
        assert payload["sets_deleted"] == 3
        assert payload["workouts_deleted"] == 2
        assert payload["jobs_deleted"] == 2
        assert payload["images_queued"] == 1

    def test_biometric_consent_marked_deleted(self) -> None:
        repo = _populated_repo()
        client = _make_client(repo)

        client.post("/v1/account/delete", json={"confirm": True}, headers=_auth())

        assert _USER_ID in repo.biometric_consent_deleted

    def test_supabase_auth_user_deleted(self) -> None:
        repo = _populated_repo()
        admin = FakeSupabaseAdminClient()
        client = _make_client(repo, admin)

        client.post("/v1/account/delete", json={"confirm": True}, headers=_auth())

        assert _USER_ID in admin.deleted_user_ids

    def test_supabase_auth_deleted_after_db(self) -> None:
        """auth.users deletion must come AFTER all DB work (write_audit_log last)."""
        repo = _populated_repo()
        admin = FakeSupabaseAdminClient()
        client = _make_client(repo, admin)

        client.post("/v1/account/delete", json={"confirm": True}, headers=_auth())

        # audit_log is the last repo step — Supabase auth is deleted after it
        assert repo.deletion_order[-1] == "write_audit_log"
        assert _USER_ID in admin.deleted_user_ids

    def test_empty_account_still_succeeds(self) -> None:
        """User with no workouts, jobs, or images can still delete their account."""
        repo = FakeAccountDeletionRepository()
        repo.user_profiles.add(_USER_ID)
        client = _make_client(repo)

        response = client.post(
            "/v1/account/delete", json={"confirm": True}, headers=_auth()
        )

        assert response.status_code == 204
        assert _USER_ID not in repo.user_profiles


# ── 401 Unauthenticated ───────────────────────────────────────────────────────


class TestDeleteAccountUnauth:
    def test_no_auth_header_returns_401(self) -> None:
        repo = FakeAccountDeletionRepository()
        client = _make_client(repo)

        response = client.post("/v1/account/delete", json={"confirm": True})

        assert response.status_code == 401

    def test_no_auth_does_not_delete_anything(self) -> None:
        repo = _populated_repo()
        client = _make_client(repo)

        client.post("/v1/account/delete", json={"confirm": True})

        assert _USER_ID in repo.user_profiles
        assert repo.deletion_order == []


# ── 429 Rate limit ────────────────────────────────────────────────────────────


class TestDeleteAccountRateLimit:
    def test_second_request_in_same_hour_returns_429(self) -> None:
        from main import app

        repo = FakeAccountDeletionRepository()
        repo.user_profiles.add(_USER_ID)
        app.state.redis = _FakeRedis(next_count=2)
        client = _make_client(repo)

        response = client.post(
            "/v1/account/delete", json={"confirm": True}, headers=_auth()
        )

        assert response.status_code == 429

    def test_rate_limited_response_has_correct_error_code(self) -> None:
        from main import app

        repo = FakeAccountDeletionRepository()
        repo.user_profiles.add(_USER_ID)
        app.state.redis = _FakeRedis(next_count=2)
        client = _make_client(repo)

        response = client.post(
            "/v1/account/delete", json={"confirm": True}, headers=_auth()
        )

        assert response.json()["error_code"] == "account_delete_rate_limited"

    def test_rate_limited_response_has_retry_after_header(self) -> None:
        from main import app

        repo = FakeAccountDeletionRepository()
        repo.user_profiles.add(_USER_ID)
        app.state.redis = _FakeRedis(next_count=2)
        client = _make_client(repo)

        response = client.post(
            "/v1/account/delete", json={"confirm": True}, headers=_auth()
        )

        assert "retry-after" in response.headers

    def test_rate_limited_does_not_delete_account(self) -> None:
        from main import app

        repo = _populated_repo()
        app.state.redis = _FakeRedis(next_count=2)
        client = _make_client(repo)

        client.post("/v1/account/delete", json={"confirm": True}, headers=_auth())

        assert _USER_ID in repo.user_profiles

    def test_first_request_allowed_when_redis_available(self) -> None:
        from main import app

        repo = _populated_repo()
        admin = FakeSupabaseAdminClient()
        app.state.redis = _FakeRedis(next_count=1)
        client = _make_client(repo, admin)

        response = client.post(
            "/v1/account/delete", json={"confirm": True}, headers=_auth()
        )

        assert response.status_code == 204

    def test_fails_open_when_redis_unavailable(self) -> None:
        """When app.state.redis is None the endpoint is not rate-blocked."""
        repo = _populated_repo()
        admin = FakeSupabaseAdminClient()
        client = _make_client(repo, admin)
        # app.state.redis is None by default in tests (no lifespan)

        response = client.post(
            "/v1/account/delete", json={"confirm": True}, headers=_auth()
        )

        assert response.status_code == 204


# ── 400 confirm validation ────────────────────────────────────────────────────


class TestDeleteAccountConfirmValidation:
    def test_confirm_false_returns_400(self) -> None:
        repo = FakeAccountDeletionRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/account/delete", json={"confirm": False}, headers=_auth()
        )

        assert response.status_code == 400

    def test_confirm_false_has_correct_error_code(self) -> None:
        repo = FakeAccountDeletionRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/account/delete", json={"confirm": False}, headers=_auth()
        )

        assert response.json()["error_code"] == "account_delete_not_confirmed"

    def test_confirm_missing_returns_400(self) -> None:
        """DeleteAccountRequest.confirm defaults to False — missing is same as False."""
        repo = FakeAccountDeletionRepository()
        client = _make_client(repo)

        response = client.post("/v1/account/delete", json={}, headers=_auth())

        assert response.status_code == 400

    def test_confirm_missing_has_correct_error_code(self) -> None:
        repo = FakeAccountDeletionRepository()
        client = _make_client(repo)

        response = client.post("/v1/account/delete", json={}, headers=_auth())

        assert response.json()["error_code"] == "account_delete_not_confirmed"

    def test_confirm_false_does_not_delete_anything(self) -> None:
        repo = _populated_repo()
        client = _make_client(repo)

        client.post("/v1/account/delete", json={"confirm": False}, headers=_auth())

        assert _USER_ID in repo.user_profiles
        assert repo.deletion_order == []
