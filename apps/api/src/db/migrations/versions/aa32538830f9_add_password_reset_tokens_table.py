"""Add password reset tokens table

Revision ID: aa32538830f9
Revises: 2371c9e29b29
Create Date: 2025-11-25 12:24:17.103673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa32538830f9'
down_revision: Union[str, None] = '2371c9e29b29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create password_reset_tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'], unique=False)
    op.create_index('idx_password_reset_tokens_token', 'password_reset_tokens', ['token'], unique=True)
    op.create_index('idx_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_password_reset_tokens_expires_at', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_token', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_user_id', table_name='password_reset_tokens')

    # Drop table
    op.drop_table('password_reset_tokens')
