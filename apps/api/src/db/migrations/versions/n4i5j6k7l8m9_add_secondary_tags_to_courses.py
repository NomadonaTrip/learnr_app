"""Add perspectives and competencies JSONB columns to courses table

Revision ID: n4i5j6k7l8m9
Revises: m3h4i5j6k7l8
Create Date: 2025-12-19

Story 2.15: Secondary Tagging for Perspectives and Underlying Competencies
Task 1: Course schema for course-configurable keyword definitions
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'n4i5j6k7l8m9'
down_revision: str | None = 'm3h4i5j6k7l8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add perspectives column - JSONB array of perspective definitions
    # Each element: {"id": str, "name": str, "keywords": [str]}
    op.add_column(
        'courses',
        sa.Column(
            'perspectives',
            JSONB,
            nullable=True
        )
    )

    # Add competencies column - JSONB array of competency definitions
    # Each element: {"id": str, "name": str, "keywords": [str]}
    op.add_column(
        'courses',
        sa.Column(
            'competencies',
            JSONB,
            nullable=True
        )
    )


def downgrade() -> None:
    op.drop_column('courses', 'competencies')
    op.drop_column('courses', 'perspectives')
