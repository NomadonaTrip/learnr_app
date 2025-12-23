"""Migrate difficulty from 0.0-1.0 to IRT b-parameter scale (-3.0 to +3.0)

Revision ID: q7l8m9n0o1p2
Revises: p6k7l8m9n0o1
Create Date: 2025-12-21

ADR-002: IRT Difficulty Scale Migration
- Adds difficulty_label column for human-readable labels (Easy/Medium/Hard)
- Converts existing difficulty values from legacy 0.0-1.0 to IRT -3.0 to +3.0
- Updates constraint to allow IRT range
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'q7l8m9n0o1p2'
down_revision: str | None = 'p6k7l8m9n0o1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Legacy to IRT conversion mappings
# Legacy values: Easy=0.3, Medium=0.5, Hard=0.7
# IRT values: Easy=-1.5, Medium=0.0, Hard=+1.5
LEGACY_TO_IRT_DISCRETE = {
    0.3: -1.5,   # Easy
    0.5: 0.0,    # Medium
    0.7: 1.5,    # Hard
}


def upgrade() -> None:
    # Step 1: Add difficulty_label column
    op.add_column(
        'questions',
        sa.Column(
            'difficulty_label',
            sa.String(10),
            nullable=True
        )
    )

    # Step 2: Drop the old constraint (0.0-1.0)
    op.drop_constraint('ck_questions_difficulty_range', 'questions', type_='check')

    # Step 3: Convert existing difficulty values to IRT scale and set labels
    # Using raw SQL for data migration
    op.execute("""
        UPDATE questions
        SET
            difficulty_label = CASE
                WHEN difficulty <= 0.35 THEN 'Easy'
                WHEN difficulty <= 0.65 THEN 'Medium'
                ELSE 'Hard'
            END,
            difficulty = CASE
                -- Discrete mappings for known legacy values (with tolerance)
                WHEN ABS(difficulty - 0.3) < 0.05 THEN -1.5
                WHEN ABS(difficulty - 0.5) < 0.05 THEN 0.0
                WHEN ABS(difficulty - 0.7) < 0.05 THEN 1.5
                -- Linear transformation for other values: (d - 0.5) * 6
                ELSE GREATEST(-3.0, LEAST(3.0, (difficulty - 0.5) * 6))
            END
    """)

    # Step 4: Add the new constraint (-3.0 to 3.0)
    op.create_check_constraint(
        'ck_questions_difficulty_range',
        'questions',
        'difficulty >= -3.0 AND difficulty <= 3.0'
    )

    # Step 5: Update the default value for new questions (0.0 = medium)
    op.alter_column(
        'questions',
        'difficulty',
        server_default='0.0'
    )


def downgrade() -> None:
    # Step 1: Drop the IRT constraint
    op.drop_constraint('ck_questions_difficulty_range', 'questions', type_='check')

    # Step 2: Convert IRT values back to legacy 0.0-1.0 scale
    op.execute("""
        UPDATE questions
        SET difficulty = CASE
            -- Discrete mappings for known IRT values (with tolerance)
            WHEN ABS(difficulty - (-1.5)) < 0.1 THEN 0.3
            WHEN ABS(difficulty - 0.0) < 0.1 THEN 0.5
            WHEN ABS(difficulty - 1.5) < 0.1 THEN 0.7
            -- Linear transformation for other values: (b / 6) + 0.5
            ELSE GREATEST(0.0, LEAST(1.0, (difficulty / 6.0) + 0.5))
        END
    """)

    # Step 3: Restore the original constraint (0.0-1.0)
    op.create_check_constraint(
        'ck_questions_difficulty_range',
        'questions',
        'difficulty >= 0.0 AND difficulty <= 1.0'
    )

    # Step 4: Restore original default
    op.alter_column(
        'questions',
        'difficulty',
        server_default='0.5'
    )

    # Step 5: Drop difficulty_label column
    op.drop_column('questions', 'difficulty_label')
