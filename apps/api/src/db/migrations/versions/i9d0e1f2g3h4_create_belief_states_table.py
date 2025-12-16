"""Create belief_states table

Revision ID: i9d0e1f2g3h4
Revises: h8c9d0e1f2g3
Create Date: 2025-12-14

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'i9d0e1f2g3h4'
down_revision: str | None = 'h8c9d0e1f2g3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create belief_states table for BKT (Bayesian Knowledge Tracing)
    op.create_table(
        'belief_states',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('concept_id', UUID(as_uuid=True), nullable=False),
        sa.Column('alpha', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('beta', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('last_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.CheckConstraint('alpha > 0', name='check_belief_alpha_positive'),
        sa.CheckConstraint('beta > 0', name='check_belief_beta_positive'),
    )

    # Create indexes per schema specification
    # Unique constraint on (user_id, concept_id)
    op.create_index(
        'uq_belief_states_user_concept',
        'belief_states',
        ['user_id', 'concept_id'],
        unique=True
    )
    # Performance indexes
    op.create_index('idx_belief_states_user', 'belief_states', ['user_id'])
    op.create_index('idx_belief_states_updated', 'belief_states', ['updated_at'])

    # Create trigger for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_belief_states_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_belief_states_updated_at
        BEFORE UPDATE ON belief_states
        FOR EACH ROW
        EXECUTE FUNCTION update_belief_states_updated_at();
    """)

    # Create database function for bulk belief initialization (idempotent)
    op.execute("""
        CREATE OR REPLACE FUNCTION initialize_beliefs(p_user_id UUID)
        RETURNS INTEGER AS $$
        DECLARE
            inserted_count INTEGER;
        BEGIN
            INSERT INTO belief_states (user_id, concept_id, alpha, beta)
            SELECT p_user_id, id, 1.0, 1.0
            FROM concepts
            ON CONFLICT (user_id, concept_id) DO NOTHING;

            GET DIAGNOSTICS inserted_count = ROW_COUNT;
            RETURN inserted_count;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS initialize_beliefs(UUID)")
    op.execute("DROP TRIGGER IF EXISTS trigger_belief_states_updated_at ON belief_states")
    op.execute("DROP FUNCTION IF EXISTS update_belief_states_updated_at()")
    op.drop_index('idx_belief_states_updated', table_name='belief_states')
    op.drop_index('idx_belief_states_user', table_name='belief_states')
    op.drop_index('uq_belief_states_user_concept', table_name='belief_states')
    op.drop_table('belief_states')
