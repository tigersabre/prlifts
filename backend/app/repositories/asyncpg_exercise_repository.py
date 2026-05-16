"""
asyncpg_exercise_repository.py
PRLifts Backend

asyncpg implementation of ExerciseRepository. Excluded from the coverage
gate — see pyproject.toml [tool.coverage.run] omit.

Trigram similarity search uses word_similarity() from pg_trgm. Cursor
pagination is disabled when q is set (similarity ordering cannot be
resumed with a keyset — Decision 94).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import asyncpg

from app.repositories.exercise_repository import ExerciseRecord


def _from_row(row: asyncpg.Record) -> ExerciseRecord:
    secondary = row["secondary_muscle_groups"]
    return ExerciseRecord(
        id=row["id"],
        name=row["name"],
        category=str(row["category"]),
        muscle_group=str(row["muscle_group"]),
        secondary_muscle_groups=[str(m) for m in secondary] if secondary else [],
        equipment=str(row["equipment"]),
        instructions=row["instructions"],
        demo_url=row["demo_url"],
        is_custom=row["is_custom"],
        created_by=row["created_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AsyncpgExerciseRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def list_exercises(
        self,
        q: str | None,
        muscle_group: str | None,
        equipment: str | None,
        category: str | None,
        limit: int,
        cursor_created_at: datetime | None,
        cursor_id: UUID | None,
    ) -> tuple[list[ExerciseRecord], bool]:
        conditions: list[str] = []
        params: list[Any] = []
        idx = 1
        q_idx: int | None = None

        if q is not None:
            q_idx = idx
            conditions.append(f"word_similarity(${idx}, name) > 0.3")
            params.append(q)
            idx += 1

        if muscle_group is not None:
            conditions.append(f"muscle_group = ${idx}::muscle_group")
            params.append(muscle_group)
            idx += 1

        if equipment is not None:
            conditions.append(f"equipment = ${idx}::exercise_equipment")
            params.append(equipment)
            idx += 1

        if category is not None:
            conditions.append(f"category = ${idx}::exercise_category")
            params.append(category)
            idx += 1

        if cursor_created_at is not None and cursor_id is not None and q is None:
            conditions.append(f"(created_at, id) < (${idx}, ${idx + 1})")
            params.extend([cursor_created_at, cursor_id])
            idx += 2

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        if q_idx is not None:
            order = (
                f"ORDER BY word_similarity(${q_idx}, name) DESC,"
                " created_at DESC, id DESC"
            )
        else:
            order = "ORDER BY created_at DESC, id DESC"

        params.append(limit + 1)
        sql = f"SELECT * FROM exercise {where} {order} LIMIT ${idx}"
        rows = await self._pool.fetch(sql, *params)
        has_more = len(rows) > limit
        return [_from_row(r) for r in rows[:limit]], has_more
