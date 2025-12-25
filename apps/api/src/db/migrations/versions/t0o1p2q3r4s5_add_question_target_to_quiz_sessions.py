"""Add question_target column to quiz_sessions table

Revision ID: t0o1p2q3r4s5
Revises: s9n0o1p2q3r4
Create Date: 2025-12-24

Story 4.1/4.7: Fixed-length quiz sessions with configurable question target.
Default is 10 for habit-forming consistency (Duolingo-style sessions).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 't0o1p2q3r4s5'
down_revision: str | None = 's9n0o1p2q3r4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add question_target column with default of 10 for habit-forming consistency
    # Per Story 4.1 v2.3 changelog: fixed default of 10, configurable for future optimization
    op.add_column(
        'quiz_sessions',
        sa.Column('question_target', sa.Integer(), nullable=False, server_default='10')
    )

    # Add CHECK constraint: question_target must be between 10 and 15
    op.create_check_constraint(
        'check_quiz_session_question_target',
        'quiz_sessions',
        'question_target BETWEEN 10 AND 15'
    )


def downgrade() -> None:
    # Remove CHECK constraint first
    op.drop_constraint('check_quiz_session_question_target', 'quiz_sessions', type_='check')

    # Remove column
    op.drop_column('quiz_sessions', 'question_target')
