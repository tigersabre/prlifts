"""
workout_set_repository.py
PRLifts Backend

WorkoutSetRepository protocol for workout_set persistence.
user_id and exercise_id are included in WorkoutSetRecord (via JOINs through
workout_exercise → workout) for IDOR checks and PR detection.

See docs/SCHEMA.md — workout_set table.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass
class WorkoutSetRecord:
    """
    Mirrors one row from workout_set plus user_id and exercise_id joined from
    workout_exercise and workout. Backend-only fields; not exposed in API responses.
    """

    id: UUID
    workout_exercise_id: UUID
    user_id: UUID
    exercise_id: UUID
    set_number: int
    set_type: str
    weight: float | None
    weight_unit: str | None
    weight_modifier: str
    modifier_value: float | None
    modifier_unit: str | None
    reps: int | None
    duration_seconds: int | None
    distance_meters: float | None
    calories: int | None
    rpe: int | None
    is_completed: bool
    notes: str | None
    server_received_at: datetime
    created_at: datetime
    updated_at: datetime


class WorkoutSetRepository(Protocol):
    """
    Abstract persistence interface for workout_set rows.

    user_id and exercise_id are passed into create so the fake can store them
    without a JOIN. Production implementations derive them via FKs.

    list_for_exercise_user is the cross-workout query used by PR recalculation
    (Decision 87). It uses idx_workout_set_exercise_user in production.
    """

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
    ) -> WorkoutSetRecord: ...

    async def get_by_id(self, workout_set_id: UUID) -> WorkoutSetRecord | None: ...

    async def update(
        self,
        workout_set_id: UUID,
        updates: dict[str, object],
    ) -> WorkoutSetRecord | None: ...

    async def delete(self, workout_set_id: UUID) -> bool: ...

    async def list_for_exercise_user(
        self,
        exercise_id: UUID,
        user_id: UUID,
        weight_modifier: str,
    ) -> list[WorkoutSetRecord]: ...


async def get_workout_set_repository() -> WorkoutSetRepository:
    """
    FastAPI dependency marker. Override in tests and in main.py lifespan.

    Raises:
        RuntimeError: Always — must be overridden before any request is served.
    """
    raise RuntimeError(
        "get_workout_set_repository has no default implementation. "
        "Wire a real implementation in main.py or override in tests."
    )
