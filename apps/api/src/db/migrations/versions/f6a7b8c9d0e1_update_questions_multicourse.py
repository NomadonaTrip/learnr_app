"""Update questions table for multi-course support

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2025-12-10

This migration updates the questions table to support multi-course architecture:
- Adds course_id FK
- Renames ka -> knowledge_area_id
- Renames babok_reference -> corpus_reference
- Converts separate option columns to JSONB options
- Changes difficulty from string to float
- Adds IRT parameters (discrimination, guess_rate, slip_rate)
- Adds is_active column
- Updates indexes for course-scoped queries
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: str | None = 'e5f6a7b8c9d0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Knowledge area mapping from old string names to new IDs
KA_NAME_TO_ID = {
    'Business Analysis Planning and Monitoring': 'ba-planning',
    'Elicitation and Collaboration': 'elicitation',
    'Requirements Life Cycle Management': 'rlcm',
    'Strategy Analysis': 'strategy',
    'Requirements Analysis and Design Definition': 'radd',
    'Solution Evaluation': 'solution-eval',
}

# Difficulty mapping from string to float
DIFFICULTY_TO_FLOAT = {
    'Easy': 0.3,
    'Medium': 0.5,
    'Hard': 0.7,
}


def upgrade() -> None:
    # Get CBAP course ID for existing questions
    conn = op.get_bind()

    # 1. Add new columns
    op.add_column('questions', sa.Column('course_id', UUID(as_uuid=True), nullable=True))
    op.add_column('questions', sa.Column('knowledge_area_id', sa.String(50), nullable=True))
    op.add_column('questions', sa.Column('corpus_reference', sa.String(100), nullable=True))
    op.add_column('questions', sa.Column('options', JSONB, nullable=True))
    op.add_column('questions', sa.Column('difficulty_float', sa.Float(), nullable=True))
    op.add_column('questions', sa.Column('discrimination', sa.Float(), nullable=False, server_default='1.0'))
    op.add_column('questions', sa.Column('guess_rate', sa.Float(), nullable=False, server_default='0.25'))
    op.add_column('questions', sa.Column('slip_rate', sa.Float(), nullable=False, server_default='0.10'))
    op.add_column('questions', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('questions', sa.Column('times_asked', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('questions', sa.Column('times_correct', sa.Integer(), nullable=False, server_default='0'))

    # 2. Get CBAP course_id
    result = conn.execute(sa.text("SELECT id FROM courses WHERE slug = 'cbap' LIMIT 1"))
    row = result.fetchone()
    cbap_course_id = row[0] if row else None

    if cbap_course_id:
        # 3. Migrate existing data

        # Set course_id for all existing questions to CBAP
        conn.execute(
            sa.text("UPDATE questions SET course_id = :course_id"),
            {"course_id": cbap_course_id}
        )

        # Map ka names to knowledge_area_id
        for old_name, new_id in KA_NAME_TO_ID.items():
            conn.execute(
                sa.text("UPDATE questions SET knowledge_area_id = :new_id WHERE ka = :old_name"),
                {"new_id": new_id, "old_name": old_name}
            )

        # Map difficulty strings to floats
        for old_diff, new_diff in DIFFICULTY_TO_FLOAT.items():
            conn.execute(
                sa.text("UPDATE questions SET difficulty_float = :new_diff WHERE difficulty = :old_diff"),
                {"new_diff": new_diff, "old_diff": old_diff}
            )

        # Convert options from separate columns to JSONB
        conn.execute(sa.text("""
            UPDATE questions
            SET options = jsonb_build_object(
                'A', option_a,
                'B', option_b,
                'C', option_c,
                'D', option_d
            )
        """))

        # Copy babok_reference to corpus_reference
        conn.execute(sa.text("""
            UPDATE questions
            SET corpus_reference = babok_reference
        """))

        # Copy times_seen to times_asked
        conn.execute(sa.text("""
            UPDATE questions
            SET times_asked = times_seen
        """))

    # 4. Make course_id NOT NULL after data migration
    op.alter_column('questions', 'course_id', nullable=False)
    op.alter_column('questions', 'knowledge_area_id', nullable=False)
    op.alter_column('questions', 'options', nullable=False)
    op.alter_column('questions', 'difficulty_float', nullable=False)

    # 5. Drop old columns
    op.drop_constraint('check_difficulty', 'questions', type_='check')
    op.drop_index('idx_questions_ka', table_name='questions')
    op.drop_index('idx_questions_difficulty', table_name='questions')
    op.drop_index('idx_questions_source', table_name='questions')
    op.drop_index('idx_questions_concept_tags', table_name='questions')

    op.drop_column('questions', 'option_a')
    op.drop_column('questions', 'option_b')
    op.drop_column('questions', 'option_c')
    op.drop_column('questions', 'option_d')
    op.drop_column('questions', 'ka')
    op.drop_column('questions', 'difficulty')
    op.drop_column('questions', 'babok_reference')
    op.drop_column('questions', 'times_seen')
    op.drop_column('questions', 'avg_correct_rate')
    op.drop_column('questions', 'concept_tags')

    # 6. Rename difficulty_float to difficulty
    op.alter_column('questions', 'difficulty_float', new_column_name='difficulty')

    # 7. Add new constraints
    op.create_foreign_key(
        'fk_questions_course',
        'questions', 'courses',
        ['course_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_check_constraint(
        'ck_questions_difficulty_range',
        'questions',
        'difficulty >= 0.0 AND difficulty <= 1.0'
    )

    op.create_check_constraint(
        'ck_questions_guess_rate_range',
        'questions',
        'guess_rate >= 0.0 AND guess_rate <= 1.0'
    )

    op.create_check_constraint(
        'ck_questions_slip_rate_range',
        'questions',
        'slip_rate >= 0.0 AND slip_rate <= 1.0'
    )

    # 8. Create new indexes
    op.create_index('idx_questions_course', 'questions', ['course_id'])
    op.create_index('idx_questions_course_ka', 'questions', ['course_id', 'knowledge_area_id'])
    op.create_index('idx_questions_difficulty', 'questions', ['difficulty'])
    op.create_index('idx_questions_active', 'questions', ['is_active'], postgresql_where=sa.text('is_active = true'))


def downgrade() -> None:
    # Drop new indexes
    op.drop_index('idx_questions_active', table_name='questions')
    op.drop_index('idx_questions_difficulty', table_name='questions')
    op.drop_index('idx_questions_course_ka', table_name='questions')
    op.drop_index('idx_questions_course', table_name='questions')

    # Drop new constraints
    op.drop_constraint('ck_questions_slip_rate_range', 'questions', type_='check')
    op.drop_constraint('ck_questions_guess_rate_range', 'questions', type_='check')
    op.drop_constraint('ck_questions_difficulty_range', 'questions', type_='check')
    op.drop_constraint('fk_questions_course', 'questions', type_='foreignkey')

    # Rename difficulty back
    op.alter_column('questions', 'difficulty', new_column_name='difficulty_float')

    # Re-add old columns
    op.add_column('questions', sa.Column('concept_tags', JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False))
    op.add_column('questions', sa.Column('avg_correct_rate', sa.Float(), server_default='0.0', nullable=False))
    op.add_column('questions', sa.Column('times_seen', sa.Integer(), server_default='0', nullable=False))
    op.add_column('questions', sa.Column('babok_reference', sa.String(100), nullable=True))
    op.add_column('questions', sa.Column('difficulty', sa.String(20), nullable=True))
    op.add_column('questions', sa.Column('ka', sa.String(100), nullable=True))
    op.add_column('questions', sa.Column('option_d', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('option_c', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('option_b', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('option_a', sa.Text(), nullable=True))

    # Migrate data back
    conn = op.get_bind()

    # Map knowledge_area_id back to ka names
    id_to_name = {v: k for k, v in KA_NAME_TO_ID.items()}
    for new_id, old_name in id_to_name.items():
        conn.execute(
            sa.text("UPDATE questions SET ka = :old_name WHERE knowledge_area_id = :new_id"),
            {"old_name": old_name, "new_id": new_id}
        )

    # Map difficulty floats back to strings
    conn.execute(sa.text("UPDATE questions SET difficulty = 'Easy' WHERE difficulty_float <= 0.4"))
    conn.execute(sa.text("UPDATE questions SET difficulty = 'Medium' WHERE difficulty_float > 0.4 AND difficulty_float <= 0.6"))
    conn.execute(sa.text("UPDATE questions SET difficulty = 'Hard' WHERE difficulty_float > 0.6"))

    # Convert options JSONB back to separate columns
    conn.execute(sa.text("""
        UPDATE questions
        SET option_a = options->>'A',
            option_b = options->>'B',
            option_c = options->>'C',
            option_d = options->>'D'
    """))

    conn.execute(sa.text("UPDATE questions SET babok_reference = corpus_reference"))
    conn.execute(sa.text("UPDATE questions SET times_seen = times_asked"))

    # Make columns NOT NULL
    op.alter_column('questions', 'ka', nullable=False)
    op.alter_column('questions', 'difficulty', nullable=False)
    op.alter_column('questions', 'option_a', nullable=False)
    op.alter_column('questions', 'option_b', nullable=False)
    op.alter_column('questions', 'option_c', nullable=False)
    op.alter_column('questions', 'option_d', nullable=False)

    # Drop new columns
    op.drop_column('questions', 'times_correct')
    op.drop_column('questions', 'times_asked')
    op.drop_column('questions', 'is_active')
    op.drop_column('questions', 'slip_rate')
    op.drop_column('questions', 'guess_rate')
    op.drop_column('questions', 'discrimination')
    op.drop_column('questions', 'difficulty_float')
    op.drop_column('questions', 'options')
    op.drop_column('questions', 'corpus_reference')
    op.drop_column('questions', 'knowledge_area_id')
    op.drop_column('questions', 'course_id')

    # Re-add old constraints and indexes
    op.create_check_constraint(
        'check_difficulty',
        'questions',
        "difficulty IN ('Easy', 'Medium', 'Hard')"
    )

    op.create_index('idx_questions_ka', 'questions', ['ka'])
    op.create_index('idx_questions_difficulty', 'questions', ['difficulty'])
    op.create_index('idx_questions_source', 'questions', ['source'])
    op.create_index('idx_questions_concept_tags', 'questions', ['concept_tags'], postgresql_using='gin')
