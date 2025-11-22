"""Initial database schema - Base tables for LearnR Platform

Revision ID: 001
Revises: None
Create Date: 2025-11-20 16:00:00

Creates:
- users
- courses
- knowledge_areas
- questions
- reading_content
- user_responses
- user_competency
- concept_mastery
- user_onboarding
- subscriptions (future)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema"""

    # ========================================
    # CORE TABLES
    # ========================================

    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_email', 'users', ['email'])

    # Courses table
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_code', sa.String(length=50), nullable=False),
        sa.Column('course_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('exam_type', sa.String(length=100), nullable=True),
        sa.Column('target_audience', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_code')
    )

    # Knowledge Areas table
    op.create_table(
        'knowledge_areas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('ka_code', sa.String(length=50), nullable=False),
        sa.Column('ka_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weight_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'ka_code', name='uq_course_ka_code')
    )
    op.create_index('idx_ka_course', 'knowledge_areas', ['course_id'])

    # ========================================
    # CONTENT TABLES
    # ========================================

    # Questions table
    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('knowledge_area_id', sa.Integer(), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('option_a', sa.Text(), nullable=False),
        sa.Column('option_b', sa.Text(), nullable=False),
        sa.Column('option_c', sa.Text(), nullable=False),
        sa.Column('option_d', sa.Text(), nullable=False),
        sa.Column('correct_answer', sa.CHAR(length=1), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('difficulty_level', sa.Integer(), nullable=True),
        sa.Column('concept_tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('embedding_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.CheckConstraint("correct_answer IN ('A','B','C','D')", name='ck_correct_answer'),
        sa.CheckConstraint('difficulty_level BETWEEN 1 AND 5', name='ck_difficulty_level'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.ForeignKeyConstraint(['knowledge_area_id'], ['knowledge_areas.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_questions_course', 'questions', ['course_id'])
    op.create_index('idx_questions_ka', 'questions', ['knowledge_area_id'])
    op.create_index('idx_questions_difficulty', 'questions', ['difficulty_level'])

    # Reading Content table
    op.create_table(
        'reading_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('knowledge_area_id', sa.Integer(), nullable=True),
        sa.Column('section_reference', sa.String(length=100), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=True),
        sa.Column('difficulty_level', sa.Integer(), nullable=True),
        sa.Column('concept_tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('embedding_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.CheckConstraint('difficulty_level BETWEEN 1 AND 5', name='ck_reading_difficulty'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.ForeignKeyConstraint(['knowledge_area_id'], ['knowledge_areas.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reading_course', 'reading_content', ['course_id'])
    op.create_index('idx_reading_ka', 'reading_content', ['knowledge_area_id'])

    # ========================================
    # USER ACTIVITY TABLES
    # ========================================

    # User Responses table (will be updated in v2.1 migration)
    op.create_table(
        'user_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('question_id', sa.Integer(), nullable=True),
        sa.Column('selected_answer', sa.CHAR(length=1), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('time_taken_seconds', sa.Integer(), nullable=True),
        sa.Column('session_type', sa.String(length=50), nullable=True),
        sa.Column('is_review', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('answered_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.CheckConstraint("selected_answer IN ('A','B','C','D')", name='ck_selected_answer'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_responses_user', 'user_responses', ['user_id'])
    op.create_index('idx_responses_question', 'user_responses', ['question_id'])
    op.create_index('idx_responses_date', 'user_responses', ['answered_at'])

    # User Competency table
    op.create_table(
        'user_competency',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('knowledge_area_id', sa.Integer(), nullable=True),
        sa.Column('competency_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('questions_answered', sa.Integer(), server_default='0', nullable=True),
        sa.Column('last_updated', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['knowledge_area_id'], ['knowledge_areas.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'knowledge_area_id', name='uq_user_ka')
    )
    op.create_index('idx_competency_user', 'user_competency', ['user_id'])

    # Concept Mastery table (Spaced Repetition)
    op.create_table(
        'concept_mastery',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('concept_tag', sa.String(length=255), nullable=False),
        sa.Column('knowledge_area_id', sa.Integer(), nullable=True),
        sa.Column('repetition_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('easiness_factor', sa.Numeric(precision=3, scale=2), server_default='2.5', nullable=True),
        sa.Column('interval_days', sa.Integer(), server_default='1', nullable=True),
        sa.Column('next_review_date', sa.Date(), nullable=False),
        sa.Column('last_reviewed', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['knowledge_area_id'], ['knowledge_areas.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'concept_tag', name='uq_user_concept')
    )
    op.create_index('idx_mastery_user', 'concept_mastery', ['user_id'])
    op.create_index('idx_mastery_review_date', 'concept_mastery', ['next_review_date'])

    # User Onboarding table
    op.create_table(
        'user_onboarding',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('referral_source', sa.String(length=100), nullable=True),
        sa.Column('exam_date', sa.Date(), nullable=True),
        sa.Column('current_knowledge_level', sa.String(length=50), nullable=True),
        sa.Column('target_score', sa.Integer(), nullable=True),
        sa.Column('daily_study_minutes', sa.Integer(), nullable=True),
        sa.Column('has_completed_diagnostic', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Subscriptions table (Future - marked for post-MVP)
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('tier', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('current_period_start', sa.Date(), nullable=True),
        sa.Column('current_period_end', sa.Date(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop all initial tables"""
    op.drop_table('subscriptions')
    op.drop_table('user_onboarding')
    op.drop_table('concept_mastery')
    op.drop_table('user_competency')
    op.drop_table('user_responses')
    op.drop_table('reading_content')
    op.drop_table('questions')
    op.drop_table('knowledge_areas')
    op.drop_table('courses')
    op.drop_table('users')
