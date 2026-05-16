"""
asyncpg_workout_exercise_repository.py
PRLifts Backend

asyncpg implementation of WorkoutExerciseRepository. Excluded from the
coverage gate — see pyproject.toml [tool.coverage.run] omit.
"""

from __future__ import annotations

from uuid import UUID

import asyncpg

from app.repositories.workout_exercise_repository import WorkoutExerciseRecord


def _from_row(
    row: asyncpg.Record, user_id: UUID | None = None
) -> WorkoutExerciseRecord:
    return WorkoutExerciseRecord(
        id=row["id"],
        workout_id=row["workout_id"],
        user_id=user_id if user_id is not None else row["user_id"],
        exercise_id=row["exercise_id"],
        order_index=row["order_index"],
        notes=row["notes"],
        rest_seconds=row["rest_seconds"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AsyncpgWorkoutExerciseRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(
        self,
        workout_id: UUID,
        user_id: UUID,
        exercise_id: UUID,
        order_index: int,
        notes: str | None,
        rest_seconds: int | None,
    ) -> WorkoutExerciseRecord:
        row = await self._pool.fetchrow(
            """
            INSERT INTO workout_exercise
                (workout_id, exercise_id, order_index, notes, rest_seconds)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            workout_id,
            exercise_id,
            order_index,
            notes,
            rest_seconds,
        )
        return _from_row(row, user_id=user_id)

    async def get_by_id(
        self, workout_exercise_id: UUID
    ) -> WorkoutExerciseRecord | None:
        row = await self._pool.fetchrow(
            """
            SELECT we.*, w.user_id
            FROM workout_exercise we
            JOIN workout w ON w.id = we.workout_id
            WHERE we.id = $1
            """,
            workout_exercise_id,
        )
        return _from_row(row) if row is not None else None

    async def delete(self, workout_exercise_id: UUID) -> bool:
        tag = await self._pool.execute(
            "DELETE FROM workout_exercise WHERE id = $1",
            workout_exercise_id,
        )
        return int(tag.split()[-1]) > 0
