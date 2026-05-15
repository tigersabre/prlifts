"""Drop plan_id column from workout table.

plan_id was a V2 placeholder for the WorkoutPlan foreign key. Per
STANDARDS.md §5.6 (orphaned column policy), placeholder columns for
unimplemented V2 features must not live in the schema. The WorkoutPlan
entity is V2 — no client or server code reads or writes plan_id.

This is a destructive, non-reversible column drop. The downgrade
re-adds the column as nullable so the migration chain stays valid,
but plan_id data (always NULL) is not recoverable from the down path.

Revision ID: 20260515_006
Revises: 20260515_005
Create Date: 2026-05-15

Reference: docs/SCHEMA.md § workout table
Reference: docs/ARCHITECTURE.md Decision P2-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20260515_006"
down_revision: str | None = "20260515_005"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE workout DROP COLUMN IF EXISTS plan_id"))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE workout ADD COLUMN IF NOT EXISTS plan_id UUID"))
