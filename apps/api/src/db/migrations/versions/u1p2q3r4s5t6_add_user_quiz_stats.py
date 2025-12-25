"""Add user quiz statistics columns

Revision ID: u1p2q3r4s5t6
Revises: t0o1p2q3r4s5
Create Date: 2025-12-24

Story 4.7: Fixed-Length Session Auto-Completion
Adds lifetime quiz statistics tracking to users table:
- quizzes_completed: Count of completed quiz sessions
- total_questions_answered: Lifetime question count
- total_time_spent_seconds: Cumulative study time
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'u1p2q3r4s5t6'
down_revision: str | None = 't0o1p2q3r4s5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add quizzes_completed column
    op.add_column(
        'users',
        sa.Column('quizzes_completed', sa.Integer(), nullable=False, server_default='0')
    )

    # Add total_questions_answered column
    op.add_column(
        'users',
        sa.Column('total_questions_answered', sa.Integer(), nullable=False, server_default='0')
    )

    # Add total_time_spent_seconds column
    op.add_column(
        'users',
        sa.Column('total_time_spent_seconds', sa.Integer(), nullable=False, server_default='0')
    )

    # Add CHECK constraints for non-negative values
    op.create_check_constraint(
        'check_quizzes_completed_non_negative',
        'users',
        'quizzes_completed >= 0'
    )
    op.create_check_constraint(
        'check_total_questions_answered_non_negative',
        'users',
        'total_questions_answered >= 0'
    )
    op.create_check_constraint(
        'check_total_time_spent_seconds_non_negative',
        'users',
        'total_time_spent_seconds >= 0'
    )


def downgrade() -> None:
    # Remove CHECK constraints first
    op.drop_constraint('check_total_time_spent_seconds_non_negative', 'users', type_='check')
    op.drop_constraint('check_total_questions_answered_non_negative', 'users', type_='check')
    op.drop_constraint('check_quizzes_completed_non_negative', 'users', type_='check')

    # Remove columns
    op.drop_column('users', 'total_time_spent_seconds')
    op.drop_column('users', 'total_questions_answered')
    op.drop_column('users', 'quizzes_completed')
