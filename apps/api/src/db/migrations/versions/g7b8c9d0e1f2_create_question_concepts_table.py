"""Create question_concepts junction table

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2025-12-10

Creates the question_concepts junction table for many-to-many relationship
between questions and concepts. Each question can map to 1-5 concepts with
a relevance score indicating how directly the question tests that concept.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'g7b8c9d0e1f2'
down_revision: str | None = 'f6a7b8c9d0e1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create question_concepts junction table
    op.create_table(
        'question_concepts',
        sa.Column('question_id', UUID(as_uuid=True), nullable=False),
        sa.Column('concept_id', UUID(as_uuid=True), nullable=False),
        sa.Column('relevance', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        # Composite primary key
        sa.PrimaryKeyConstraint('question_id', 'concept_id'),
        # Foreign key constraints with CASCADE delete
        sa.ForeignKeyConstraint(
            ['question_id'], ['questions.id'],
            name='fk_question_concepts_question',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['concept_id'], ['concepts.id'],
            name='fk_question_concepts_concept',
            ondelete='CASCADE'
        ),
        # Check constraint for relevance range
        sa.CheckConstraint(
            'relevance >= 0.0 AND relevance <= 1.0',
            name='ck_question_concepts_relevance_range'
        ),
    )

    # Create indexes for efficient lookups
    op.create_index(
        'idx_question_concepts_question',
        'question_concepts',
        ['question_id']
    )
    op.create_index(
        'idx_question_concepts_concept',
        'question_concepts',
        ['concept_id']
    )


def downgrade() -> None:
    op.drop_index('idx_question_concepts_concept', table_name='question_concepts')
    op.drop_index('idx_question_concepts_question', table_name='question_concepts')
    op.drop_table('question_concepts')
