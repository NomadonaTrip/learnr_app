"""Create courses table

Revision ID: a1b2c3d4e5f6
Revises: e1edd6b1edb2
Create Date: 2025-12-09

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = 'e1edd6b1edb2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create courses table
    op.create_table(
        'courses',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('corpus_name', sa.String(length=100), nullable=True),
        sa.Column('knowledge_areas', JSONB(), nullable=False),
        sa.Column('default_diagnostic_count', sa.Integer(), nullable=False, server_default='12'),
        sa.Column('mastery_threshold', sa.Float(), nullable=False, server_default='0.8'),
        sa.Column('gap_threshold', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('confidence_threshold', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('icon_url', sa.String(length=500), nullable=True),
        sa.Column('color_hex', sa.String(length=7), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_courses_slug', 'courses', ['slug'], unique=True)
    op.create_index(
        'idx_courses_active',
        'courses',
        ['is_active'],
        postgresql_where=sa.text('is_active = TRUE')
    )


def downgrade() -> None:
    op.drop_index('idx_courses_active', table_name='courses')
    op.drop_index('idx_courses_slug', table_name='courses')
    op.drop_table('courses')
