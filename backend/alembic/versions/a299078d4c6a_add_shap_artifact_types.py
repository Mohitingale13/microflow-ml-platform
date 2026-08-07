"""add_shap_artifact_types

Revision ID: a299078d4c6a
Revises: 96c25a0c4cd8
Create Date: 2026-08-06 08:55:30.600522

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a299078d4c6a'
down_revision: Union[str, None] = '96c25a0c4cd8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'shap_values_json'")
        op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'shap_summary_png'")
        op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'shap_bar_png'")
        op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'shap_dependence_png'")


def downgrade() -> None:
    pass
