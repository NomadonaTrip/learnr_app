"""Add perspectives and competencies ARRAY columns to questions table

Revision ID: o5j6k7l8m9n0
Revises: n4i5j6k7l8m9
Create Date: 2025-12-19

Story 2.15: Secondary Tagging for Perspectives and Underlying Competencies
Task 2: Question schema for storing classified tags
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision: str = 'o5j6k7l8m9n0'
down_revision: str | None = 'n4i5j6k7l8m9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add perspectives column - ARRAY of strings for perspective IDs
    op.add_column(
        'questions',
        sa.Column(
            'perspectives',
            ARRAY(sa.String()),
            nullable=True,
            server_default='{}'
        )
    )

    # Add competencies column - ARRAY of strings for competency IDs
    op.add_column(
        'questions',
        sa.Column(
            'competencies',
            ARRAY(sa.String()),
            nullable=True,
            server_default='{}'
        )
    )

    # Create GIN indexes for efficient array containment queries
    # GIN indexes are optimal for PostgreSQL array operations like @> (contains)
    op.execute("""
        CREATE INDEX idx_questions_perspectives_gin
        ON questions USING GIN (perspectives)
    """)

    op.execute("""
        CREATE INDEX idx_questions_competencies_gin
        ON questions USING GIN (competencies)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_questions_competencies_gin")
    op.execute("DROP INDEX IF EXISTS idx_questions_perspectives_gin")
    op.drop_column('questions', 'competencies')
    op.drop_column('questions', 'perspectives')
