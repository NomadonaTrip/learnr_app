"""Create concept_prerequisites table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2025-12-09

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: str | None = 'd4e5f6a7b8c9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create concept_prerequisites table with composite primary key
    op.create_table(
        'concept_prerequisites',
        sa.Column('concept_id', UUID(as_uuid=True), nullable=False),
        sa.Column('prerequisite_concept_id', UUID(as_uuid=True), nullable=False),
        sa.Column('strength', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('relationship_type', sa.String(length=20), nullable=False, server_default="'required'"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        # Composite primary key
        sa.PrimaryKeyConstraint('concept_id', 'prerequisite_concept_id'),
        # Foreign key constraints with CASCADE delete
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prerequisite_concept_id'], ['concepts.id'], ondelete='CASCADE'),
        # Check constraints
        sa.CheckConstraint('concept_id != prerequisite_concept_id', name='ck_no_self_loop'),
        sa.CheckConstraint('strength >= 0.0 AND strength <= 1.0', name='ck_strength_range'),
        sa.CheckConstraint(
            "relationship_type IN ('required', 'helpful', 'related')",
            name='ck_valid_relationship_type'
        ),
    )

    # Create indexes for efficient lookups
    op.create_index(
        'idx_concept_prereqs_concept',
        'concept_prerequisites',
        ['concept_id']
    )
    op.create_index(
        'idx_concept_prereqs_prereq',
        'concept_prerequisites',
        ['prerequisite_concept_id']
    )


def downgrade() -> None:
    op.drop_index('idx_concept_prereqs_prereq', table_name='concept_prerequisites')
    op.drop_index('idx_concept_prereqs_concept', table_name='concept_prerequisites')
    op.drop_table('concept_prerequisites')
