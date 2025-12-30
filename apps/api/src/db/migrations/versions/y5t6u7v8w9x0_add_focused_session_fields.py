"""Add target_concept_ids column and update session_type CHECK constraint for focused sessions

This migration:
1. Adds target_concept_ids JSONB column for focused_concept sessions
2. Updates session_type CHECK constraint to include 'focused_ka' and 'focused_concept'

Revision ID: y5t6u7v8w9x0
Revises: x4s5t6u7v8w9
Create Date: 2025-12-29

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'y5t6u7v8w9x0'
down_revision: str | None = 'x4s5t6u7v8w9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add target_concept_ids column (JSONB, nullable, default empty array)
    # Stores JSON array of concept UUID strings: ["uuid1", "uuid2", "uuid3"]
    op.add_column(
        'quiz_sessions',
        sa.Column(
            'target_concept_ids',
            JSONB,
            nullable=True,
            server_default='[]'
        )
    )

    # Update session_type CHECK constraint to include new focused session types
    # First drop the existing constraint
    op.drop_constraint('check_quiz_session_type', 'quiz_sessions', type_='check')

    # Then create the updated constraint with new values
    op.create_check_constraint(
        'check_quiz_session_type',
        'quiz_sessions',
        "session_type IN ('diagnostic', 'adaptive', 'focused', 'focused_ka', 'focused_concept', 'review')"
    )


def downgrade() -> None:
    # Revert session_type CHECK constraint
    op.drop_constraint('check_quiz_session_type', 'quiz_sessions', type_='check')
    op.create_check_constraint(
        'check_quiz_session_type',
        'quiz_sessions',
        "session_type IN ('diagnostic', 'adaptive', 'focused', 'review')"
    )

    # Remove target_concept_ids column
    op.drop_column('quiz_sessions', 'target_concept_ids')
