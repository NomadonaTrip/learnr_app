"""Create quiz_sessions table for adaptive quiz engine

Revision ID: l2g3h4i5j6k7
Revises: k1f2g3h4i5j6
Create Date: 2025-12-17

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'l2g3h4i5j6k7'
down_revision: str | None = 'k1f2g3h4i5j6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create quiz_sessions table per architecture schema
    op.create_table(
        'quiz_sessions',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('enrollment_id', UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('session_type', sa.String(50), nullable=False, server_default="'adaptive'"),
        sa.Column('question_strategy', sa.String(50), nullable=False, server_default="'max_info_gain'"),
        sa.Column('knowledge_area_filter', sa.String(50), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('correct_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_paused', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "session_type IN ('diagnostic', 'adaptive', 'focused', 'review')",
            name='check_quiz_session_type'
        ),
        sa.CheckConstraint(
            "question_strategy IN ('max_info_gain', 'max_uncertainty', 'prerequisite_first', 'balanced')",
            name='check_quiz_question_strategy'
        ),
    )

    # Create indexes per architecture specification
    # Index for user lookup
    op.create_index('idx_quiz_sessions_user', 'quiz_sessions', ['user_id'])

    # Index for enrollment lookup
    op.create_index('idx_quiz_sessions_enrollment', 'quiz_sessions', ['enrollment_id'])

    # Partial index for active sessions (ended_at IS NULL) - optimizes finding active session
    op.execute("""
        CREATE INDEX idx_quiz_sessions_user_active
        ON quiz_sessions (user_id, ended_at)
        WHERE ended_at IS NULL
    """)

    # Create trigger function for updating version on modification (optimistic locking)
    op.execute("""
        CREATE OR REPLACE FUNCTION update_quiz_session_version()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.version = OLD.version + 1;
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_quiz_session_version
        BEFORE UPDATE ON quiz_sessions
        FOR EACH ROW
        EXECUTE FUNCTION update_quiz_session_version();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trigger_quiz_session_version ON quiz_sessions")
    op.execute("DROP FUNCTION IF EXISTS update_quiz_session_version()")
    op.execute("DROP INDEX IF EXISTS idx_quiz_sessions_user_active")
    op.drop_index('idx_quiz_sessions_enrollment', table_name='quiz_sessions')
    op.drop_index('idx_quiz_sessions_user', table_name='quiz_sessions')
    op.drop_table('quiz_sessions')
