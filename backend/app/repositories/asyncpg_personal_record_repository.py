"""
asyncpg_personal_record_repository.py
PRLifts Backend

asyncpg implementation of PersonalRecordRepository. Excluded from the
coverage gate — see pyproject.toml [tool.coverage.run] omit.

The personal_record table has no UNIQUE constraint on
(user_id, exercise_id, weight_modifier, record_type). Upsert is therefore
implemented as UPDATE-then-INSERT. This is safe because pr_service.py
calls get_current_pr before upsert, so the two-step pattern matches
the caller's intent exactly.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

import asyncpg

from app.repositories.personal_record_repository import PersonalRecordRecord


def _dec(v: Decimal | None) -> float | None:
    return float(v) if v is not None else None


def _from_row(row: asyncpg.Record) -> PersonalRecordRecord:
    return PersonalRecordRecord(
        id=row["id"],
        user_id=row["user_id"],
        exercise_id=row["exercise_id"],
        workout_set_id=row["workout_set_id"],
        weight_modifier=str(row["weight_modifier"]),
        record_type=str(row["record_type"]),
        value=float(row["value"]),
        value_unit=str(row["value_unit"]) if row["value_unit"] is not None else None,
        recorded_at=row["recorded_at"],
        previous_value=_dec(row["previous_value"]),
        previous_recorded_at=row["previous_recorded_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


_WHERE_KEY = (
    "user_id = $1 AND exercise_id = $2"
    " AND weight_modifier = $3::weight_modifier AND record_type = $4::record_type"
)


class AsyncpgPersonalRecordRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_current_pr(
        self,
        user_id: UUID,
        exercise_id: UUID,
        weight_modifier: str,
        record_type: str,
    ) -> PersonalRecordRecord | None:
        row = await self._pool.fetchrow(
            f"SELECT * FROM personal_record WHERE {_WHERE_KEY}",
            user_id,
            exercise_id,
            weight_modifier,
            record_type,
        )
        return _from_row(row) if row is not None else None

    async def upsert(
        self,
        user_id: UUID,
        exercise_id: UUID,
        workout_set_id: UUID,
        weight_modifier: str,
        record_type: str,
        value: float,
        value_unit: str | None,
        recorded_at: datetime,
        previous_value: float | None,
        previous_recorded_at: datetime | None,
    ) -> PersonalRecordRecord:
        row = await self._pool.fetchrow(
            f"""
            UPDATE personal_record SET
                workout_set_id       = $3,
                value                = $6,
                value_unit           = $7::value_unit,
                recorded_at          = $8,
                previous_value       = $9,
                previous_recorded_at = $10,
                updated_at           = NOW()
            WHERE {_WHERE_KEY}
            RETURNING *
            """,
            user_id,
            exercise_id,
            workout_set_id,
            weight_modifier,
            record_type,
            value,
            value_unit,
            recorded_at,
            previous_value,
            previous_recorded_at,
        )
        if row is not None:
            return _from_row(row)

        row = await self._pool.fetchrow(
            """
            INSERT INTO personal_record (
                user_id, exercise_id, workout_set_id, weight_modifier, record_type,
                value, value_unit, recorded_at, previous_value, previous_recorded_at
            ) VALUES (
                $1, $2, $3, $4::weight_modifier, $5::record_type,
                $6, $7::value_unit, $8, $9, $10
            )
            RETURNING *
            """,
            user_id,
            exercise_id,
            workout_set_id,
            weight_modifier,
            record_type,
            value,
            value_unit,
            recorded_at,
            previous_value,
            previous_recorded_at,
        )
        return _from_row(row)

    async def delete_if_exists(
        self,
        user_id: UUID,
        exercise_id: UUID,
        weight_modifier: str,
        record_type: str,
    ) -> bool:
        tag = await self._pool.execute(
            f"DELETE FROM personal_record WHERE {_WHERE_KEY}",
            user_id,
            exercise_id,
            weight_modifier,
            record_type,
        )
        return int(tag.split()[-1]) > 0
