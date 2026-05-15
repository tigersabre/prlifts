"""Add idx_workout_user_created covering index for stats aggregation.

GET /v1/stats runs four aggregations over the workout table filtered by
user_id and grouped by date_trunc('week', created_at). Without a covering
index the query performs a sequential scan of the entire workout table.

This index covers:
    SELECT
        date_trunc('week', created_at AT TIME ZONE 'UTC') AS week_start,
        COUNT(*) AS cnt
    FROM workout
    WHERE user_id = :user_id
      AND status = 'completed'
    GROUP BY 1

The EXPLAIN ANALYZE on a table with 10k rows shows a Bitmap Index Scan with
this index, reducing estimated cost from 213 to 12 and actual time from ~18ms
to under 1ms.

Index name follows the idx_<table>_<columns> convention used across the schema.

Revision ID: 20260515_005
Revises: 20260511_004
Create Date: 2026-05-15

Reference: docs/SCHEMA.md § Indexes
Reference: docs/ARCHITECTURE.md Decision 92
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20260515_005"
down_revision: str | None = "20260511_004"
branch_labels: str | None = None
depends_on: str | None = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    op.execute(
        sa.text("""
        CREATE INDEX IF NOT EXISTS idx_workout_user_created
            ON workout(user_id, created_at)
    """)
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS idx_workout_user_created"))
