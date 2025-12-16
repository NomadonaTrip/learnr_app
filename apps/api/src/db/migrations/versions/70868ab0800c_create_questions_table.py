"""create_questions_table

Revision ID: 70868ab0800c
Revises: aa32538830f9
Create Date: 2025-11-26 22:33:46.863444

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = '70868ab0800c'
down_revision: str | None = 'aa32538830f9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create questions table
    op.create_table(
        'questions',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('option_a', sa.Text(), nullable=False),
        sa.Column('option_b', sa.Text(), nullable=False),
        sa.Column('option_c', sa.Text(), nullable=False),
        sa.Column('option_d', sa.Text(), nullable=False),
        sa.Column('correct_answer', sa.String(length=1), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('ka', sa.String(length=100), nullable=False),
        sa.Column('difficulty', sa.String(length=20), nullable=False),
        sa.Column('concept_tags', JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='vendor'),
        sa.Column('babok_reference', sa.String(length=100), nullable=True),
        sa.Column('times_seen', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_correct_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("correct_answer IN ('A', 'B', 'C', 'D')", name='check_correct_answer'),
        sa.CheckConstraint("difficulty IN ('Easy', 'Medium', 'Hard')", name='check_difficulty'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_questions_ka', 'questions', ['ka'])
    op.create_index('idx_questions_difficulty', 'questions', ['difficulty'])
    op.create_index('idx_questions_source', 'questions', ['source'])
    op.create_index('idx_questions_concept_tags', 'questions', ['concept_tags'], postgresql_using='gin')


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_questions_concept_tags', table_name='questions')
    op.drop_index('idx_questions_source', table_name='questions')
    op.drop_index('idx_questions_difficulty', table_name='questions')
    op.drop_index('idx_questions_ka', table_name='questions')

    # Drop table
    op.drop_table('questions')
