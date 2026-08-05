"""add run_ai_reviews table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-04
"""

from alembic import op
import sqlalchemy as sa

revision: str = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "run_ai_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Cache key
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        # Raw Gemini response
        sa.Column("review_text", sa.Text(), nullable=False),
        # Structured parsed fields
        sa.Column("overall_assessment", sa.Text(), nullable=False),
        sa.Column("strengths", sa.Text(), nullable=False),
        sa.Column("weaknesses", sa.Text(), nullable=False),
        sa.Column("comparison", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        # Timestamps
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

    # Indexes
    op.create_index("ix_run_ai_reviews_run_id", "run_ai_reviews", ["run_id"])
    op.create_index("ix_run_ai_reviews_prompt_hash", "run_ai_reviews", ["prompt_hash"])

    # Unique constraint: one review per (run, prompt_hash)
    op.create_unique_constraint(
        "uq_run_ai_review_hash", "run_ai_reviews", ["run_id", "prompt_hash"]
    )


def downgrade() -> None:
    op.drop_table("run_ai_reviews")
