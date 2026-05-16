"""
asyncpg_workout_repository.py
PRLifts Backend

asyncpg implementation of WorkoutRepository. Excluded from the coverage gate
— see pyproject.toml [tool.coverage.run] omit.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import asyncpg

from app.repositories.workout_repository import WorkoutRecord

_ENUM_CASTS: dict[str, str] = {
    "status": "::workout_status",
    "type": "::workout_type",
    "format": "::workout_format",
    "location": "::workout_location",
}


def _from_row(row: asyncpg.Record) -> WorkoutRecord:
    return WorkoutRecord(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        notes=row["notes"],
        status=str(row["status"]),
        type=str(row["type"]),
        format=str(row["format"]),
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        duration_seconds=row["duration_seconds"],
        location=str(row["location"]) if row["location"] is not None else None,
        rating=row["rating"],
        server_received_at=row["server_received_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AsyncpgWorkoutRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(
        self,
        user_id: UUID,
        workout_type: str,
        workout_format: str,
        name: str | None,
        location: str | None,
        client_started_at: datetime | None,
    ) -> WorkoutRecord:
        started_at = client_started_at or datetime.now(UTC)
        row = await self._pool.fetchrow(
            """
            INSERT INTO workout (
                user_id, type, format, name, location, started_at, status
            ) VALUES (
                $1, $2::workout_type, $3::workout_format, $4,
                $5::workout_location, $6, 'in_progress'::workout_status
            )
            RETURNING *
            """,
            user_id,
            workout_type,
            workout_format,
            name,
            location,
            started_at,
        )
        return _from_row(row)

    async def get_by_id(self, workout_id: UUID) -> WorkoutRecord | None:
        row = await self._pool.fetchrow(
            "SELECT * FROM workout WHERE id = $1",
            workout_id,
        )
        return _from_row(row) if row is not None else None

    async def list_for_user(
        self,
        user_id: UUID,
        limit: int,
        cursor_created_at: datetime | None,
        cursor_id: UUID | None,
        format_filter: str | None,
        status_filter: str | None,
    ) -> tuple[list[WorkoutRecord], bool]:
        conditions: list[str] = ["user_id = $1"]
        params: list[Any] = [user_id]
        idx = 2

        if cursor_created_at is not None and cursor_id is not None:
            conditions.append(f"(created_at, id) < (${idx}, ${idx + 1})")
            params.extend([cursor_created_at, cursor_id])
            idx += 2

        if format_filter is not None:
            conditions.append(f"format = ${idx}::workout_format")
            params.append(format_filter)
            idx += 1

        if status_filter is not None:
            conditions.append(f"status = ${idx}::workout_status")
            params.append(status_filter)
            idx += 1

        params.append(limit + 1)
        sql = (
            f"SELECT * FROM workout WHERE {' AND '.join(conditions)}"
            f" ORDER BY created_at DESC, id DESC LIMIT ${idx}"
        )
        rows = await self._pool.fetch(sql, *params)
        has_more = len(rows) > limit
        return [_from_row(r) for r in rows[:limit]], has_more

    async def update(
        self,
        workout_id: UUID,
        updates: dict[str, object],
    ) -> WorkoutRecord | None:
        if not updates:
            return await self.get_by_id(workout_id)

        parts: list[str] = []
        values: list[object] = []
        for i, (col, val) in enumerate(updates.items(), start=1):
            cast = _ENUM_CASTS.get(col, "")
            parts.append(f"{col} = ${i}{cast}")
            values.append(val)

        n = len(values) + 1
        values.append(workout_id)
        sql = (
            f"UPDATE workout SET {', '.join(parts)}, updated_at = NOW()"
            f" WHERE id = ${n} RETURNING *"
        )
        row = await self._pool.fetchrow(sql, *values)
        return _from_row(row) if row is not None else None

    async def delete(self, workout_id: UUID) -> bool:
        tag = await self._pool.execute(
            "DELETE FROM workout WHERE id = $1",
            workout_id,
        )
        return int(tag.split()[-1]) > 0
