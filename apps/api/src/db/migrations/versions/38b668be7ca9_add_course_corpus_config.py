"""add course corpus_config

Revision ID: 38b668be7ca9
Revises: z6u7v8w9x0y1
Create Date: 2026-06-27 12:56:48.067335

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '38b668be7ca9'
down_revision: Union[str, None] = 'z6u7v8w9x0y1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('courses', sa.Column('corpus_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('courses', 'corpus_config')
