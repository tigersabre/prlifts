"""
asyncpg_stats_repository.py
PRLifts Backend

asyncpg implementation of StatsRepository. Excluded from the coverage
gate — see pyproject.toml [tool.coverage.run] omit.
"""

from __future__ import annotations

from uuid import UUID

import asyncpg

from app.repositories.stats_repository import StatsRecord

_STATS_SQL = """
    WITH weekly AS (
        SELECT
            date_trunc('week', created_at AT TIME ZONE 'UTC') AS week_start,
            COUNT(*) AS cnt
        FROM workout
        WHERE user_id = $1
          AND status = 'completed'
        GROUP BY 1
    ),
    current_week_start AS (
        SELECT date_trunc('week', NOW() AT TIME ZONE 'UTC') AS w
    )
    SELECT
        COALESCE(SUM(cnt) FILTER (
            WHERE week_start = (SELECT w FROM current_week_start)
        ), 0) AS weekly_count,
        COALESCE(MAX(cnt), 0)  AS best_week,
        COALESCE(SUM(cnt), 0)  AS total_workouts,
        (SELECT COUNT(*) FROM personal_record
         WHERE user_id = $1)   AS total_prs
    FROM weekly
"""


class AsyncpgStatsRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_stats(self, user_id: UUID) -> StatsRecord:
        row = await self._pool.fetchrow(_STATS_SQL, user_id)
        return StatsRecord(
            weekly_count=int(row["weekly_count"]),
            best_week=int(row["best_week"]),
            total_workouts=int(row["total_workouts"]),
            total_prs=int(row["total_prs"]),
        )
