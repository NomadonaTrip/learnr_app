"""Add unique partial index to enforce single active quiz session per user

This migration:
1. Cleans up any existing duplicate active sessions (keeps most recent, ends others)
2. Adds a unique partial index to prevent race conditions from creating duplicates

Revision ID: x4s5t6u7v8w9
Revises: w3r4s5t6u7v8
Create Date: 2025-12-28

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'x4s5t6u7v8w9'
down_revision: str | None = 'w3r4s5t6u7v8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Step 1: Clean up existing duplicate active sessions
    # For each user with multiple active sessions, keep only the most recent one
    # and mark the others as ended
    op.execute("""
        WITH ranked_sessions AS (
            SELECT
                id,
                user_id,
                ROW_NUMBER() OVER (
                    PARTITION BY user_id
                    ORDER BY started_at DESC
                ) as rn
            FROM quiz_sessions
            WHERE ended_at IS NULL
        )
        UPDATE quiz_sessions
        SET ended_at = NOW()
        WHERE id IN (
            SELECT id FROM ranked_sessions WHERE rn > 1
        )
    """)

    # Step 2: Add unique partial index to enforce single active session per user
    # This prevents race conditions from creating duplicate active sessions
    op.execute("""
        CREATE UNIQUE INDEX idx_quiz_sessions_user_active_unique
        ON quiz_sessions (user_id)
        WHERE ended_at IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_quiz_sessions_user_active_unique")
