"""add experiment_ai_strategy table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-04
"""

from alembic import op
import sqlalchemy as sa

revision: str = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "experiment_ai_strategy",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "experiment_id",
            sa.String(36),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("history_hash", sa.String(64), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("strategy_json", sa.Text(), nullable=False),
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

    op.create_index("ix_experiment_ai_strategy_experiment_id", "experiment_ai_strategy", ["experiment_id"])
    op.create_index("ix_experiment_ai_strategy_history_hash", "experiment_ai_strategy", ["history_hash"])

    op.create_unique_constraint(
        "uq_experiment_ai_strategy_hash", "experiment_ai_strategy", ["experiment_id", "history_hash"]
    )


def downgrade() -> None:
    op.drop_table("experiment_ai_strategy")
