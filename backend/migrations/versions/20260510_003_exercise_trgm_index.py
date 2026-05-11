"""Ensure pg_trgm extension and GIN index exist for exercise name search.

The pg_trgm extension and idx_exercise_name_trgm index were included in the
V1 schema migration (20260427_001). This migration adds an idempotent guard so
environments where pg_trgm was not available at initial migration time, or
databases restored from pre-index snapshots, get the index on next upgrade.

CREATE INDEX CONCURRENTLY cannot run inside a transaction block. Alembic wraps
migrations in a transaction by default, so we switch the connection to
AUTOCOMMIT for the CONCURRENTLY statement only, then restore normal behaviour.

Revision ID: 20260510_003
Revises: 20260428_002
Create Date: 2026-05-10

Reference: docs/SCHEMA.md § Indexes — idx_exercise_name_trgm
Reference: docs/ARCHITECTURE.md Decision 94 — cursor-based pagination
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20260510_003"
down_revision: str | None = "20260428_002"
branch_labels: str | None = None
depends_on: str | None = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    # Extension is safe to create inside a transaction (idempotent).
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "pg_trgm"'))

    # CONCURRENTLY requires autocommit — no transaction wrapper allowed.
    conn = op.get_bind()
    conn.execution_options(isolation_level="AUTOCOMMIT")
    op.execute(
        sa.text(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_exercise_name_trgm"
            " ON exercise USING gin(name gin_trgm_ops)"
        )
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    # Drop the index only — leaving the extension in place is intentional.
    # pg_trgm may be used by other indexes; dropping it is destructive and
    # requires explicit operator action.
    op.execute(sa.text("DROP INDEX IF EXISTS idx_exercise_name_trgm"))
