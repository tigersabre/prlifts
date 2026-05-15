"""
stats_repository.py
PRLifts Backend

StatsRepository protocol for user statistics aggregation. Returns pre-aggregated
counts for the GET /v1/stats endpoint without exposing raw query details to the
router layer.

The production implementation executes a single SQL query with four scalar
aggregations over the workout and personal_record tables:
  - weekly_count:    workouts completed in the current Mon–Sun UTC window
  - best_week:       MAX weekly completed count across all time
  - total_workouts:  lifetime completed workouts for the user
  - total_prs:       rows in personal_record for the user

See docs/SCHEMA.md — workout table, personal_record table.
See docs/ARCHITECTURE.md Decision 92 — weekly consistency metric definition.
"""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass
class StatsRecord:
    """Aggregated stats for one user. All fields are non-negative integers."""

    weekly_count: int
    best_week: int
    total_workouts: int
    total_prs: int


class StatsRepository(Protocol):
    """
    Abstract persistence interface for user statistics.

    Production wires in a database-backed implementation. Tests inject an
    in-memory fake via app.dependency_overrides[get_stats_repository].
    """

    async def get_stats(self, user_id: UUID) -> StatsRecord:
        """
        Return aggregated stats for user_id.

        Never returns None — new users with no history receive a StatsRecord
        with all fields set to 0.

        Production SQL (single query, covering index on workout(user_id, created_at)):

            WITH weekly AS (
                SELECT
                    date_trunc('week', created_at AT TIME ZONE 'UTC') AS week_start,
                    COUNT(*) AS cnt
                FROM workout
                WHERE user_id = :user_id
                  AND status = 'completed'
                GROUP BY 1
            ),
            current_week_start AS (
                SELECT date_trunc('week', NOW() AT TIME ZONE 'UTC') AS w
            )
            SELECT
                COALESCE(SUM(cnt) FILTER (
                    WHERE week_start = (SELECT w FROM current_week_start)
                ), 0)                           AS weekly_count,
                COALESCE(MAX(cnt), 0)           AS best_week,
                COALESCE(SUM(cnt), 0)           AS total_workouts,
                (SELECT COUNT(*) FROM personal_record
                 WHERE user_id = :user_id)      AS total_prs
            FROM weekly;
        """
        ...


async def get_stats_repository() -> StatsRepository:
    """
    FastAPI dependency marker for the StatsRepository.

    Override in tests:
        app.dependency_overrides[get_stats_repository] = lambda: FakeStatsRepository()

    In production this is overridden in main.py lifespan once the database
    connection pool is available.

    Raises:
        RuntimeError: Always — must be overridden before any request is served.
    """
    raise RuntimeError(
        "get_stats_repository has no default implementation. "
        "Wire a real implementation in main.py or override in tests."
    )
