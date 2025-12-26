"""Create reading_queue table

Revision ID: v2q3r4s5t6u7
Revises: u1p2q3r4s5t6
Create Date: 2025-12-25

Story 5.5: Background Reading Queue Population
Creates reading_queue table for storing user's queued reading materials
triggered by quiz answer submissions.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'v2q3r4s5t6u7'
down_revision: str | None = 'u1p2q3r4s5t6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create reading_queue table
    op.create_table(
        'reading_queue',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('enrollment_id', UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_id', UUID(as_uuid=True), nullable=False),
        sa.Column('triggered_by_question_id', UUID(as_uuid=True), nullable=True),
        sa.Column('triggered_by_concept_id', UUID(as_uuid=True), nullable=True),
        sa.Column('priority', sa.String(length=10), nullable=False, server_default='Medium'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='unread'),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('times_opened', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_reading_time_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chunk_id'], ['reading_chunks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by_question_id'], ['questions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['triggered_by_concept_id'], ['concepts.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('enrollment_id', 'chunk_id', name='uq_reading_queue_enrollment_chunk'),
        sa.CheckConstraint("priority IN ('High', 'Medium', 'Low')", name='check_reading_queue_priority'),
        sa.CheckConstraint("status IN ('unread', 'reading', 'completed', 'dismissed')", name='check_reading_queue_status'),
    )

    # Create indexes for efficient queries
    op.create_index('idx_reading_queue_user', 'reading_queue', ['user_id'])
    op.create_index('idx_reading_queue_enrollment', 'reading_queue', ['enrollment_id'])
    op.create_index('idx_reading_queue_enrollment_status', 'reading_queue', ['enrollment_id', 'status'])
    op.create_index('idx_reading_queue_priority', 'reading_queue', ['enrollment_id', sa.text('priority DESC'), 'added_at'])


def downgrade() -> None:
    op.drop_index('idx_reading_queue_priority', table_name='reading_queue')
    op.drop_index('idx_reading_queue_enrollment_status', table_name='reading_queue')
    op.drop_index('idx_reading_queue_enrollment', table_name='reading_queue')
    op.drop_index('idx_reading_queue_user', table_name='reading_queue')
    op.drop_table('reading_queue')
