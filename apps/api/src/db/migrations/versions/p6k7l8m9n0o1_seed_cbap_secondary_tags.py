"""Seed CBAP course perspectives and competencies

Revision ID: p6k7l8m9n0o1
Revises: o5j6k7l8m9n0
Create Date: 2025-12-19

Story 2.15: Secondary Tagging for Perspectives and Underlying Competencies
Task 3: Seed CBAP course with BABOK Chapter 9 competencies and Chapter 10 perspectives
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'p6k7l8m9n0o1'
down_revision: str | None = 'o5j6k7l8m9n0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# BABOK Chapter 10 - Perspectives
# Story 2.16: Added primary_ka field for non-conventional KA mapping
CBAP_PERSPECTIVES = '''[
    {
        "id": "agile",
        "name": "Agile",
        "primary_ka": "strategy",
        "keywords": ["agile", "scrum", "kanban", "iterative", "adaptive", "sprint", "backlog"]
    },
    {
        "id": "bi",
        "name": "Business Intelligence",
        "primary_ka": "solution-eval",
        "keywords": ["bi", "business-intelligence", "analytics", "reporting", "data-warehouse", "dashboard"]
    },
    {
        "id": "it",
        "name": "Information Technology",
        "primary_ka": "radd",
        "keywords": ["it", "information-technology", "software", "systems", "technical", "development"]
    },
    {
        "id": "bpm",
        "name": "Business Process Management",
        "primary_ka": "radd",
        "keywords": ["bpm", "business-process", "process-improvement", "workflow", "process-modeling"]
    },
    {
        "id": "ba",
        "name": "Business Architecture",
        "primary_ka": "strategy",
        "keywords": ["business-architecture", "capability", "value-stream"]
    }
]'''

# BABOK Chapter 9 - Underlying Competencies
CBAP_COMPETENCIES = '''[
    {
        "id": "analytical",
        "name": "Analytical Thinking and Problem Solving",
        "keywords": ["analytical", "problem-solving", "critical-thinking", "decision-making", "systems-thinking", "conceptual-thinking"]
    },
    {
        "id": "behavioral",
        "name": "Behavioral Characteristics",
        "keywords": ["behavioral", "behavioural", "adaptability", "ethics", "trustworthiness", "personal-accountability", "organization"]
    },
    {
        "id": "business-knowledge",
        "name": "Business Knowledge",
        "keywords": ["business-knowledge", "industry", "organization", "methodology", "solution-knowledge", "business-acumen"]
    },
    {
        "id": "communication",
        "name": "Communication Skills",
        "keywords": ["communication", "verbal", "written", "listening", "non-verbal", "presentation"]
    },
    {
        "id": "interaction",
        "name": "Interaction Skills",
        "keywords": ["interaction", "facilitation", "leadership", "negotiation", "conflict-resolution", "teamwork", "teaching"]
    },
    {
        "id": "tools-tech",
        "name": "Tools and Technology",
        "keywords": ["tools-and-technology", "tools", "technology", "software-applications", "office-productivity", "ba-tools"]
    }
]'''


def upgrade() -> None:
    # Update CBAP course with perspectives and competencies
    op.execute(
        sa.text("""
            UPDATE courses
            SET
                perspectives = :perspectives ::JSONB,
                competencies = :competencies ::JSONB
            WHERE slug = 'cbap'
        """).bindparams(
            sa.bindparam('perspectives', value=CBAP_PERSPECTIVES, type_=sa.Text),
            sa.bindparam('competencies', value=CBAP_COMPETENCIES, type_=sa.Text)
        )
    )


def downgrade() -> None:
    # Clear perspectives and competencies from CBAP course
    op.execute(
        sa.text("""
            UPDATE courses
            SET
                perspectives = NULL,
                competencies = NULL
            WHERE slug = 'cbap'
        """)
    )
