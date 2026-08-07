"""add_missing_artifact_types

Revision ID: b0107acce356
Revises: a299078d4c6a
Create Date: 2026-08-06 08:58:34.264289

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0107acce356'
down_revision: Union[str, None] = 'a299078d4c6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'feature_importance_png'")
        op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'feature_importance_json'")
        op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'explainability_summary_json'")


def downgrade() -> None:
    pass
