"""Create concept_unlock_events table for Story 4.11

Revision ID: s9n0o1p2q3r4
Revises: r8m9n0o1p2q3
Create Date: 2025-12-24

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 's9n0o1p2q3r4'
down_revision: str | None = 'r8m9n0o1p2q3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create concept_unlock_events table for tracking when concepts are unlocked
    # Story 4.11: Prerequisite-Based Curriculum Navigation
    op.create_table(
        'concept_unlock_events',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('concept_id', UUID(as_uuid=True), nullable=False),
        sa.Column('prerequisite_concept_id', UUID(as_uuid=True), nullable=True),  # Which prereq triggered unlock
        sa.Column('unlocked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prerequisite_concept_id'], ['concepts.id'], ondelete='SET NULL'),
    )

    # Create indexes for efficient querying
    op.create_index('idx_unlock_events_user', 'concept_unlock_events', ['user_id'])
    op.create_index('idx_unlock_events_user_concept', 'concept_unlock_events', ['user_id', 'concept_id'])
    op.create_index('idx_unlock_events_unlocked_at', 'concept_unlock_events', ['unlocked_at'])

    # Unique constraint: a concept can only be unlocked once per user
    op.create_index(
        'uq_unlock_events_user_concept',
        'concept_unlock_events',
        ['user_id', 'concept_id'],
        unique=True
    )


def downgrade() -> None:
    op.drop_index('uq_unlock_events_user_concept', table_name='concept_unlock_events')
    op.drop_index('idx_unlock_events_unlocked_at', table_name='concept_unlock_events')
    op.drop_index('idx_unlock_events_user_concept', table_name='concept_unlock_events')
    op.drop_index('idx_unlock_events_user', table_name='concept_unlock_events')
    op.drop_table('concept_unlock_events')
