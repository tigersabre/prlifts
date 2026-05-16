"""
asyncpg_user_repository.py
PRLifts Backend

asyncpg implementation of UserRepository. Excluded from the coverage gate
— see pyproject.toml [tool.coverage.run] omit.
"""

from __future__ import annotations

from uuid import UUID

import asyncpg

from app.repositories.user_repository import UserRecord

_ENUM_CASTS: dict[str, str] = {
    "unit_preference": "::weight_unit",
    "measurement_unit": "::measurement_unit",
    "gender": "::gender",
    "goal": "::user_goal",
    "beta_tier": "::beta_tier",
}


def _from_row(row: asyncpg.Record) -> UserRecord:
    return UserRecord(
        id=row["id"],
        email=row["email"],
        display_name=row["display_name"],
        avatar_url=row["avatar_url"],
        unit_preference=str(row["unit_preference"]),
        measurement_unit=str(row["measurement_unit"]),
        date_of_birth=row["date_of_birth"],
        gender=str(row["gender"]),
        goal=str(row["goal"]) if row["goal"] is not None else None,
        beta_tier=str(row["beta_tier"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AsyncpgUserRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(
        self,
        user_id: UUID,
        display_name: str | None,
        unit_preference: str,
        measurement_unit: str,
    ) -> UserRecord:
        row = await self._pool.fetchrow(
            """
            INSERT INTO "user" (id, display_name, unit_preference, measurement_unit)
            VALUES ($1, $2, $3::weight_unit, $4::measurement_unit)
            RETURNING *
            """,
            user_id,
            display_name,
            unit_preference,
            measurement_unit,
        )
        return _from_row(row)

    async def get_by_id(self, user_id: UUID) -> UserRecord | None:
        row = await self._pool.fetchrow(
            'SELECT * FROM "user" WHERE id = $1',
            user_id,
        )
        return _from_row(row) if row is not None else None

    async def update(
        self,
        user_id: UUID,
        updates: dict[str, object],
    ) -> UserRecord | None:
        if not updates:
            return await self.get_by_id(user_id)

        parts: list[str] = []
        values: list[object] = []
        for i, (col, val) in enumerate(updates.items(), start=1):
            cast = _ENUM_CASTS.get(col, "")
            parts.append(f"{col} = ${i}{cast}")
            values.append(val)

        n = len(values) + 1
        values.append(user_id)
        sql = (
            f'UPDATE "user" SET {", ".join(parts)}, updated_at = NOW()'
            f" WHERE id = ${n} RETURNING *"
        )
        row = await self._pool.fetchrow(sql, *values)
        return _from_row(row) if row is not None else None

    async def exists(self, user_id: UUID) -> bool:
        row = await self._pool.fetchrow(
            'SELECT 1 FROM "user" WHERE id = $1',
            user_id,
        )
        return row is not None
