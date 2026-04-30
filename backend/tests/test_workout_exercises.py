"""
test_workout_exercises.py
PRLifts Backend Tests

Unit tests for the WorkoutExercise CRUD endpoints:
  POST   /v1/workout-exercises        — add exercise to workout
  DELETE /v1/workout-exercises/{id}   — remove exercise from workout

See docs/SCHEMA.md — workout_exercise table.
See GitHub Issue #37 for acceptance criteria.
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

from app.repositories.workout_exercise_repository import (  # noqa: E402
    WorkoutExerciseRecord,
)
from app.repositories.workout_repository import WorkoutRecord  # noqa: E402

# ── Constants ────────────────────────────────────────────────────────────────

_SECRET: str = os.environ.get(
    "SUPABASE_JWT_SECRET", "test-supabase-jwt-secret-for-unit-tests"
)
_ALGORITHM = "HS256"
_AUDIENCE = "authenticated"

_USER_A_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_USER_B_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_WORKOUT_ID = UUID("11111111-1111-1111-1111-111111111111")
_EXERCISE_ID = UUID("22222222-2222-2222-2222-222222222222")
_WE_ID = UUID("33333333-3333-3333-3333-333333333333")

_NOW = datetime(2026, 4, 29, 12, 0, 0, tzinfo=UTC)

_DEFAULT_WORKOUT = WorkoutRecord(
    id=_WORKOUT_ID,
    user_id=_USER_A_ID,
    name="Push Day",
    notes=None,
    status="in_progress",
    type="ad_hoc",
    format="weightlifting",
    plan_id=None,
    started_at=_NOW,
    completed_at=None,
    duration_seconds=None,
    location="gym",
    rating=None,
    server_received_at=_NOW,
    created_at=_NOW,
    updated_at=_NOW,
)

_DEFAULT_WE = WorkoutExerciseRecord(
    id=_WE_ID,
    workout_id=_WORKOUT_ID,
    user_id=_USER_A_ID,
    exercise_id=_EXERCISE_ID,
    order_index=0,
    notes=None,
    rest_seconds=None,
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


# ── Fake repositories ─────────────────────────────────────────────────────────


class FakeWorkoutRepository:
    def __init__(self, initial: WorkoutRecord | None = None) -> None:
        self._store: dict[UUID, WorkoutRecord] = {}
        if initial:
            self._store[initial.id] = initial

    async def create(self, **_: Any) -> WorkoutRecord:
        raise NotImplementedError

    async def get_by_id(self, workout_id: UUID) -> WorkoutRecord | None:
        return self._store.get(workout_id)

    async def list_for_user(self, **_: Any) -> tuple[list[WorkoutRecord], int]:
        raise NotImplementedError

    async def update(self, **_: Any) -> WorkoutRecord | None:
        raise NotImplementedError

    async def delete(self, workout_id: UUID) -> bool:
        raise NotImplementedError


class FakeWorkoutExerciseRepository:
    def __init__(self, initial: WorkoutExerciseRecord | None = None) -> None:
        self._store: dict[UUID, WorkoutExerciseRecord] = {}
        if initial:
            self._store[initial.id] = initial

    async def create(
        self,
        workout_id: UUID,
        user_id: UUID,
        exercise_id: UUID,
        order_index: int,
        notes: str | None,
        rest_seconds: int | None,
    ) -> WorkoutExerciseRecord:
        now = datetime.now(UTC)
        record = WorkoutExerciseRecord(
            id=uuid4(),
            workout_id=workout_id,
            user_id=user_id,
            exercise_id=exercise_id,
            order_index=order_index,
            notes=notes,
            rest_seconds=rest_seconds,
            created_at=now,
            updated_at=now,
        )
        self._store[record.id] = record
        return record

    async def get_by_id(
        self, workout_exercise_id: UUID
    ) -> WorkoutExerciseRecord | None:
        return self._store.get(workout_exercise_id)

    async def delete(self, workout_exercise_id: UUID) -> bool:
        if workout_exercise_id not in self._store:
            return False
        del self._store[workout_exercise_id]
        return True


# ── Fixture helpers ───────────────────────────────────────────────────────────


def _make_client(
    exercise_repo: FakeWorkoutExerciseRepository,
    workout_repo: FakeWorkoutRepository,
) -> TestClient:
    from app.repositories.workout_exercise_repository import (
        get_workout_exercise_repository,
    )
    from app.repositories.workout_repository import get_workout_repository
    from main import app

    app.dependency_overrides[get_workout_exercise_repository] = lambda: exercise_repo
    app.dependency_overrides[get_workout_repository] = lambda: workout_repo
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Generator[None, None, None]:
    yield
    from main import app

    app.dependency_overrides.clear()


# ── POST /v1/workout-exercises ────────────────────────────────────────────────


class TestCreateWorkoutExercise:
    def test_creates_and_returns_201(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository()
        workout_repo = FakeWorkoutRepository(initial=_DEFAULT_WORKOUT)
        client = _make_client(exercise_repo, workout_repo)

        response = client.post(
            "/v1/workout-exercises",
            json={
                "workout_id": str(_WORKOUT_ID),
                "exercise_id": str(_EXERCISE_ID),
                "order_index": 0,
            },
            headers=_auth(),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["workout_id"] == str(_WORKOUT_ID)
        assert data["exercise_id"] == str(_EXERCISE_ID)
        assert data["order_index"] == 0
        assert "id" in data

    def test_stores_optional_fields(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository()
        workout_repo = FakeWorkoutRepository(initial=_DEFAULT_WORKOUT)
        client = _make_client(exercise_repo, workout_repo)

        response = client.post(
            "/v1/workout-exercises",
            json={
                "workout_id": str(_WORKOUT_ID),
                "exercise_id": str(_EXERCISE_ID),
                "order_index": 1,
                "notes": "Focus on depth",
                "rest_seconds": 120,
            },
            headers=_auth(),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["notes"] == "Focus on depth"
        assert data["rest_seconds"] == 120

    def test_response_does_not_include_user_id(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository()
        workout_repo = FakeWorkoutRepository(initial=_DEFAULT_WORKOUT)
        client = _make_client(exercise_repo, workout_repo)

        response = client.post(
            "/v1/workout-exercises",
            json={
                "workout_id": str(_WORKOUT_ID),
                "exercise_id": str(_EXERCISE_ID),
                "order_index": 0,
            },
            headers=_auth(),
        )

        assert response.status_code == 201
        assert "user_id" not in response.json()

    def test_returns_404_when_workout_not_found(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository()
        workout_repo = FakeWorkoutRepository()
        client = _make_client(exercise_repo, workout_repo)

        response = client.post(
            "/v1/workout-exercises",
            json={
                "workout_id": str(uuid4()),
                "exercise_id": str(_EXERCISE_ID),
                "order_index": 0,
            },
            headers=_auth(),
        )

        assert response.status_code == 404
        assert response.json()["error_code"] == "workout_not_found"

    def test_returns_403_when_workout_belongs_to_another_user(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository()
        workout_repo = FakeWorkoutRepository(initial=_DEFAULT_WORKOUT)
        client = _make_client(exercise_repo, workout_repo)

        response = client.post(
            "/v1/workout-exercises",
            json={
                "workout_id": str(_WORKOUT_ID),
                "exercise_id": str(_EXERCISE_ID),
                "order_index": 0,
            },
            headers=_auth(_USER_B_ID),
        )

        assert response.status_code == 403
        assert response.json()["error_code"] == "workout_forbidden"

    def test_returns_401_when_unauthenticated(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository()
        workout_repo = FakeWorkoutRepository(initial=_DEFAULT_WORKOUT)
        client = _make_client(exercise_repo, workout_repo)

        response = client.post(
            "/v1/workout-exercises",
            json={
                "workout_id": str(_WORKOUT_ID),
                "exercise_id": str(_EXERCISE_ID),
                "order_index": 0,
            },
        )

        assert response.status_code == 401

    def test_returns_422_when_missing_required_fields(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository()
        workout_repo = FakeWorkoutRepository(initial=_DEFAULT_WORKOUT)
        client = _make_client(exercise_repo, workout_repo)

        response = client.post(
            "/v1/workout-exercises",
            json={"workout_id": str(_WORKOUT_ID)},
            headers=_auth(),
        )

        assert response.status_code == 422

    def test_idor_user_b_cannot_add_exercise_to_user_a_workout(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository()
        workout_repo = FakeWorkoutRepository(initial=_DEFAULT_WORKOUT)
        client = _make_client(exercise_repo, workout_repo)

        client.post(
            "/v1/workout-exercises",
            json={
                "workout_id": str(_WORKOUT_ID),
                "exercise_id": str(_EXERCISE_ID),
                "order_index": 0,
            },
            headers=_auth(_USER_B_ID),
        )

        assert len(exercise_repo._store) == 0

    def test_rest_seconds_max_enforced(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository()
        workout_repo = FakeWorkoutRepository(initial=_DEFAULT_WORKOUT)
        client = _make_client(exercise_repo, workout_repo)

        response = client.post(
            "/v1/workout-exercises",
            json={
                "workout_id": str(_WORKOUT_ID),
                "exercise_id": str(_EXERCISE_ID),
                "order_index": 0,
                "rest_seconds": 3601,
            },
            headers=_auth(),
        )

        assert response.status_code == 422

    def test_error_response_has_request_id(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository()
        workout_repo = FakeWorkoutRepository()
        client = _make_client(exercise_repo, workout_repo)

        response = client.post(
            "/v1/workout-exercises",
            json={
                "workout_id": str(uuid4()),
                "exercise_id": str(_EXERCISE_ID),
                "order_index": 0,
            },
            headers=_auth(),
        )

        assert response.status_code == 404
        assert "request_id" in response.json()


# ── DELETE /v1/workout-exercises/{id} ────────────────────────────────────────


class TestDeleteWorkoutExercise:
    def test_deletes_and_returns_204(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository(initial=_DEFAULT_WE)
        workout_repo = FakeWorkoutRepository(initial=_DEFAULT_WORKOUT)
        client = _make_client(exercise_repo, workout_repo)

        response = client.delete(f"/v1/workout-exercises/{_WE_ID}", headers=_auth())

        assert response.status_code == 204
        assert _WE_ID not in exercise_repo._store

    def test_returns_404_when_not_found(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository()
        workout_repo = FakeWorkoutRepository()
        client = _make_client(exercise_repo, workout_repo)

        response = client.delete(f"/v1/workout-exercises/{_WE_ID}", headers=_auth())

        assert response.status_code == 404
        assert response.json()["error_code"] == "workout_exercise_not_found"

    def test_returns_403_when_not_owned(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository(initial=_DEFAULT_WE)
        workout_repo = FakeWorkoutRepository()
        client = _make_client(exercise_repo, workout_repo)

        response = client.delete(
            f"/v1/workout-exercises/{_WE_ID}", headers=_auth(_USER_B_ID)
        )

        assert response.status_code == 403
        assert response.json()["error_code"] == "workout_exercise_forbidden"

    def test_returns_401_when_unauthenticated(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository(initial=_DEFAULT_WE)
        workout_repo = FakeWorkoutRepository()
        client = _make_client(exercise_repo, workout_repo)

        response = client.delete(f"/v1/workout-exercises/{_WE_ID}")

        assert response.status_code == 401

    def test_idor_user_b_cannot_delete_user_a_exercise(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository(initial=_DEFAULT_WE)
        workout_repo = FakeWorkoutRepository()
        client = _make_client(exercise_repo, workout_repo)

        client.delete(f"/v1/workout-exercises/{_WE_ID}", headers=_auth(_USER_B_ID))

        assert _WE_ID in exercise_repo._store

    def test_error_response_has_request_id(self) -> None:
        exercise_repo = FakeWorkoutExerciseRepository()
        workout_repo = FakeWorkoutRepository()
        client = _make_client(exercise_repo, workout_repo)

        response = client.delete(f"/v1/workout-exercises/{_WE_ID}", headers=_auth())

        assert response.status_code == 404
        assert "request_id" in response.json()


# ── Repository internals ──────────────────────────────────────────────────────


async def test_get_workout_exercise_repository_raises_runtime_error() -> None:
    from app.repositories.workout_exercise_repository import (
        get_workout_exercise_repository,
    )

    with pytest.raises(RuntimeError, match="get_workout_exercise_repository"):
        await get_workout_exercise_repository()
