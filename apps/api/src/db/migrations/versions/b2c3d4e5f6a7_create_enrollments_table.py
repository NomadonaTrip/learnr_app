"""Create enrollments table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-09

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create enrollments table
    op.create_table(
        'enrollments',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('course_id', UUID(as_uuid=True), nullable=False),
        sa.Column('exam_date', sa.Date(), nullable=True),
        sa.Column('target_score', sa.Integer(), nullable=True),
        sa.Column('daily_study_time', sa.Integer(), nullable=True),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('completion_percentage', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'course_id', name='uq_enrollments_user_course'),
        sa.CheckConstraint(
            "status IN ('active', 'paused', 'completed', 'archived')",
            name='check_enrollment_status'
        )
    )

    # Create indexes
    op.create_index('idx_enrollments_user', 'enrollments', ['user_id'])
    op.create_index('idx_enrollments_course', 'enrollments', ['course_id'])
    op.create_index(
        'idx_enrollments_user_active',
        'enrollments',
        ['user_id', 'status'],
        postgresql_where=sa.text("status = 'active'")
    )


def downgrade() -> None:
    op.drop_index('idx_enrollments_user_active', table_name='enrollments')
    op.drop_index('idx_enrollments_course', table_name='enrollments')
    op.drop_index('idx_enrollments_user', table_name='enrollments')
    op.drop_table('enrollments')
