"""Create concepts table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2025-12-09

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: str | None = 'c3d4e5f6a7b8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create concepts table with multi-course support
    op.create_table(
        'concepts',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('course_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('corpus_section_ref', sa.String(length=50), nullable=True),
        sa.Column('knowledge_area_id', sa.String(length=50), nullable=False),
        sa.Column('difficulty_estimate', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('prerequisite_depth', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE')
    )

    # Create indexes per schema specification
    op.create_index('idx_concepts_course', 'concepts', ['course_id'])
    op.create_index('idx_concepts_knowledge_area', 'concepts', ['course_id', 'knowledge_area_id'])
    op.create_index('idx_concepts_section', 'concepts', ['corpus_section_ref'])


def downgrade() -> None:
    op.drop_index('idx_concepts_section', table_name='concepts')
    op.drop_index('idx_concepts_knowledge_area', table_name='concepts')
    op.drop_index('idx_concepts_course', table_name='concepts')
    op.drop_table('concepts')
