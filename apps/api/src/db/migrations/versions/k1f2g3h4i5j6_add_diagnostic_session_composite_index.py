"""Add composite index on diagnostic_sessions for faster combined lookups

Revision ID: k1f2g3h4i5j6
Revises: j0e1f2g3h4i5
Create Date: 2025-12-16

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'k1f2g3h4i5j6'
down_revision: str | None = 'j0e1f2g3h4i5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add composite index for faster combined lookups on (user_id, enrollment_id, status)
    # This optimizes queries that filter by user and enrollment to find sessions by status
    op.create_index(
        'idx_diagnostic_sessions_user_enrollment_status',
        'diagnostic_sessions',
        ['user_id', 'enrollment_id', 'status'],
    )


def downgrade() -> None:
    op.drop_index(
        'idx_diagnostic_sessions_user_enrollment_status',
        table_name='diagnostic_sessions',
    )
