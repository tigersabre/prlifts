"""
exercise_repository.py
PRLifts Backend

ExerciseRepository protocol for exercise library persistence.

See docs/SCHEMA.md — exercise table.
See docs/ARCHITECTURE.md Decision 94 — cursor-based pagination.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass
class ExerciseRecord:
    """Mirrors one row from the exercise table. All fields match column names."""

    id: UUID
    name: str
    category: str
    muscle_group: str
    secondary_muscle_groups: list[str]
    equipment: str
    instructions: str | None
    demo_url: str | None
    is_custom: bool
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if self.secondary_muscle_groups is None:
            self.secondary_muscle_groups = []


class ExerciseRepository(Protocol):
    """
    Abstract persistence interface for the exercise library.

    Production wires in a database-backed implementation. Tests inject an
    in-memory fake via app.dependency_overrides[get_exercise_repository].

    Ordering: results are always returned (created_at DESC, id DESC) when no
    search query is active, or (similarity DESC, created_at DESC, id DESC)
    when q is provided — matching the cursor composite per Decision 94.
    """

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
        """
        Return up to `limit` exercises.

        When q is provided, filters by trigram similarity and orders by
        similarity DESC. When q is absent, orders by created_at DESC, id DESC.

        The bool return value indicates whether more records exist beyond
        the returned page.
        """
        ...


async def get_exercise_repository() -> ExerciseRepository:
    """
    FastAPI dependency marker for the ExerciseRepository.

    Override in tests:
        app.dependency_overrides[get_exercise_repository] = (
            lambda: FakeExerciseRepository()
        )

    In production this is overridden in main.py lifespan once the database
    connection pool is available.

    Raises:
        RuntimeError: Always — must be overridden before any request is served.
    """
    raise RuntimeError(
        "get_exercise_repository has no default implementation. "
        "Wire a real implementation in main.py or override in tests."
    )
