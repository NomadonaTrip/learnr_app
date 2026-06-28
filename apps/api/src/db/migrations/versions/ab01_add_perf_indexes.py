"""add performance indexes: questions(course_id, difficulty_label), review_responses(question_id)

Two indexes the DB lacked but queries want:
- idx_questions_difficulty_label: difficulty-tier question selection (Story 10.1 IRT)
- idx_review_responses_question: FK lookup / joins on review_responses.question_id

Revision ID: ab01perfindexes
Revises: aa01questionstz
Create Date: 2026-06-28
"""
from alembic import op

revision = "ab01perfindexes"
down_revision = "aa01questionstz"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_questions_difficulty_label",
        "questions",
        ["course_id", "difficulty_label"],
    )
    op.create_index(
        "idx_review_responses_question",
        "review_responses",
        ["question_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_review_responses_question", table_name="review_responses")
    op.drop_index("idx_questions_difficulty_label", table_name="questions")
