"""
personal_record_repository.py
PRLifts Backend

PersonalRecordRepository protocol for personal_record persistence.
Used exclusively by the PR detection service — never written by user-facing endpoints.

See docs/SCHEMA.md — personal_record table.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass
class PersonalRecordRecord:
    """Mirrors one row from the personal_record table."""

    id: UUID
    user_id: UUID
    exercise_id: UUID
    workout_set_id: UUID
    weight_modifier: str
    record_type: str
    value: float
    value_unit: str | None
    recorded_at: datetime
    previous_value: float | None
    previous_recorded_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PersonalRecordRepository(Protocol):
    """
    Abstract persistence interface for personal_record rows.

    Rows are keyed by (user_id, exercise_id, weight_modifier, record_type).
    Each combination has at most one active PR row.
    """

    async def get_current_pr(
        self,
        user_id: UUID,
        exercise_id: UUID,
        weight_modifier: str,
        record_type: str,
    ) -> PersonalRecordRecord | None: ...

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
    ) -> PersonalRecordRecord: ...

    async def delete_if_exists(
        self,
        user_id: UUID,
        exercise_id: UUID,
        weight_modifier: str,
        record_type: str,
    ) -> bool: ...


async def get_personal_record_repository() -> PersonalRecordRepository:
    """
    FastAPI dependency marker. Override in tests and in main.py lifespan.

    Raises:
        RuntimeError: Always — must be overridden before any request is served.
    """
    raise RuntimeError(
        "get_personal_record_repository has no default implementation. "
        "Wire a real implementation in main.py or override in tests."
    )
