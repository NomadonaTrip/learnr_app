"""Create quiz_responses table

Revision ID: m3h4i5j6k7l8
Revises: l2g3h4i5j6k7
Create Date: 2025-12-17

Story 4.2: Bayesian Question Selection Engine
- Tracks individual question responses within quiz sessions
- Enables recency filtering and session-level deduplication

Story 4.3: Answer Submission and Immediate Feedback
- Added request_id for idempotency
- Added info_gain_actual for Bayesian belief tracking
- Added belief_updates JSONB for concept update snapshots
- Added CHECK constraint for selected_answer
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'm3h4i5j6k7l8'
down_revision = 'l2g3h4i5j6k7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'quiz_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('selected_answer', sa.String(1), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('time_taken_ms', sa.Integer(), nullable=True),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('info_gain_actual', sa.Float(), nullable=True),
        sa.Column('belief_updates', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['quiz_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.CheckConstraint("selected_answer IN ('A', 'B', 'C', 'D')", name='ck_quiz_responses_selected_answer'),
        sa.UniqueConstraint('request_id', name='uq_quiz_responses_request_id'),
    )

    # Create indexes
    op.create_index('ix_quiz_responses_user_id', 'quiz_responses', ['user_id'])
    op.create_index('ix_quiz_responses_session_id', 'quiz_responses', ['session_id'])
    op.create_index('ix_quiz_responses_question_id', 'quiz_responses', ['question_id'])
    op.create_index('ix_quiz_responses_request_id', 'quiz_responses', ['request_id'])

    # Composite indexes for query optimization
    op.create_index('idx_quiz_responses_user_created', 'quiz_responses', ['user_id', 'created_at'])
    op.create_index('idx_quiz_responses_session', 'quiz_responses', ['session_id'])
    op.create_index('idx_quiz_responses_user_question', 'quiz_responses', ['user_id', 'question_id'])
    op.create_index('idx_quiz_responses_request_id', 'quiz_responses', ['request_id'])


def downgrade() -> None:
    op.drop_index('idx_quiz_responses_request_id', table_name='quiz_responses')
    op.drop_index('idx_quiz_responses_user_question', table_name='quiz_responses')
    op.drop_index('idx_quiz_responses_session', table_name='quiz_responses')
    op.drop_index('idx_quiz_responses_user_created', table_name='quiz_responses')
    op.drop_index('ix_quiz_responses_request_id', table_name='quiz_responses')
    op.drop_index('ix_quiz_responses_question_id', table_name='quiz_responses')
    op.drop_index('ix_quiz_responses_session_id', table_name='quiz_responses')
    op.drop_index('ix_quiz_responses_user_id', table_name='quiz_responses')
    op.drop_table('quiz_responses')
