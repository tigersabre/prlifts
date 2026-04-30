"""
test_workouts.py
PRLifts Backend Tests

Unit tests for the workout CRUD endpoints:
  POST   /v1/workouts              — create workout
  GET    /v1/workouts              — list user workouts
  GET    /v1/workouts/{id}         — get single workout
  PATCH  /v1/workouts/{id}         — partial update
  DELETE /v1/workouts/{id}         — delete with cascade

Each test class isolates its own FakeWorkoutRepository via dependency_overrides
so tests never share mutable state.

See docs/SCHEMA.md — workout table.
See GitHub Issue #36 for acceptance criteria.
"""

import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.repositories.workout_repository import WorkoutRecord

# ── Constants ────────────────────────────────────────────────────────────────

_SECRET: str = os.environ.get(
    "SUPABASE_JWT_SECRET", "test-supabase-jwt-secret-for-unit-tests"
)
_ALGORITHM = "HS256"
_AUDIENCE = "authenticated"

_USER_A_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_USER_B_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_WORKOUT_ID = UUID("11111111-1111-1111-1111-111111111111")

_NOW = datetime(2026, 4, 29, 12, 0, 0, tzinfo=UTC)
_STARTED_AT = datetime(2026, 4, 29, 10, 0, 0, tzinfo=UTC)

_DEFAULT_RECORD = WorkoutRecord(
    id=_WORKOUT_ID,
    user_id=_USER_A_ID,
    name="Morning Lift",
    notes=None,
    status="in_progress",
    type="ad_hoc",
    format="weightlifting",
    plan_id=None,
    started_at=_STARTED_AT,
    completed_at=None,
    duration_seconds=None,
    location="gym",
    rating=None,
    server_received_at=_NOW,
    created_at=_NOW,
    updated_at=_NOW,
)


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


class FakeWorkoutRepository:
    """
    In-memory WorkoutRepository for unit tests.

    Stores records keyed by workout_id. Each test class creates a fresh
    instance via dependency_overrides so state never leaks between tests.
    """

    def __init__(self, initial: WorkoutRecord | None = None) -> None:
        self._store: dict[UUID, WorkoutRecord] = {}
        if initial is not None:
            self._store[initial.id] = initial

    async def create(
        self,
        user_id: UUID,
        workout_type: str,
        workout_format: str,
        name: str | None,
        location: str | None,
        plan_id: UUID | None,
        client_started_at: datetime | None,
    ) -> WorkoutRecord:
        now = datetime.now(UTC)
        record = WorkoutRecord(
            id=uuid4(),
            user_id=user_id,
            name=name,
            notes=None,
            status="in_progress",
            type=workout_type,
            format=workout_format,
            plan_id=plan_id,
            started_at=client_started_at if client_started_at is not None else now,
            completed_at=None,
            duration_seconds=None,
            location=location,
            rating=None,
            server_received_at=now,
            created_at=now,
            updated_at=now,
        )
        self._store[record.id] = record
        return record

    async def get_by_id(self, workout_id: UUID) -> WorkoutRecord | None:
        return self._store.get(workout_id)

    async def list_for_user(
        self,
        user_id: UUID,
        page: int,
        per_page: int,
        format_filter: str | None,
        status_filter: str | None,
    ) -> tuple[list[WorkoutRecord], int]:
        records = [r for r in self._store.values() if r.user_id == user_id]
        if format_filter is not None:
            records = [r for r in records if r.format == format_filter]
        if status_filter is not None:
            records = [r for r in records if r.status == status_filter]
        records.sort(key=lambda r: r.started_at, reverse=True)
        total = len(records)
        start = (page - 1) * per_page
        return records[start : start + per_page], total

    async def update(
        self,
        workout_id: UUID,
        updates: dict[str, object],
    ) -> WorkoutRecord | None:
        record = self._store.get(workout_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        updated = WorkoutRecord(
            id=record.id,
            user_id=record.user_id,
            name=updates.get("name", record.name),  # type: ignore[arg-type]
            notes=updates.get("notes", record.notes),  # type: ignore[arg-type]
            status=str(updates.get("status", record.status)),
            type=record.type,
            format=record.format,
            plan_id=record.plan_id,
            started_at=record.started_at,
            completed_at=updates.get("completed_at", record.completed_at),  # type: ignore[arg-type]
            duration_seconds=updates.get("duration_seconds", record.duration_seconds),  # type: ignore[arg-type]
            location=record.location,
            rating=updates.get("rating", record.rating),  # type: ignore[arg-type]
            server_received_at=record.server_received_at,
            created_at=record.created_at,
            updated_at=now,
        )
        self._store[workout_id] = updated
        return updated

    async def delete(self, workout_id: UUID) -> bool:
        if workout_id not in self._store:
            return False
        del self._store[workout_id]
        return True


# ── Fixture helpers ───────────────────────────────────────────────────────────


def _make_client(repo: FakeWorkoutRepository) -> TestClient:
    """Returns a TestClient with the given repo wired as the dependency."""
    from app.repositories.workout_repository import get_workout_repository
    from main import app

    app.dependency_overrides[get_workout_repository] = lambda: repo
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Generator[None, None, None]:
    yield
    from main import app

    app.dependency_overrides.clear()


# ── POST /v1/workouts ─────────────────────────────────────────────────────────


class TestCreateWorkout:
    def test_creates_workout_and_returns_201(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/workouts",
            json={"type": "ad_hoc", "format": "weightlifting"},
            headers=_auth(),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "ad_hoc"
        assert data["format"] == "weightlifting"
        assert "id" in data
        assert "created_at" in data

    def test_status_is_in_progress(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/workouts",
            json={"type": "ad_hoc", "format": "weightlifting"},
            headers=_auth(),
        )

        assert response.status_code == 201
        assert response.json()["status"] == "in_progress"

    def test_user_id_from_jwt_not_body(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/workouts",
            json={"type": "ad_hoc", "format": "weightlifting"},
            headers=_auth(_USER_A_ID),
        )

        assert response.status_code == 201
        assert response.json()["user_id"] == str(_USER_A_ID)

    def test_client_started_at_used_when_provided(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)
        started = "2026-04-29T09:00:00Z"

        response = client.post(
            "/v1/workouts",
            json={
                "type": "ad_hoc",
                "format": "weightlifting",
                "client_started_at": started,
            },
            headers=_auth(),
        )

        assert response.status_code == 201
        assert response.json()["started_at"].startswith("2026-04-29T09:00:00")

    def test_optional_fields_stored(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/workouts",
            json={
                "type": "planned",
                "format": "cardio",
                "name": "Evening Run",
                "location": "outdoor",
            },
            headers=_auth(),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Evening Run"
        assert data["location"] == "outdoor"
        assert data["type"] == "planned"
        assert data["format"] == "cardio"

    def test_name_max_length_enforced(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/workouts",
            json={"type": "ad_hoc", "format": "weightlifting", "name": "A" * 201},
            headers=_auth(),
        )

        assert response.status_code == 422

    def test_name_exactly_200_chars_accepted(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/workouts",
            json={"type": "ad_hoc", "format": "weightlifting", "name": "A" * 200},
            headers=_auth(),
        )

        assert response.status_code == 201

    def test_returns_401_when_unauthenticated(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/workouts",
            json={"type": "ad_hoc", "format": "weightlifting"},
        )

        assert response.status_code == 401
        assert response.json()["error_code"] == "auth_token_missing"

    def test_returns_422_when_type_missing(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/workouts",
            json={"format": "weightlifting"},
            headers=_auth(),
        )

        assert response.status_code == 422

    def test_returns_422_when_format_missing(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/workouts",
            json={"type": "ad_hoc"},
            headers=_auth(),
        )

        assert response.status_code == 422

    def test_returns_422_for_invalid_type(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/workouts",
            json={"type": "invalid", "format": "weightlifting"},
            headers=_auth(),
        )

        assert response.status_code == 422

    def test_response_includes_all_required_fields(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/workouts",
            json={"type": "ad_hoc", "format": "weightlifting"},
            headers=_auth(),
        )

        data = response.json()
        required = {
            "id", "user_id", "status", "type", "format",
            "started_at", "created_at", "updated_at",
        }
        assert required.issubset(data.keys())


# ── GET /v1/workouts ──────────────────────────────────────────────────────────


class TestListWorkouts:
    def test_returns_own_workouts(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.get("/v1/workouts", headers=_auth())

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["id"] == str(_WORKOUT_ID)

    def test_does_not_return_other_users_workouts(self) -> None:
        b_record = WorkoutRecord(
            id=uuid4(),
            user_id=_USER_B_ID,
            name=None,
            notes=None,
            status="in_progress",
            type="ad_hoc",
            format="weightlifting",
            plan_id=None,
            started_at=_STARTED_AT,
            completed_at=None,
            duration_seconds=None,
            location=None,
            rating=None,
            server_received_at=_NOW,
            created_at=_NOW,
            updated_at=_NOW,
        )
        repo = FakeWorkoutRepository(initial=b_record)
        client = _make_client(repo)

        response = client.get("/v1/workouts", headers=_auth(_USER_A_ID))

        assert response.status_code == 200
        assert response.json()["total"] == 0
        assert response.json()["data"] == []

    def test_ordered_by_started_at_desc(self) -> None:
        repo = FakeWorkoutRepository()
        earlier = WorkoutRecord(
            id=uuid4(),
            user_id=_USER_A_ID,
            name="Earlier",
            notes=None,
            status="completed",
            type="ad_hoc",
            format="weightlifting",
            plan_id=None,
            started_at=datetime(2026, 4, 28, 10, 0, 0, tzinfo=UTC),
            completed_at=None,
            duration_seconds=None,
            location=None,
            rating=None,
            server_received_at=_NOW,
            created_at=_NOW,
            updated_at=_NOW,
        )
        later = WorkoutRecord(
            id=uuid4(),
            user_id=_USER_A_ID,
            name="Later",
            notes=None,
            status="in_progress",
            type="ad_hoc",
            format="weightlifting",
            plan_id=None,
            started_at=datetime(2026, 4, 29, 10, 0, 0, tzinfo=UTC),
            completed_at=None,
            duration_seconds=None,
            location=None,
            rating=None,
            server_received_at=_NOW,
            created_at=_NOW,
            updated_at=_NOW,
        )
        repo._store[earlier.id] = earlier
        repo._store[later.id] = later
        client = _make_client(repo)

        response = client.get("/v1/workouts", headers=_auth())

        assert response.status_code == 200
        data = response.json()["data"]
        assert data[0]["name"] == "Later"
        assert data[1]["name"] == "Earlier"

    def test_empty_list_returns_200(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.get("/v1/workouts", headers=_auth())

        assert response.status_code == 200
        assert response.json()["total"] == 0
        assert response.json()["data"] == []

    def test_pagination_has_more(self) -> None:
        repo = FakeWorkoutRepository()
        for i in range(5):
            w = WorkoutRecord(
                id=uuid4(),
                user_id=_USER_A_ID,
                name=f"Workout {i}",
                notes=None,
                status="completed",
                type="ad_hoc",
                format="weightlifting",
                plan_id=None,
                started_at=datetime(2026, 4, i + 1, 10, 0, 0, tzinfo=UTC),
                completed_at=None,
                duration_seconds=None,
                location=None,
                rating=None,
                server_received_at=_NOW,
                created_at=_NOW,
                updated_at=_NOW,
            )
            repo._store[w.id] = w
        client = _make_client(repo)

        response = client.get("/v1/workouts?page=1&per_page=3", headers=_auth())

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["data"]) == 3
        assert data["has_more"] is True

    def test_pagination_last_page_has_more_false(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.get("/v1/workouts?page=1&per_page=20", headers=_auth())

        assert response.status_code == 200
        assert response.json()["has_more"] is False

    def test_format_filter(self) -> None:
        repo = FakeWorkoutRepository()
        cardio = WorkoutRecord(
            id=uuid4(),
            user_id=_USER_A_ID,
            name="Cardio Day",
            notes=None,
            status="in_progress",
            type="ad_hoc",
            format="cardio",
            plan_id=None,
            started_at=_STARTED_AT,
            completed_at=None,
            duration_seconds=None,
            location=None,
            rating=None,
            server_received_at=_NOW,
            created_at=_NOW,
            updated_at=_NOW,
        )
        repo._store[_DEFAULT_RECORD.id] = _DEFAULT_RECORD
        repo._store[cardio.id] = cardio
        client = _make_client(repo)

        response = client.get("/v1/workouts?format=cardio", headers=_auth())

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["format"] == "cardio"

    def test_status_filter(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.get("/v1/workouts?status=completed", headers=_auth())

        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_returns_401_when_unauthenticated(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.get("/v1/workouts")

        assert response.status_code == 401
        assert response.json()["error_code"] == "auth_token_missing"

    def test_response_includes_pagination_fields(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.get("/v1/workouts", headers=_auth())

        data = response.json()
        assert {"data", "total", "page", "per_page", "has_more"}.issubset(data.keys())


# ── GET /v1/workouts/{id} ─────────────────────────────────────────────────────


class TestGetWorkout:
    def test_returns_own_workout(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.get(f"/v1/workouts/{_WORKOUT_ID}", headers=_auth())

        assert response.status_code == 200
        assert response.json()["id"] == str(_WORKOUT_ID)

    def test_returns_404_when_not_found(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.get(f"/v1/workouts/{_WORKOUT_ID}", headers=_auth())

        assert response.status_code == 404
        assert response.json()["error_code"] == "workout_not_found"

    def test_returns_403_when_not_owned(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.get(f"/v1/workouts/{_WORKOUT_ID}", headers=_auth(_USER_B_ID))

        assert response.status_code == 403
        assert response.json()["error_code"] == "workout_forbidden"

    def test_returns_401_when_unauthenticated(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.get(f"/v1/workouts/{_WORKOUT_ID}")

        assert response.status_code == 401

    def test_error_response_has_request_id(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.get(f"/v1/workouts/{_WORKOUT_ID}", headers=_auth())

        assert response.status_code == 404
        assert "request_id" in response.json()


# ── PATCH /v1/workouts/{id} ───────────────────────────────────────────────────


class TestUpdateWorkout:
    def test_updates_name(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={"name": "Leg Day"},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Leg Day"

    def test_updates_notes(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={"notes": "Felt strong today"},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["notes"] == "Felt strong today"

    def test_updates_status_to_completed(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={"status": "completed"},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_completed_at_set_server_side_on_completion(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={"status": "completed"},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["completed_at"] is not None

    def test_duration_seconds_calculated_on_completion(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={"status": "completed"},
            headers=_auth(),
        )

        assert response.status_code == 200
        duration = response.json()["duration_seconds"]
        assert duration is not None
        assert duration > 0

    def test_empty_body_returns_current_workout(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Morning Lift"
        assert response.json()["status"] == "in_progress"

    def test_updates_rating(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={"rating": 5},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["rating"] == 5

    def test_rating_out_of_range_returns_422(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={"rating": 6},
            headers=_auth(),
        )

        assert response.status_code == 422

    def test_notes_max_length_enforced(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={"notes": "A" * 5001},
            headers=_auth(),
        )

        assert response.status_code == 422

    def test_status_paused_does_not_set_completed_at(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={"status": "paused"},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["status"] == "paused"
        assert response.json()["completed_at"] is None

    def test_returns_404_when_not_found(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={"status": "completed"},
            headers=_auth(),
        )

        assert response.status_code == 404
        assert response.json()["error_code"] == "workout_not_found"

    def test_returns_403_when_not_owned(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={"status": "completed"},
            headers=_auth(_USER_B_ID),
        )

        assert response.status_code == 403
        assert response.json()["error_code"] == "workout_forbidden"

    def test_returns_401_when_unauthenticated(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={"status": "completed"},
        )

        assert response.status_code == 401

    def test_idor_user_b_cannot_update_user_a_workout(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        client.patch(
            f"/v1/workouts/{_WORKOUT_ID}",
            json={"name": "Hacked"},
            headers=_auth(_USER_B_ID),
        )

        assert repo._store[_WORKOUT_ID].name == "Morning Lift"


# ── DELETE /v1/workouts/{id} ─────────────────────────────────────────────────


class TestDeleteWorkout:
    def test_deletes_workout_and_returns_204(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.delete(f"/v1/workouts/{_WORKOUT_ID}", headers=_auth())

        assert response.status_code == 204
        assert _WORKOUT_ID not in repo._store

    def test_returns_404_when_not_found(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.delete(f"/v1/workouts/{_WORKOUT_ID}", headers=_auth())

        assert response.status_code == 404
        assert response.json()["error_code"] == "workout_not_found"

    def test_returns_403_when_not_owned(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.delete(
            f"/v1/workouts/{_WORKOUT_ID}", headers=_auth(_USER_B_ID)
        )

        assert response.status_code == 403
        assert response.json()["error_code"] == "workout_forbidden"

    def test_returns_401_when_unauthenticated(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.delete(f"/v1/workouts/{_WORKOUT_ID}")

        assert response.status_code == 401

    def test_idor_user_b_cannot_delete_user_a_workout(self) -> None:
        repo = FakeWorkoutRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        client.delete(f"/v1/workouts/{_WORKOUT_ID}", headers=_auth(_USER_B_ID))

        assert _WORKOUT_ID in repo._store

    def test_error_response_has_request_id(self) -> None:
        repo = FakeWorkoutRepository()
        client = _make_client(repo)

        response = client.delete(f"/v1/workouts/{_WORKOUT_ID}", headers=_auth())

        assert response.status_code == 404
        assert "request_id" in response.json()


# ── Repository internals ──────────────────────────────────────────────────────


async def test_get_workout_repository_raises_runtime_error() -> None:
    """The default get_workout_repository must always be overridden in production."""
    from app.repositories.workout_repository import get_workout_repository

    with pytest.raises(RuntimeError, match="get_workout_repository"):
        await get_workout_repository()
