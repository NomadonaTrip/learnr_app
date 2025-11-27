"""add_question_text_hash_unique_constraint

Revision ID: e1edd6b1edb2
Revises: 70868ab0800c
Create Date: 2025-11-27 00:12:06.277693

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1edd6b1edb2'
down_revision: Union[str, None] = '70868ab0800c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add a unique index on MD5 hash of question_text to prevent duplicates
    # This ensures idempotency when re-running imports
    op.create_index(
        'idx_questions_text_hash_unique',
        'questions',
        [sa.text('md5(question_text)')],
        unique=True,
        postgresql_using='btree'
    )


def downgrade() -> None:
    # Drop the unique index
    op.drop_index('idx_questions_text_hash_unique', table_name='questions')
