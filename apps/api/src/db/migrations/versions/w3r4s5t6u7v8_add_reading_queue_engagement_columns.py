"""Add reading_queue engagement columns (first_opened_at, dismissed_at)

Story 5.8: Reading Item Detail View and Engagement Tracking

Revision ID: w3r4s5t6u7v8
Revises: v2q3r4s5t6u7
Create Date: 2025-12-28
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "w3r4s5t6u7v8"
down_revision: str | None = "v2q3r4s5t6u7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add first_opened_at and dismissed_at columns to reading_queue table."""
    op.add_column(
        "reading_queue",
        sa.Column("first_opened_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "reading_queue",
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Remove first_opened_at and dismissed_at columns from reading_queue table."""
    op.drop_column("reading_queue", "dismissed_at")
    op.drop_column("reading_queue", "first_opened_at")
