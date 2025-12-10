"""Create reading_chunks table

Revision ID: h8c9d0e1f2g3
Revises: g7b8c9d0e1f2
Create Date: 2025-12-10

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, ARRAY

# revision identifiers, used by Alembic.
revision: str = 'h8c9d0e1f2g3'
down_revision: Union[str, None] = 'g7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create reading_chunks table with multi-course support
    op.create_table(
        'reading_chunks',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('course_id', UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('corpus_section', sa.String(length=50), nullable=False),
        sa.Column('knowledge_area_id', sa.String(length=50), nullable=False),
        sa.Column('concept_ids', ARRAY(UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('estimated_read_time_minutes', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('chunk_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE')
    )

    # Create indexes per schema specification
    op.create_index('idx_reading_chunks_course', 'reading_chunks', ['course_id'])
    op.create_index('idx_reading_chunks_knowledge_area', 'reading_chunks', ['course_id', 'knowledge_area_id'])
    op.create_index('idx_reading_chunks_section', 'reading_chunks', ['corpus_section'])
    op.create_index('idx_reading_chunks_concepts', 'reading_chunks', ['concept_ids'], postgresql_using='gin')

    # Create trigger for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_reading_chunks_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_reading_chunks_updated_at
        BEFORE UPDATE ON reading_chunks
        FOR EACH ROW
        EXECUTE FUNCTION update_reading_chunks_updated_at();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trigger_reading_chunks_updated_at ON reading_chunks")
    op.execute("DROP FUNCTION IF EXISTS update_reading_chunks_updated_at()")
    op.drop_index('idx_reading_chunks_concepts', table_name='reading_chunks', postgresql_using='gin')
    op.drop_index('idx_reading_chunks_section', table_name='reading_chunks')
    op.drop_index('idx_reading_chunks_knowledge_area', table_name='reading_chunks')
    op.drop_index('idx_reading_chunks_course', table_name='reading_chunks')
    op.drop_table('reading_chunks')
