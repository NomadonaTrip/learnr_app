"""Add initialize_beliefs_with_prior database function

Revision ID: r8m9n0o1p2q3
Revises: q7l8m9n0o1p2
Create Date: 2025-12-24

Story 3.4.1: Familiarity-Based Belief Prior Integration
- Creates new DB function that accepts alpha/beta parameters
- Used for setting initial belief priors based on user's declared familiarity
- Keeps existing initialize_beliefs() function for backward compatibility
"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'r8m9n0o1p2q3'
down_revision: str | None = 'q7l8m9n0o1p2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create new database function for belief initialization with custom prior
    # This function accepts alpha/beta parameters to set initial belief states
    # based on user's declared familiarity level from onboarding
    op.execute("""
        CREATE OR REPLACE FUNCTION initialize_beliefs_with_prior(
            p_user_id UUID,
            p_course_id UUID,
            p_alpha FLOAT,
            p_beta FLOAT
        )
        RETURNS INTEGER AS $$
        DECLARE
            inserted_count INTEGER;
        BEGIN
            -- Validate alpha/beta constraints
            IF p_alpha <= 0 OR p_beta <= 0 THEN
                RAISE EXCEPTION 'alpha and beta must be positive, got alpha=%, beta=%', p_alpha, p_beta;
            END IF;

            -- Insert belief states for all concepts in the specified course
            -- Uses ON CONFLICT DO NOTHING for idempotency
            INSERT INTO belief_states (user_id, concept_id, alpha, beta)
            SELECT p_user_id, c.id, p_alpha, p_beta
            FROM concepts c
            WHERE c.course_id = p_course_id
            ON CONFLICT (user_id, concept_id) DO NOTHING;

            GET DIAGNOSTICS inserted_count = ROW_COUNT;
            RETURN inserted_count;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS initialize_beliefs_with_prior(UUID, UUID, FLOAT, FLOAT)")
