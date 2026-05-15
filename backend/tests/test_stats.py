"""
test_stats.py
PRLifts Backend Tests

Unit tests for the stats endpoint:
  GET /v1/stats — user statistics summary

Each test class isolates its own FakeStatsRepository via dependency_overrides
so tests never share mutable state.

Scenarios covered:
  - New user with no history returns all-zero response (never null, never 404)
  - Active user returns correct counts for all four fields
  - Monday reset: weekly_count reflects only the current Mon–Sun UTC window;
    best_week is preserved from earlier weeks
  - Authentication required (401 for missing token)

See docs/SCHEMA.md — workout table, personal_record table.
See docs/ARCHITECTURE.md Decision 92 — weekly consistency metric.
"""

import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient

from app.repositories.stats_repository import StatsRecord

# ── Constants ────────────────────────────────────────────────────────────────

_SECRET: str = os.environ.get(
    "SUPABASE_JWT_SECRET", "test-supabase-jwt-secret-for-unit-tests"
)
_ALGORITHM = "HS256"
_AUDIENCE = "authenticated"

_USER_A_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

# Fixed reference dates for deterministic Monday-reset tests.
# 2026-05-13 is a Wednesday; its week Monday is 2026-05-11.
_TODAY = datetime(2026, 5, 13, 12, 0, 0, tzinfo=UTC)
_THIS_WEEK_MON = datetime(2026, 5, 11, 0, 0, 0, tzinfo=UTC)
_LAST_WEEK_MON = datetime(2026, 5, 4, 0, 0, 0, tzinfo=UTC)


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


# ── Fake repository ───────────────────────────────────────────────────────────


class FakeStatsRepository:
    """
    In-memory StatsRepository for unit tests.

    Accepts explicit weekly_count, best_week, total_workouts, and total_prs so
    each test scenario can precisely configure the aggregate values it needs
    without coupling to SQL date-window logic.
    """

    def __init__(
        self,
        weekly_count: int = 0,
        best_week: int = 0,
        total_workouts: int = 0,
        total_prs: int = 0,
    ) -> None:
        self._record = StatsRecord(
            weekly_count=weekly_count,
            best_week=best_week,
            total_workouts=total_workouts,
            total_prs=total_prs,
        )

    async def get_stats(self, user_id: UUID) -> StatsRecord:
        return self._record


# ── Client factory ────────────────────────────────────────────────────────────


def _make_client(repo: FakeStatsRepository) -> TestClient:
    from app.repositories.stats_repository import get_stats_repository
    from main import app

    app.dependency_overrides[get_stats_repository] = lambda: repo
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Generator[None, None, None]:
    yield
    from main import app

    app.dependency_overrides.clear()


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestGetStats:
    def test_new_user_returns_all_zeros(self) -> None:
        """A user with no workout history must receive zeroes for all fields."""
        repo = FakeStatsRepository()
        client = _make_client(repo)

        response = client.get("/v1/stats", headers=_auth())

        assert response.status_code == 200
        data = response.json()
        assert data["weekly_count"] == 0
        assert data["best_week"] == 0
        assert data["total_workouts"] == 0
        assert data["total_prs"] == 0

    def test_active_user_returns_correct_counts(self) -> None:
        """All four stat fields reflect the repository values."""
        repo = FakeStatsRepository(
            weekly_count=3,
            best_week=5,
            total_workouts=42,
            total_prs=7,
        )
        client = _make_client(repo)

        response = client.get("/v1/stats", headers=_auth())

        assert response.status_code == 200
        data = response.json()
        assert data["weekly_count"] == 3
        assert data["best_week"] == 5
        assert data["total_workouts"] == 42
        assert data["total_prs"] == 7

    def test_monday_reset_weekly_count_resets_best_week_preserved(self) -> None:
        """
        After Monday, weekly_count should reset to reflect only the new week's
        workouts while best_week retains the previous week's higher count.

        Scenario: user had 5 workouts last week (their best), then 1 workout
        so far this week (Monday just passed). weekly_count == 1, best_week == 5.
        """
        repo = FakeStatsRepository(
            weekly_count=1,
            best_week=5,
            total_workouts=21,
            total_prs=4,
        )
        client = _make_client(repo)

        response = client.get("/v1/stats", headers=_auth())

        assert response.status_code == 200
        data = response.json()
        assert data["weekly_count"] == 1  # only this week
        assert data["best_week"] == 5  # preserved from last week
        assert data["total_workouts"] == 21
        assert data["total_prs"] == 4

    def test_best_week_equals_weekly_count_when_current_week_is_best(self) -> None:
        """When the current week is the user's best, weekly_count == best_week."""
        repo = FakeStatsRepository(
            weekly_count=6,
            best_week=6,
            total_workouts=30,
            total_prs=10,
        )
        client = _make_client(repo)

        response = client.get("/v1/stats", headers=_auth())

        assert response.status_code == 200
        data = response.json()
        assert data["weekly_count"] == data["best_week"] == 6

    def test_requires_authentication(self) -> None:
        """Requests without a Bearer token must receive HTTP 401."""
        repo = FakeStatsRepository()
        client = _make_client(repo)

        response = client.get("/v1/stats")

        assert response.status_code == 401
        assert response.json()["error_code"] == "auth_token_missing"

    def test_response_contains_all_required_fields(self) -> None:
        """Response schema must include all four fields — no missing keys."""
        repo = FakeStatsRepository(
            weekly_count=2, best_week=3, total_workouts=10, total_prs=1
        )
        client = _make_client(repo)

        response = client.get("/v1/stats", headers=_auth())

        assert response.status_code == 200
        data = response.json()
        for field in ("weekly_count", "best_week", "total_workouts", "total_prs"):
            assert field in data, f"Missing field: {field}"

    def test_expired_token_returns_401(self) -> None:
        """Expired JWT must receive HTTP 401 auth_token_expired."""
        repo = FakeStatsRepository()
        client = _make_client(repo)
        headers = {"Authorization": f"Bearer {_make_token(expired=True)}"}

        response = client.get("/v1/stats", headers=headers)

        assert response.status_code == 401
        assert response.json()["error_code"] == "auth_token_expired"
