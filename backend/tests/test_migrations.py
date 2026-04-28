"""
test_migrations.py
PRLifts Backend Tests

Integration test for the V1 Alembic migration. Verifies that the migration
applies cleanly, can be rolled back cleanly, and is idempotent on re-apply.

This test requires a real PostgreSQL database and is skipped automatically
when ENVIRONMENT=test (the default for the unit-test run). To run it locally:

    ENVIRONMENT=development pytest tests/test_migrations.py -v

The test leaves the database in the pre-migration (empty) state after it runs.
Alembic reads DATABASE_URL from the environment or from .env.local via env.py.
"""

import os

import pytest

_REAL_DB_AVAILABLE = os.environ.get("ENVIRONMENT") != "test"


@pytest.mark.skipif(
    not _REAL_DB_AVAILABLE,
    reason=(
        "Integration test — requires a real PostgreSQL instance. "
        "Run locally with ENVIRONMENT=development and a valid DATABASE_URL."
    ),
)
def test_v1_migration_applies_and_rolls_back_cleanly() -> None:
    """
    Verifies the V1 schema migration satisfies all DoD conditions:

    1. Applies cleanly from an empty database (upgrade head)
    2. Is idempotent — a second upgrade head completes with no changes
    3. Rolls back cleanly without errors (downgrade -1)
    4. Can be re-applied after rollback

    The test always cleans up — the database is left at base state
    regardless of pass or failure.
    """
    # Arrange — lazy import so the test module is collectable without alembic
    # being configured (alembic reads env vars it may not find in test mode).
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")

    try:
        # Ensure we start from a clean baseline (idempotent if already at base)
        command.downgrade(cfg, "base")

        # Act — apply migration
        command.upgrade(cfg, "head")

        # Assert — idempotent re-apply produces no errors
        command.upgrade(cfg, "head")

        # Act — roll back the single migration step
        command.downgrade(cfg, "-1")

        # Assert — can be re-applied after rollback (schema is consistent)
        command.upgrade(cfg, "head")

    finally:
        # Always return the database to the pre-migration state
        command.downgrade(cfg, "base")
