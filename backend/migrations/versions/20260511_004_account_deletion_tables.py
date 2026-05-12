"""Create audit_log and image_deletion_queue tables for account deletion.

audit_log is an append-only event store for system-level events (e.g.
user.deletion_completed). user_id is stored as a plain UUID column with no FK
constraint so audit records survive after the user row is deleted.

image_deletion_queue holds Fal.ai image URLs that need manual deletion. The
Fal.ai DPA is not yet signed, so the backend cannot call the Fal.ai deletion API
directly — images are queued for manual operator cleanup instead.
See ARCHITECTURE.md Decision 95.

Revision ID: 20260511_004
Revises: 20260510_003
Create Date: 2026-05-11

Reference: docs/SCHEMA.md
Reference: docs/ARCHITECTURE.md Decision 95 — account hard delete
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20260511_004"
down_revision: str | None = "20260510_003"
branch_labels: str | None = None
depends_on: str | None = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    op.execute(
        sa.text("""
        CREATE TABLE audit_log (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_type TEXT        NOT NULL,
            user_id    UUID,
            payload    JSONB       NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """)
    )
    op.execute(
        sa.text(
            "COMMENT ON TABLE audit_log IS "
            "'Append-only system event log. user_id has no FK constraint — rows "
            "must survive user account deletion. Used for user.deletion_completed "
            "audit entries and other system events. Never deleted by cascade.'"
        )
    )

    op.execute(
        sa.text("""
        CREATE TABLE image_deletion_queue (
            id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id      UUID,
            image_url    TEXT        NOT NULL,
            queued_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            processed_at TIMESTAMPTZ
        )
        """)
    )
    op.execute(
        sa.text(
            "COMMENT ON TABLE image_deletion_queue IS "
            "'Fal.ai generated image URLs queued for manual operator deletion. "
            "The Fal.ai DPA is not yet signed — images cannot be programmatically "
            "deleted. An operator processes rows where processed_at IS NULL. "
            "user_id has no FK — the user row is deleted before this is processed.'"
        )
    )

    op.execute(
        sa.text(
            "CREATE INDEX idx_image_deletion_queue_unprocessed "
            "ON image_deletion_queue(queued_at) "
            "WHERE processed_at IS NULL"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_audit_log_event_type "
            "ON audit_log(event_type, created_at DESC)"
        )
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS image_deletion_queue"))
    op.execute(sa.text("DROP TABLE IF EXISTS audit_log"))
