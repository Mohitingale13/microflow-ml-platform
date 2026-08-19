"""add ai evaluation retry and status fields

Revision ID: 1cd59f8a341b
Revises: 0bc48e7b232a
Create Date: 2026-08-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1cd59f8a341b'
down_revision: Union[str, None] = '0bc48e7b232a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add columns (initially nullable for data backfill)
    op.add_column('ai_query_caches', sa.Column('evaluation_status', sa.String(length=20), nullable=True))
    op.add_column('ai_query_caches', sa.Column('evaluation_retries', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('ai_query_caches', sa.Column('evaluation_error', sa.Text(), nullable=True))

    # 2. Backfill existing rows safely
    # existing successfully evaluated rows become completed
    op.execute("UPDATE ai_query_caches SET evaluation_status = 'completed', evaluation_retries = 0 WHERE context_relevance_score IS NOT NULL")
    # existing unevaluated rows become pending
    op.execute("UPDATE ai_query_caches SET evaluation_status = 'pending', evaluation_retries = 0 WHERE context_relevance_score IS NULL")

    # 3. Apply NOT NULL constraints and index
    op.alter_column('ai_query_caches', 'evaluation_status', nullable=False, server_default='pending')
    op.alter_column('ai_query_caches', 'evaluation_retries', nullable=False, server_default='0')
    op.create_index(op.f('ix_ai_query_caches_evaluation_status'), 'ai_query_caches', ['evaluation_status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_query_caches_evaluation_status'), table_name='ai_query_caches')
    op.drop_column('ai_query_caches', 'evaluation_error')
    op.drop_column('ai_query_caches', 'evaluation_retries')
    op.drop_column('ai_query_caches', 'evaluation_status')
