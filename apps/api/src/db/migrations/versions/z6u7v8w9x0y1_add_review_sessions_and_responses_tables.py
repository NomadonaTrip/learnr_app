"""Add review_sessions and review_responses tables

Revision ID: z6u7v8w9x0y1
Revises: y5t6u7v8w9x0
Create Date: 2025-12-30

Story 4.9: Post-Session Review Mode
Creates review_sessions and review_responses tables for post-quiz
review functionality where users re-answer incorrect questions.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = 'z6u7v8w9x0y1'
down_revision: str | None = 'y5t6u7v8w9x0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create review_sessions table
    op.create_table(
        'review_sessions',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('original_session_id', UUID(as_uuid=True), nullable=False),
        sa.Column('question_ids', JSONB, nullable=False),
        sa.Column('total_to_review', sa.Integer(), nullable=False),
        sa.Column('reviewed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reinforced_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('still_incorrect_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['original_session_id'], ['quiz_sessions.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'skipped')",
            name='check_review_session_status'
        ),
    )

    # Create indexes for review_sessions
    op.create_index('idx_review_sessions_user', 'review_sessions', ['user_id'])
    op.create_index('idx_review_sessions_original', 'review_sessions', ['original_session_id'])
    op.create_index('idx_review_sessions_status', 'review_sessions', ['status'])

    # Create review_responses table
    op.create_table(
        'review_responses',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('review_session_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', UUID(as_uuid=True), nullable=False),
        sa.Column('original_response_id', UUID(as_uuid=True), nullable=False),
        sa.Column('selected_answer', sa.String(length=1), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('was_reinforced', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('belief_updates', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['review_session_id'], ['review_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['original_response_id'], ['quiz_responses.id']),
        sa.CheckConstraint(
            "selected_answer IN ('A', 'B', 'C', 'D')",
            name='ck_review_responses_selected_answer'
        ),
    )

    # Create indexes for review_responses
    op.create_index('idx_review_responses_session', 'review_responses', ['review_session_id'])
    op.create_index('idx_review_responses_user', 'review_responses', ['user_id'])


def downgrade() -> None:
    # Drop review_responses indexes and table first (FK dependency)
    op.drop_index('idx_review_responses_user', table_name='review_responses')
    op.drop_index('idx_review_responses_session', table_name='review_responses')
    op.drop_table('review_responses')

    # Drop review_sessions indexes and table
    op.drop_index('idx_review_sessions_status', table_name='review_sessions')
    op.drop_index('idx_review_sessions_original', table_name='review_sessions')
    op.drop_index('idx_review_sessions_user', table_name='review_sessions')
    op.drop_table('review_sessions')
