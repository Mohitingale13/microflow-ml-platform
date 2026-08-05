"""add dataset_ai_analysis table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-04
"""

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dataset_ai_analysis",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "dataset_id",
            sa.String(36),
            sa.ForeignKey("datasets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("analysis_json", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index("ix_dataset_ai_analysis_dataset_id", "dataset_ai_analysis", ["dataset_id"])
    op.create_index("ix_dataset_ai_analysis_prompt_hash", "dataset_ai_analysis", ["prompt_hash"])

    op.create_unique_constraint(
        "uq_dataset_ai_analysis_hash", "dataset_ai_analysis", ["dataset_id", "prompt_hash"]
    )


def downgrade() -> None:
    op.drop_table("dataset_ai_analysis")
