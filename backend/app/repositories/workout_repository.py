"""
workout_repository.py
PRLifts Backend

WorkoutRepository protocol for workout persistence. The FastAPI dependency
get_workout_repository is the single injection point — route handlers receive
it via Depends() and tests override it with an in-memory fake.

See docs/SCHEMA.md — workout table for the authoritative column list.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass
class WorkoutRecord:
    """Mirrors one row from the workout table. All fields match column names exactly."""

    id: UUID
    user_id: UUID
    name: str | None
    notes: str | None
    status: str
    type: str
    format: str
    plan_id: UUID | None
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: int | None
    location: str | None
    rating: int | None
    server_received_at: datetime
    created_at: datetime
    updated_at: datetime


class WorkoutRepository(Protocol):
    """
    Abstract persistence interface for workouts.

    Production wires in a database-backed implementation. Tests inject an
    in-memory fake via app.dependency_overrides[get_workout_repository].
    """

    async def create(
        self,
        user_id: UUID,
        workout_type: str,
        workout_format: str,
        name: str | None,
        location: str | None,
        plan_id: UUID | None,
        client_started_at: datetime | None,
    ) -> WorkoutRecord: ...

    async def get_by_id(self, workout_id: UUID) -> WorkoutRecord | None: ...

    async def list_for_user(
        self,
        user_id: UUID,
        page: int,
        per_page: int,
        format_filter: str | None,
        status_filter: str | None,
    ) -> tuple[list[WorkoutRecord], int]: ...

    async def update(
        self,
        workout_id: UUID,
        updates: dict[str, object],
    ) -> WorkoutRecord | None: ...

    async def delete(self, workout_id: UUID) -> bool:
        """
        Delete the workout and cascade to workout_exercise and workout_set rows.

        Any personal_record rows referencing the deleted sets must be removed
        before the cascade — the PR recalculation logic handles this.

        Returns True if the workout existed and was deleted; False if not found.
        """
        ...


async def get_workout_repository() -> WorkoutRepository:
    """
    FastAPI dependency marker for the WorkoutRepository.

    Override in tests:
        app.dependency_overrides[get_workout_repository] = (
            lambda: FakeWorkoutRepository()
        )

    In production this is overridden in main.py lifespan once the database
    connection pool is available.

    Raises:
        RuntimeError: Always — must be overridden before any request is served.
    """
    raise RuntimeError(
        "get_workout_repository has no default implementation. "
        "Wire a real implementation in main.py or override in tests."
    )
