"""
user_repository.py
PRLifts Backend

UserRepository protocol for user profile persistence. The FastAPI dependency
get_user_repository is the single injection point — route handlers receive it
via Depends() and tests override it with an in-memory fake.

See docs/SCHEMA.md — user table for the authoritative column list.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from uuid import UUID


@dataclass
class UserRecord:
    """Mirrors one row from the user table. All fields match column names exactly."""

    id: UUID
    email: str | None
    display_name: str | None
    avatar_url: str | None
    unit_preference: str
    measurement_unit: str
    date_of_birth: date | None
    gender: str
    goal: str | None
    beta_tier: str
    created_at: datetime
    updated_at: datetime


class UserRepository(Protocol):
    """
    Abstract persistence interface for user profiles.

    Production wires in a database-backed implementation. Tests inject an
    in-memory fake via app.dependency_overrides[get_user_repository].
    """

    async def create(
        self,
        user_id: UUID,
        display_name: str | None,
        unit_preference: str,
        measurement_unit: str,
    ) -> UserRecord: ...

    async def get_by_id(self, user_id: UUID) -> UserRecord | None: ...

    async def update(
        self,
        user_id: UUID,
        updates: dict[str, object],
    ) -> UserRecord | None: ...

    async def exists(self, user_id: UUID) -> bool: ...


async def get_user_repository() -> UserRepository:
    """
    FastAPI dependency marker for the UserRepository.

    Override in tests:
        app.dependency_overrides[get_user_repository] = lambda: FakeUserRepository()

    In production this is overridden in main.py lifespan once the database
    connection pool is available.

    Raises:
        RuntimeError: Always — must be overridden before any request is served.
    """
    raise RuntimeError(
        "get_user_repository has no default implementation. "
        "Wire a real implementation in main.py or override in tests."
    )
