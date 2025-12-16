"""Seed CBAP course data

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-12-09

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: str | None = 'b2c3d4e5f6a7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# CBAP course seed data
CBAP_KNOWLEDGE_AREAS = '''[
    {"id": "ba-planning", "name": "Business Analysis Planning and Monitoring", "short_name": "BA Planning", "display_order": 1, "color": "#3B82F6"},
    {"id": "elicitation", "name": "Elicitation and Collaboration", "short_name": "Elicitation", "display_order": 2, "color": "#10B981"},
    {"id": "rlcm", "name": "Requirements Life Cycle Management", "short_name": "RLCM", "display_order": 3, "color": "#F59E0B"},
    {"id": "strategy", "name": "Strategy Analysis", "short_name": "Strategy", "display_order": 4, "color": "#EF4444"},
    {"id": "radd", "name": "Requirements Analysis and Design Definition", "short_name": "RADD", "display_order": 5, "color": "#8B5CF6"},
    {"id": "solution-eval", "name": "Solution Evaluation", "short_name": "Solution Eval", "display_order": 6, "color": "#EC4899"}
]'''


def upgrade() -> None:
    # Insert CBAP course with ON CONFLICT DO NOTHING for idempotency
    op.execute(
        sa.text("""
            INSERT INTO courses (slug, name, description, corpus_name, knowledge_areas)
            VALUES (
                'cbap',
                'CBAP Certification Prep',
                'Comprehensive preparation course for the Certified Business Analysis Professional (CBAP) certification exam based on BABOK v3.',
                'BABOK v3',
                :knowledge_areas ::JSONB
            )
            ON CONFLICT (slug) DO NOTHING
        """).bindparams(sa.bindparam('knowledge_areas', value=CBAP_KNOWLEDGE_AREAS, type_=sa.Text))
    )


def downgrade() -> None:
    # Remove CBAP course
    op.execute(
        sa.text("DELETE FROM courses WHERE slug = 'cbap'")
    )
