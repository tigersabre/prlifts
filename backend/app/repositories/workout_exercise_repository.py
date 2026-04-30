"""
workout_exercise_repository.py
PRLifts Backend

WorkoutExerciseRepository protocol for workout_exercise persistence.
user_id is included in WorkoutExerciseRecord (via JOIN from workout) for IDOR checks.

See docs/SCHEMA.md — workout_exercise table.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass
class WorkoutExerciseRecord:
    """
    Mirrors one row from workout_exercise plus user_id joined from workout.
    user_id is backend-only — not exposed in API responses.
    """

    id: UUID
    workout_id: UUID
    user_id: UUID
    exercise_id: UUID
    order_index: int
    notes: str | None
    rest_seconds: int | None
    created_at: datetime
    updated_at: datetime


class WorkoutExerciseRepository(Protocol):
    """
    Abstract persistence interface for workout_exercise rows.
    user_id is passed into create so the fake can store it without a JOIN.
    Production implementations derive user_id via the workout FK.
    """

    async def create(
        self,
        workout_id: UUID,
        user_id: UUID,
        exercise_id: UUID,
        order_index: int,
        notes: str | None,
        rest_seconds: int | None,
    ) -> WorkoutExerciseRecord: ...

    async def get_by_id(
        self, workout_exercise_id: UUID
    ) -> WorkoutExerciseRecord | None: ...

    async def delete(self, workout_exercise_id: UUID) -> bool: ...


async def get_workout_exercise_repository() -> WorkoutExerciseRepository:
    """
    FastAPI dependency marker. Override in tests and in main.py lifespan.

    Raises:
        RuntimeError: Always — must be overridden before any request is served.
    """
    raise RuntimeError(
        "get_workout_exercise_repository has no default implementation. "
        "Wire a real implementation in main.py or override in tests."
    )
