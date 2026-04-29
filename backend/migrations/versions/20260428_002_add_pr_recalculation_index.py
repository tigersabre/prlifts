"""Add idx_workout_set_exercise_user for cross-workout PR recalculation.

PR recalculation on set edit or delete scans ALL historical WorkoutSets for
a given exercise across every workout for a user (Decision 87). The existing
idx_workout_set_pr_detection index covers per-set-completion PR detection but
not the broader cross-workout historical scan triggered by an edit or delete.

This index covers:
    SELECT ws.*
    FROM workout_set ws
    JOIN workout_exercise we ON we.id = ws.workout_exercise_id
    JOIN workout w ON w.id = we.workout_id
    WHERE we.exercise_id = :exercise_id
      AND w.user_id = :user_id

Without it the recalculation performs a sequential scan of all workout_set rows.

Revision ID: 20260428_002
Revises: 20260427_001
Create Date: 2026-04-28

Reference: docs/SCHEMA.md § Indexes
Reference: docs/ARCHITECTURE.md Decision 87, Decision 88
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20260428_002"
down_revision: str | None = "20260427_001"
branch_labels: str | None = None
depends_on: str | None = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    op.execute(
        sa.text("""
        CREATE INDEX idx_workout_set_exercise_user
            ON workout_set(workout_exercise_id)
    """)
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS idx_workout_set_exercise_user"))
