"""
asyncpg_workout_set_repository.py
PRLifts Backend

asyncpg implementation of WorkoutSetRepository. Excluded from the coverage
gate — see pyproject.toml [tool.coverage.run] omit.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

import asyncpg

from app.repositories.workout_set_repository import WorkoutSetRecord

_ENUM_CASTS: dict[str, str] = {
    "set_type": "::set_type",
    "weight_unit": "::weight_unit",
    "weight_modifier": "::weight_modifier",
    "modifier_unit": "::weight_unit",
}

_JOINED_SELECT = """
    SELECT ws.*, w.user_id, we.exercise_id
    FROM workout_set ws
    JOIN workout_exercise we ON we.id = ws.workout_exercise_id
    JOIN workout w ON w.id = we.workout_id
"""


def _dec(v: Decimal | None) -> float | None:
    return float(v) if v is not None else None


def _from_row(
    row: asyncpg.Record,
    user_id: UUID | None = None,
    exercise_id: UUID | None = None,
) -> WorkoutSetRecord:
    return WorkoutSetRecord(
        id=row["id"],
        workout_exercise_id=row["workout_exercise_id"],
        user_id=user_id if user_id is not None else row["user_id"],
        exercise_id=exercise_id if exercise_id is not None else row["exercise_id"],
        set_number=row["set_number"],
        set_type=str(row["set_type"]),
        weight=_dec(row["weight"]),
        weight_unit=str(row["weight_unit"]) if row["weight_unit"] is not None else None,
        weight_modifier=str(row["weight_modifier"]),
        modifier_value=_dec(row["modifier_value"]),
        modifier_unit=(
            str(row["modifier_unit"]) if row["modifier_unit"] is not None else None
        ),
        reps=row["reps"],
        duration_seconds=row["duration_seconds"],
        distance_meters=_dec(row["distance_meters"]),
        calories=row["calories"],
        rpe=row["rpe"],
        is_completed=row["is_completed"],
        notes=row["notes"],
        server_received_at=row["server_received_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AsyncpgWorkoutSetRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

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
        row = await self._pool.fetchrow(
            """
            INSERT INTO workout_set (
                workout_exercise_id, set_number, set_type,
                weight, weight_unit, weight_modifier,
                modifier_value, modifier_unit, reps,
                duration_seconds, distance_meters, calories,
                rpe, is_completed, notes
            ) VALUES (
                $1, $2, $3::set_type,
                $4, $5::weight_unit, $6::weight_modifier,
                $7, $8::weight_unit, $9,
                $10, $11, $12,
                $13, $14, $15
            )
            RETURNING *
            """,
            workout_exercise_id,
            set_number,
            set_type,
            weight,
            weight_unit,
            weight_modifier,
            modifier_value,
            modifier_unit,
            reps,
            duration_seconds,
            distance_meters,
            calories,
            rpe,
            is_completed,
            notes,
        )
        return _from_row(row, user_id=user_id, exercise_id=exercise_id)

    async def get_by_id(self, workout_set_id: UUID) -> WorkoutSetRecord | None:
        row = await self._pool.fetchrow(
            f"{_JOINED_SELECT} WHERE ws.id = $1",
            workout_set_id,
        )
        return _from_row(row) if row is not None else None

    async def update(
        self,
        workout_set_id: UUID,
        updates: dict[str, object],
    ) -> WorkoutSetRecord | None:
        if not updates:
            return await self.get_by_id(workout_set_id)

        parts: list[str] = []
        values: list[Any] = []
        for i, (col, val) in enumerate(updates.items(), start=1):
            cast = _ENUM_CASTS.get(col, "")
            parts.append(f"{col} = ${i}{cast}")
            values.append(val)

        n = len(values) + 1
        values.append(workout_set_id)
        sql = f"""
            WITH updated AS (
                UPDATE workout_set SET {", ".join(parts)}, updated_at = NOW()
                WHERE id = ${n}
                RETURNING *
            )
            SELECT u.*, w.user_id, we.exercise_id
            FROM updated u
            JOIN workout_exercise we ON we.id = u.workout_exercise_id
            JOIN workout w ON w.id = we.workout_id
        """
        row = await self._pool.fetchrow(sql, *values)
        return _from_row(row) if row is not None else None

    async def delete(self, workout_set_id: UUID) -> bool:
        tag = await self._pool.execute(
            "DELETE FROM workout_set WHERE id = $1",
            workout_set_id,
        )
        return int(tag.split()[-1]) > 0

    async def list_for_exercise_user(
        self,
        exercise_id: UUID,
        user_id: UUID,
        weight_modifier: str,
    ) -> list[WorkoutSetRecord]:
        rows = await self._pool.fetch(
            f"""
            {_JOINED_SELECT}
            WHERE we.exercise_id = $1
              AND w.user_id = $2
              AND ws.weight_modifier = $3::weight_modifier
            ORDER BY ws.created_at DESC
            """,
            exercise_id,
            user_id,
            weight_modifier,
        )
        return [_from_row(r) for r in rows]
