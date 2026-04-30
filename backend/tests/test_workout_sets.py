"""
test_workout_sets.py
PRLifts Backend Tests

Unit tests for the WorkoutSet CRUD endpoints:
  POST   /v1/workout-sets        — log a set, triggers PR detection
  PATCH  /v1/workout-sets/{id}   — update a set, triggers PR recalculation
  DELETE /v1/workout-sets/{id}   — delete a set, triggers PR recalculation

See docs/SCHEMA.md — workout_set, personal_record tables.
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
from app.repositories.workout_set_repository import WorkoutSetRecord  # noqa: E402
from app.services.pr_service import FakePersonalRecordRepository  # noqa: E402

# ── Constants ────────────────────────────────────────────────────────────────

_SECRET: str = os.environ.get(
    "SUPABASE_JWT_SECRET", "test-supabase-jwt-secret-for-unit-tests"
)
_ALGORITHM = "HS256"
_AUDIENCE = "authenticated"

_USER_A_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_USER_B_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_WE_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_EXERCISE_ID = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
_SET_ID = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")

_NOW = datetime(2026, 4, 29, 12, 0, 0, tzinfo=UTC)

_DEFAULT_WE = WorkoutExerciseRecord(
    id=_WE_ID,
    workout_id=uuid4(),
    user_id=_USER_A_ID,
    exercise_id=_EXERCISE_ID,
    order_index=0,
    notes=None,
    rest_seconds=None,
    created_at=_NOW,
    updated_at=_NOW,
)

_DEFAULT_SET = WorkoutSetRecord(
    id=_SET_ID,
    workout_exercise_id=_WE_ID,
    user_id=_USER_A_ID,
    exercise_id=_EXERCISE_ID,
    set_number=1,
    set_type="normal",
    weight=100.0,
    weight_unit="kg",
    weight_modifier="none",
    modifier_value=None,
    modifier_unit=None,
    reps=5,
    duration_seconds=None,
    distance_meters=None,
    calories=None,
    rpe=8,
    is_completed=True,
    notes=None,
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


# ── Fake repositories ─────────────────────────────────────────────────────────


class FakeWorkoutExerciseRepository:
    def __init__(self, initial: WorkoutExerciseRecord | None = None) -> None:
        self._store: dict[UUID, WorkoutExerciseRecord] = {}
        if initial:
            self._store[initial.id] = initial

    async def create(self, **_: Any) -> WorkoutExerciseRecord:
        raise NotImplementedError

    async def get_by_id(self, we_id: UUID) -> WorkoutExerciseRecord | None:
        return self._store.get(we_id)

    async def delete(self, we_id: UUID) -> bool:
        raise NotImplementedError


class FakeWorkoutSetRepository:
    def __init__(self, initial: WorkoutSetRecord | None = None) -> None:
        self._store: dict[UUID, WorkoutSetRecord] = {}
        if initial:
            self._store[initial.id] = initial

    async def create(
        self,
        workout_exercise_id: UUID,
        user_id: UUID,
        exercise_id: UUID,
        set_number: int,
        set_type: str,
        weight: float | None,
        weight_unit: str | None,
        weight_modifier: str,
        modifier_value: float | None,
        modifier_unit: str | None,
        reps: int | None,
        duration_seconds: int | None,
        distance_meters: float | None,
        calories: int | None,
        rpe: int | None,
        is_completed: bool,
        notes: str | None,
    ) -> WorkoutSetRecord:
        now = datetime.now(UTC)
        record = WorkoutSetRecord(
            id=uuid4(),
            workout_exercise_id=workout_exercise_id,
            user_id=user_id,
            exercise_id=exercise_id,
            set_number=set_number,
            set_type=set_type,
            weight=weight,
            weight_unit=weight_unit,
            weight_modifier=weight_modifier,
            modifier_value=modifier_value,
            modifier_unit=modifier_unit,
            reps=reps,
            duration_seconds=duration_seconds,
            distance_meters=distance_meters,
            calories=calories,
            rpe=rpe,
            is_completed=is_completed,
            notes=notes,
            server_received_at=now,
            created_at=now,
            updated_at=now,
        )
        self._store[record.id] = record
        return record

    async def get_by_id(self, workout_set_id: UUID) -> WorkoutSetRecord | None:
        return self._store.get(workout_set_id)

    async def update(
        self, workout_set_id: UUID, updates: dict[str, object]
    ) -> WorkoutSetRecord | None:
        record = self._store.get(workout_set_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        updated = WorkoutSetRecord(
            id=record.id,
            workout_exercise_id=record.workout_exercise_id,
            user_id=record.user_id,
            exercise_id=record.exercise_id,
            set_number=int(updates.get("set_number", record.set_number)),  # type: ignore[arg-type]
            set_type=str(updates.get("set_type", record.set_type)),
            weight=updates.get("weight", record.weight),  # type: ignore[arg-type]
            weight_unit=updates.get("weight_unit", record.weight_unit),  # type: ignore[arg-type]
            weight_modifier=str(updates.get("weight_modifier", record.weight_modifier)),
            modifier_value=updates.get("modifier_value", record.modifier_value),  # type: ignore[arg-type]
            modifier_unit=updates.get("modifier_unit", record.modifier_unit),  # type: ignore[arg-type]
            reps=updates.get("reps", record.reps),  # type: ignore[arg-type]
            duration_seconds=updates.get("duration_seconds", record.duration_seconds),  # type: ignore[arg-type]
            distance_meters=updates.get("distance_meters", record.distance_meters),  # type: ignore[arg-type]
            calories=updates.get("calories", record.calories),  # type: ignore[arg-type]
            rpe=updates.get("rpe", record.rpe),  # type: ignore[arg-type]
            is_completed=bool(updates.get("is_completed", record.is_completed)),
            notes=updates.get("notes", record.notes),  # type: ignore[arg-type]
            server_received_at=record.server_received_at,
            created_at=record.created_at,
            updated_at=now,
        )
        self._store[workout_set_id] = updated
        return updated

    async def delete(self, workout_set_id: UUID) -> bool:
        if workout_set_id not in self._store:
            return False
        del self._store[workout_set_id]
        return True

    async def list_for_exercise_user(
        self, exercise_id: UUID, user_id: UUID, weight_modifier: str
    ) -> list[WorkoutSetRecord]:
        return [
            s
            for s in self._store.values()
            if s.exercise_id == exercise_id
            and s.user_id == user_id
            and s.weight_modifier == weight_modifier
        ]


# ── Fixture helpers ───────────────────────────────────────────────────────────


def _make_client(
    exercise_repo: FakeWorkoutExerciseRepository,
    set_repo: FakeWorkoutSetRepository,
    pr_repo: FakePersonalRecordRepository,
) -> TestClient:
    from app.repositories.personal_record_repository import (
        get_personal_record_repository,
    )
    from app.repositories.workout_exercise_repository import (
        get_workout_exercise_repository,
    )
    from app.repositories.workout_set_repository import get_workout_set_repository
    from main import app

    app.dependency_overrides[get_workout_exercise_repository] = lambda: exercise_repo
    app.dependency_overrides[get_workout_set_repository] = lambda: set_repo
    app.dependency_overrides[get_personal_record_repository] = lambda: pr_repo
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Generator[None, None, None]:
    yield
    from main import app

    app.dependency_overrides.clear()


# ── POST /v1/workout-sets ─────────────────────────────────────────────────────


class TestCreateWorkoutSet:
    def test_creates_set_and_returns_201(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(initial=_DEFAULT_WE),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.post(
            "/v1/workout-sets",
            json={
                "workout_exercise_id": str(_WE_ID),
                "set_number": 1,
                "weight": 100.0,
                "weight_unit": "kg",
                "reps": 5,
                "is_completed": True,
            },
            headers=_auth(),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["workout_exercise_id"] == str(_WE_ID)
        assert data["set_number"] == 1
        assert data["weight"] == 100.0
        assert data["reps"] == 5

    def test_response_includes_is_personal_record(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(initial=_DEFAULT_WE),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.post(
            "/v1/workout-sets",
            json={
                "workout_exercise_id": str(_WE_ID),
                "set_number": 1,
                "weight": 100.0,
                "reps": 5,
            },
            headers=_auth(),
        )

        assert response.status_code == 201
        assert "is_personal_record" in response.json()

    def test_first_set_is_a_personal_record(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(initial=_DEFAULT_WE),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.post(
            "/v1/workout-sets",
            json={
                "workout_exercise_id": str(_WE_ID),
                "set_number": 1,
                "weight": 100.0,
            },
            headers=_auth(),
        )

        assert response.status_code == 201
        assert response.json()["is_personal_record"] is True

    def test_second_lower_set_is_not_pr(self) -> None:
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        pr_repo = FakePersonalRecordRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(initial=_DEFAULT_WE),
            set_repo,
            pr_repo,
        )

        import asyncio

        # Establish existing PR at 100kg
        asyncio.run(
            pr_repo.upsert(
                _USER_A_ID,
                _EXERCISE_ID,
                _SET_ID,
                "none",
                "heaviest_weight",
                value=100.0,
                value_unit="kg",
                recorded_at=_NOW,
                previous_value=None,
                previous_recorded_at=None,
            )
        )

        response = client.post(
            "/v1/workout-sets",
            json={
                "workout_exercise_id": str(_WE_ID),
                "set_number": 2,
                "weight": 90.0,
            },
            headers=_auth(),
        )

        assert response.status_code == 201
        assert response.json()["is_personal_record"] is False

    def test_heavier_set_is_pr(self) -> None:
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        pr_repo = FakePersonalRecordRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(initial=_DEFAULT_WE),
            set_repo,
            pr_repo,
        )

        import asyncio

        asyncio.run(
            pr_repo.upsert(
                _USER_A_ID,
                _EXERCISE_ID,
                _SET_ID,
                "none",
                "heaviest_weight",
                value=100.0,
                value_unit="kg",
                recorded_at=_NOW,
                previous_value=None,
                previous_recorded_at=None,
            )
        )

        response = client.post(
            "/v1/workout-sets",
            json={
                "workout_exercise_id": str(_WE_ID),
                "set_number": 2,
                "weight": 105.0,
            },
            headers=_auth(),
        )

        assert response.status_code == 201
        assert response.json()["is_personal_record"] is True

    def test_must_have_metric_validated(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(initial=_DEFAULT_WE),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.post(
            "/v1/workout-sets",
            json={
                "workout_exercise_id": str(_WE_ID),
                "set_number": 1,
                "rpe": 8,
            },
            headers=_auth(),
        )

        assert response.status_code == 422

    def test_returns_404_when_workout_exercise_not_found(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.post(
            "/v1/workout-sets",
            json={
                "workout_exercise_id": str(_WE_ID),
                "set_number": 1,
                "weight": 100.0,
            },
            headers=_auth(),
        )

        assert response.status_code == 404
        assert response.json()["error_code"] == "workout_exercise_not_found"

    def test_returns_403_when_exercise_belongs_to_another_user(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(initial=_DEFAULT_WE),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.post(
            "/v1/workout-sets",
            json={
                "workout_exercise_id": str(_WE_ID),
                "set_number": 1,
                "weight": 100.0,
            },
            headers=_auth(_USER_B_ID),
        )

        assert response.status_code == 403
        assert response.json()["error_code"] == "workout_exercise_forbidden"

    def test_returns_401_when_unauthenticated(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(initial=_DEFAULT_WE),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.post(
            "/v1/workout-sets",
            json={
                "workout_exercise_id": str(_WE_ID),
                "set_number": 1,
                "weight": 100.0,
            },
        )

        assert response.status_code == 401

    def test_weight_modifier_defaults_to_none(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(initial=_DEFAULT_WE),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.post(
            "/v1/workout-sets",
            json={
                "workout_exercise_id": str(_WE_ID),
                "set_number": 1,
                "reps": 10,
            },
            headers=_auth(),
        )

        assert response.status_code == 201
        assert response.json()["weight_modifier"] == "none"

    def test_rpe_out_of_range_rejected(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(initial=_DEFAULT_WE),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.post(
            "/v1/workout-sets",
            json={
                "workout_exercise_id": str(_WE_ID),
                "set_number": 1,
                "weight": 100.0,
                "rpe": 11,
            },
            headers=_auth(),
        )

        assert response.status_code == 422

    def test_response_includes_required_fields(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(initial=_DEFAULT_WE),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.post(
            "/v1/workout-sets",
            json={
                "workout_exercise_id": str(_WE_ID),
                "set_number": 1,
                "weight": 100.0,
            },
            headers=_auth(),
        )

        data = response.json()
        required = {
            "id",
            "workout_exercise_id",
            "set_number",
            "set_type",
            "weight_modifier",
            "is_completed",
            "is_personal_record",
            "created_at",
            "updated_at",
        }
        assert required.issubset(data.keys())


# ── PATCH /v1/workout-sets/{id} ───────────────────────────────────────────────


class TestUpdateWorkoutSet:
    def test_updates_weight_and_returns_200(self) -> None:
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.patch(
            f"/v1/workout-sets/{_SET_ID}",
            json={"weight": 110.0},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["weight"] == 110.0

    def test_response_includes_is_personal_record(self) -> None:
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.patch(
            f"/v1/workout-sets/{_SET_ID}",
            json={"weight": 110.0},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert "is_personal_record" in response.json()

    def test_edit_weight_up_sets_is_pr_true(self) -> None:
        import asyncio

        pr_repo = FakePersonalRecordRepository()
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            pr_repo,
        )

        asyncio.run(
            pr_repo.upsert(
                _USER_A_ID,
                _EXERCISE_ID,
                _SET_ID,
                "none",
                "heaviest_weight",
                value=100.0,
                value_unit="kg",
                recorded_at=_NOW,
                previous_value=None,
                previous_recorded_at=None,
            )
        )

        response = client.patch(
            f"/v1/workout-sets/{_SET_ID}",
            json={"weight": 110.0},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["is_personal_record"] is True

    def test_empty_body_returns_unchanged_set(self) -> None:
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.patch(
            f"/v1/workout-sets/{_SET_ID}",
            json={},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["weight"] == 100.0

    def test_returns_404_when_not_found(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.patch(
            f"/v1/workout-sets/{_SET_ID}",
            json={"weight": 110.0},
            headers=_auth(),
        )

        assert response.status_code == 404
        assert response.json()["error_code"] == "workout_set_not_found"

    def test_returns_403_when_not_owned(self) -> None:
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.patch(
            f"/v1/workout-sets/{_SET_ID}",
            json={"weight": 110.0},
            headers=_auth(_USER_B_ID),
        )

        assert response.status_code == 403
        assert response.json()["error_code"] == "workout_set_forbidden"

    def test_returns_401_when_unauthenticated(self) -> None:
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.patch(
            f"/v1/workout-sets/{_SET_ID}",
            json={"weight": 110.0},
        )

        assert response.status_code == 401

    def test_idor_user_b_cannot_update_user_a_set(self) -> None:
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        client.patch(
            f"/v1/workout-sets/{_SET_ID}",
            json={"weight": 999.0},
            headers=_auth(_USER_B_ID),
        )

        assert set_repo._store[_SET_ID].weight == 100.0

    def test_rpe_out_of_range_rejected(self) -> None:
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.patch(
            f"/v1/workout-sets/{_SET_ID}",
            json={"rpe": 0},
            headers=_auth(),
        )

        assert response.status_code == 422

    def test_error_response_has_request_id(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.patch(
            f"/v1/workout-sets/{_SET_ID}",
            json={"weight": 110.0},
            headers=_auth(),
        )

        assert response.status_code == 404
        assert "request_id" in response.json()


# ── DELETE /v1/workout-sets/{id} ─────────────────────────────────────────────


class TestDeleteWorkoutSet:
    def test_deletes_set_and_returns_204(self) -> None:
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.delete(f"/v1/workout-sets/{_SET_ID}", headers=_auth())

        assert response.status_code == 204
        assert _SET_ID not in set_repo._store

    def test_pr_removed_when_only_set_deleted(self) -> None:
        import asyncio

        pr_repo = FakePersonalRecordRepository()
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            pr_repo,
        )

        asyncio.run(
            pr_repo.upsert(
                _USER_A_ID,
                _EXERCISE_ID,
                _SET_ID,
                "none",
                "heaviest_weight",
                value=100.0,
                value_unit="kg",
                recorded_at=_NOW,
                previous_value=None,
                previous_recorded_at=None,
            )
        )

        client.delete(f"/v1/workout-sets/{_SET_ID}", headers=_auth())

        pr = asyncio.run(
            pr_repo.get_current_pr(_USER_A_ID, _EXERCISE_ID, "none", "heaviest_weight")
        )
        assert pr is None

    def test_returns_404_when_not_found(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.delete(f"/v1/workout-sets/{_SET_ID}", headers=_auth())

        assert response.status_code == 404
        assert response.json()["error_code"] == "workout_set_not_found"

    def test_returns_403_when_not_owned(self) -> None:
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.delete(
            f"/v1/workout-sets/{_SET_ID}", headers=_auth(_USER_B_ID)
        )

        assert response.status_code == 403
        assert response.json()["error_code"] == "workout_set_forbidden"

    def test_returns_401_when_unauthenticated(self) -> None:
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.delete(f"/v1/workout-sets/{_SET_ID}")

        assert response.status_code == 401

    def test_idor_user_b_cannot_delete_user_a_set(self) -> None:
        set_repo = FakeWorkoutSetRepository(initial=_DEFAULT_SET)
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        client.delete(f"/v1/workout-sets/{_SET_ID}", headers=_auth(_USER_B_ID))

        assert _SET_ID in set_repo._store

    def test_error_response_has_request_id(self) -> None:
        set_repo = FakeWorkoutSetRepository()
        client = _make_client(
            FakeWorkoutExerciseRepository(),
            set_repo,
            FakePersonalRecordRepository(),
        )

        response = client.delete(f"/v1/workout-sets/{_SET_ID}", headers=_auth())

        assert response.status_code == 404
        assert "request_id" in response.json()


# ── Repository internals ──────────────────────────────────────────────────────


async def test_get_workout_set_repository_raises_runtime_error() -> None:
    from app.repositories.workout_set_repository import get_workout_set_repository

    with pytest.raises(RuntimeError, match="get_workout_set_repository"):
        await get_workout_set_repository()


async def test_get_personal_record_repository_raises_runtime_error() -> None:
    from app.repositories.personal_record_repository import (
        get_personal_record_repository,
    )

    with pytest.raises(RuntimeError, match="get_personal_record_repository"):
        await get_personal_record_repository()
