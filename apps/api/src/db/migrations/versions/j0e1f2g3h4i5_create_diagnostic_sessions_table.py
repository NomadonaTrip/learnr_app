"""Create diagnostic_sessions table

Revision ID: j0e1f2g3h4i5
Revises: i9d0e1f2g3h4
Create Date: 2025-12-16

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = 'j0e1f2g3h4i5'
down_revision: str | None = 'i9d0e1f2g3h4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create diagnostic_sessions table for session state management
    op.create_table(
        'diagnostic_sessions',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('enrollment_id', UUID(as_uuid=True), nullable=False),
        sa.Column('question_ids', JSONB, nullable=False),
        sa.Column('current_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default="'in_progress'"),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "status IN ('in_progress', 'completed', 'expired', 'reset')",
            name='diagnostic_session_status_check'
        ),
        sa.CheckConstraint('current_index >= 0', name='diagnostic_session_index_check'),
    )

    # Create indexes per schema specification
    # Index for user lookup
    op.create_index('idx_diagnostic_sessions_user', 'diagnostic_sessions', ['user_id'])

    # Index for enrollment lookup
    op.create_index('idx_diagnostic_sessions_enrollment', 'diagnostic_sessions', ['enrollment_id'])

    # Partial unique index: only one active session per enrollment
    op.execute("""
        CREATE UNIQUE INDEX idx_diagnostic_sessions_active_enrollment
        ON diagnostic_sessions (enrollment_id)
        WHERE status = 'in_progress'
    """)

    # Index for stale session cleanup (started_at for in_progress sessions)
    op.execute("""
        CREATE INDEX idx_diagnostic_sessions_stale
        ON diagnostic_sessions (started_at)
        WHERE status = 'in_progress'
    """)

    # Create trigger for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_diagnostic_sessions_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_diagnostic_sessions_updated_at
        BEFORE UPDATE ON diagnostic_sessions
        FOR EACH ROW
        EXECUTE FUNCTION update_diagnostic_sessions_updated_at();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trigger_diagnostic_sessions_updated_at ON diagnostic_sessions")
    op.execute("DROP FUNCTION IF EXISTS update_diagnostic_sessions_updated_at()")
    op.execute("DROP INDEX IF EXISTS idx_diagnostic_sessions_stale")
    op.execute("DROP INDEX IF EXISTS idx_diagnostic_sessions_active_enrollment")
    op.drop_index('idx_diagnostic_sessions_enrollment', table_name='diagnostic_sessions')
    op.drop_index('idx_diagnostic_sessions_user', table_name='diagnostic_sessions')
    op.drop_table('diagnostic_sessions')
