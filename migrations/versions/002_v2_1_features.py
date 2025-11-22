"""v2.1 Feature Release - Session Management, Reviews, Reading Library, Admin Tools

Revision ID: 002
Revises: 001
Create Date: 2025-11-20 16:30:00

Adds v2.1 Features:
- Session Management (quiz_sessions)
- Post-Session Review (session_reviews, review_attempts)
- Asynchronous Reading Library (reading_queue, reading_bookmarks, reading_engagement)
- Feedback System (explanation_feedback, reading_feedback)
- Admin Support Tools (admin_audit_log)
- Progress Tracking (competency_history)
- Password Reset (password_reset_tokens)

Updates:
- user_responses: Add session_id FK for session-based tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add v2.1 features to database schema"""

    # ========================================
    # COMPETENCY HISTORY (Progress Trends)
    # ========================================

    op.create_table(
        'competency_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('knowledge_area_id', sa.Integer(), nullable=False),
        sa.Column('competency_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('questions_answered', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['knowledge_area_id'], ['knowledge_areas.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'knowledge_area_id', 'snapshot_date', name='uq_user_ka_snapshot')
    )
    op.create_index('idx_history_user', 'competency_history', ['user_id'])
    op.create_index('idx_history_ka', 'competency_history', ['knowledge_area_id'])
    op.create_index('idx_history_date', 'competency_history', ['snapshot_date'])

    # ========================================
    # PASSWORD RESET
    # ========================================

    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('is_used', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('used_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index('idx_reset_token', 'password_reset_tokens', ['token'])
    op.create_index('idx_reset_user', 'password_reset_tokens', ['user_id'])
    op.create_index('idx_reset_expires', 'password_reset_tokens', ['expires_at'])

    # ========================================
    # SESSION MANAGEMENT (Must create before feedback tables)
    # ========================================

    op.create_table(
        'quiz_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_type', sa.String(length=20), nullable=False),
        sa.Column('target_question_count', sa.Integer(), nullable=True),
        sa.Column('questions_answered_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('correct_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('current_question_id', sa.Integer(), nullable=True),
        sa.Column('is_paused', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('is_completed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('start_time', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('end_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('paused_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.CheckConstraint(
            "session_type IN ('diagnostic', 'new_content', 'mixed', 'ka_focused')",
            name='ck_session_type'
        ),
        sa.ForeignKeyConstraint(['current_question_id'], ['questions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sessions_user', 'quiz_sessions', ['user_id'])
    op.create_index('idx_sessions_status', 'quiz_sessions', ['is_completed', 'is_paused'])
    op.create_index('idx_sessions_created', 'quiz_sessions', ['created_at'])

    # Update user_responses to add session_id FK (now that quiz_sessions exists)
    op.add_column('user_responses', sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_user_responses_session',
        'user_responses', 'quiz_sessions',
        ['session_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_responses_session', 'user_responses', ['session_id'])

    # ========================================
    # POST-SESSION REVIEW
    # ========================================

    # Session Reviews
    op.create_table(
        'session_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('review_status', sa.String(length=20), server_default='not_started', nullable=False),
        sa.Column('total_questions_to_review', sa.Integer(), nullable=False),
        sa.Column('questions_reinforced_correctly', sa.Integer(), server_default='0', nullable=True),
        sa.Column('questions_still_incorrect', sa.Integer(), server_default='0', nullable=True),
        sa.Column('original_score_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('final_score_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('improvement_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('review_started_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('review_completed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.CheckConstraint(
            "review_status IN ('not_started', 'in_progress', 'completed', 'skipped')",
            name='ck_review_status'
        ),
        sa.ForeignKeyConstraint(['session_id'], ['quiz_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index('idx_reviews_user', 'session_reviews', ['user_id'])
    op.create_index('idx_reviews_status', 'session_reviews', ['review_status'])
    op.create_index('idx_reviews_created', 'session_reviews', ['created_at'])

    # Review Attempts
    op.create_table(
        'review_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_review_id', sa.Integer(), nullable=False),
        sa.Column('original_attempt_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('selected_answer', sa.CHAR(length=1), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('is_reinforced', sa.Boolean(), nullable=False),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.CheckConstraint("selected_answer IN ('A','B','C','D')", name='ck_review_answer'),
        sa.ForeignKeyConstraint(['original_attempt_id'], ['user_responses.id']),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
        sa.ForeignKeyConstraint(['session_review_id'], ['session_reviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_review_attempts_session', 'review_attempts', ['session_review_id'])
    op.create_index('idx_review_attempts_question', 'review_attempts', ['question_id'])
    op.create_index('idx_review_attempts_reinforced', 'review_attempts', ['is_reinforced'])

    # ========================================
    # ASYNCHRONOUS READING LIBRARY
    # ========================================

    # Reading Queue
    op.create_table(
        'reading_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('chunk_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('priority', sa.String(length=10), nullable=False),
        sa.Column('reading_status', sa.String(length=20), server_default='unread', nullable=True),
        sa.Column('was_incorrect', sa.Boolean(), nullable=False),
        sa.Column('relevance_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('ka_id', sa.Integer(), nullable=True),
        sa.Column('times_opened', sa.Integer(), server_default='0', nullable=True),
        sa.Column('first_opened_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('total_reading_time_seconds', sa.Integer(), server_default='0', nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('dismissed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('added_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.CheckConstraint("priority IN ('high', 'medium', 'low')", name='ck_priority'),
        sa.CheckConstraint(
            "reading_status IN ('unread', 'reading', 'completed', 'dismissed')",
            name='ck_reading_status'
        ),
        sa.ForeignKeyConstraint(['chunk_id'], ['reading_content.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ka_id'], ['knowledge_areas.id']),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
        sa.ForeignKeyConstraint(['session_id'], ['quiz_sessions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'chunk_id', name='uq_user_chunk')
    )
    op.create_index('idx_reading_queue_user', 'reading_queue', ['user_id'])
    op.create_index('idx_reading_queue_status', 'reading_queue', ['reading_status'])
    op.create_index('idx_reading_queue_priority', 'reading_queue', ['priority'])
    op.create_index('idx_reading_queue_ka', 'reading_queue', ['ka_id'])
    op.create_index('idx_reading_queue_added', 'reading_queue', ['added_at'])

    # Reading Bookmarks
    op.create_table(
        'reading_bookmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('chunk_id', sa.Integer(), nullable=False),
        sa.Column('source_context', sa.String(length=100), nullable=True),
        sa.Column('related_question_id', sa.Integer(), nullable=True),
        sa.Column('read_status', sa.String(length=20), server_default='unread', nullable=True),
        sa.Column('bookmarked_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('marked_read_at', sa.TIMESTAMP(), nullable=True),
        sa.CheckConstraint("read_status IN ('unread', 'read')", name='ck_bookmark_status'),
        sa.ForeignKeyConstraint(['chunk_id'], ['reading_content.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_question_id'], ['questions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'chunk_id', name='uq_bookmark_user_chunk')
    )
    op.create_index('idx_bookmarks_user', 'reading_bookmarks', ['user_id'])
    op.create_index('idx_bookmarks_status', 'reading_bookmarks', ['read_status'])
    op.create_index('idx_bookmarks_created', 'reading_bookmarks', ['bookmarked_at'])

    # Reading Engagement (Analytics)
    op.create_table(
        'reading_engagement',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('chunk_id', sa.Integer(), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('queue_id', sa.Integer(), nullable=True),
        sa.Column('displayed_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('expanded_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('collapsed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('scroll_depth_percentage', sa.Integer(), nullable=True),
        sa.Column('marked_read', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.CheckConstraint(
            'scroll_depth_percentage BETWEEN 0 AND 100',
            name='ck_scroll_depth'
        ),
        sa.ForeignKeyConstraint(['chunk_id'], ['reading_content.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['queue_id'], ['reading_queue.id']),
        sa.ForeignKeyConstraint(['session_id'], ['quiz_sessions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_engagement_user', 'reading_engagement', ['user_id'])
    op.create_index('idx_engagement_chunk', 'reading_engagement', ['chunk_id'])
    op.create_index('idx_engagement_session', 'reading_engagement', ['session_id'])
    op.create_index('idx_engagement_displayed', 'reading_engagement', ['displayed_at'])

    # ========================================
    # FEEDBACK SYSTEM (After reading_queue creation)
    # ========================================

    # Explanation Feedback
    op.create_table(
        'explanation_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_helpful', sa.Boolean(), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
        sa.ForeignKeyConstraint(['session_id'], ['quiz_sessions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_exp_feedback_question', 'explanation_feedback', ['question_id'])
    op.create_index('idx_exp_feedback_user', 'explanation_feedback', ['user_id'])
    op.create_index('idx_exp_feedback_helpful', 'explanation_feedback', ['is_helpful'])

    # Reading Feedback
    op.create_table(
        'reading_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('chunk_id', sa.Integer(), nullable=False),
        sa.Column('queue_id', sa.Integer(), nullable=True),
        sa.Column('is_relevant', sa.Boolean(), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['chunk_id'], ['reading_content.id']),
        sa.ForeignKeyConstraint(['queue_id'], ['reading_queue.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reading_feedback_chunk', 'reading_feedback', ['chunk_id'])
    op.create_index('idx_reading_feedback_user', 'reading_feedback', ['user_id'])
    op.create_index('idx_reading_feedback_relevant', 'reading_feedback', ['is_relevant'])

    # ========================================
    # ADMIN SUPPORT TOOLS
    # ========================================

    op.create_table(
        'admin_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_user_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['admin_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_admin', 'admin_audit_log', ['admin_user_id'])
    op.create_index('idx_audit_action', 'admin_audit_log', ['action_type'])
    op.create_index('idx_audit_target', 'admin_audit_log', ['target_user_id'])
    op.create_index('idx_audit_created', 'admin_audit_log', ['created_at'])


def downgrade() -> None:
    """Remove v2.1 features"""

    # Drop new tables (reverse order of creation)
    op.drop_table('admin_audit_log')
    op.drop_table('reading_engagement')
    op.drop_table('reading_bookmarks')
    op.drop_table('reading_queue')
    op.drop_table('review_attempts')
    op.drop_table('session_reviews')
    op.drop_table('quiz_sessions')
    op.drop_table('reading_feedback')
    op.drop_table('explanation_feedback')
    op.drop_table('password_reset_tokens')
    op.drop_table('competency_history')

    # Remove session_id column from user_responses
    op.drop_index('idx_responses_session', table_name='user_responses')
    op.drop_constraint('fk_user_responses_session', 'user_responses', type_='foreignkey')
    op.drop_column('user_responses', 'session_id')
