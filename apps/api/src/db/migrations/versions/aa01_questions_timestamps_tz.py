"""questions timestamps -> timezone-aware

Revision ID: aa01questionstz
Revises: 38b668be7ca9
Create Date: 2026-06-27
"""
from alembic import op
import sqlalchemy as sa

revision = "aa01questionstz"
down_revision = "38b668be7ca9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("questions", "created_at", type_=sa.DateTime(timezone=True),
                    existing_nullable=False, postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column("questions", "updated_at", type_=sa.DateTime(timezone=True),
                    existing_nullable=False, postgresql_using="updated_at AT TIME ZONE 'UTC'")


def downgrade() -> None:
    op.alter_column("questions", "updated_at", type_=sa.TIMESTAMP(),
                    existing_nullable=False, postgresql_using="updated_at AT TIME ZONE 'UTC'")
    op.alter_column("questions", "created_at", type_=sa.TIMESTAMP(),
                    existing_nullable=False, postgresql_using="created_at AT TIME ZONE 'UTC'")
