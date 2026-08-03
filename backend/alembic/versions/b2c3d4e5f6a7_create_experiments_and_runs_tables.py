"""create experiments and runs tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Create ENUM types ────────────────────────────────────────────────────
    experimentstatus = sa.Enum(
        "draft", "active", "archived",
        name="experimentstatus",
    )
    # Removing manual .create calls to avoid duplicate type errors
    # experimentstatus.create(op.get_bind(), checkfirst=True)

    runstatus = sa.Enum(
        "draft", "queued", "running", "completed", "failed", "cancelled",
        name="runstatus",
    )
    # runstatus.create(op.get_bind(), checkfirst=True)

    # ── experiments table ────────────────────────────────────────────────────
    op.create_table(
        "experiments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "dataset_id",
            sa.String(36),
            sa.ForeignKey("datasets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("objective", sa.String(1024), nullable=True),
        sa.Column("default_configuration", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft", "active", "archived",
                name="experimentstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="draft",
        ),
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

    op.create_index("ix_experiments_name", "experiments", ["name"])
    op.create_index("ix_experiments_dataset_id", "experiments", ["dataset_id"])
    op.create_index("ix_experiments_status", "experiments", ["status"])
    op.create_index("ix_experiments_created_at", "experiments", ["created_at"])

    # ── runs table ───────────────────────────────────────────────────────────
    op.create_table(
        "runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "experiment_id",
            sa.String(36),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("run_number", sa.Integer(), nullable=False),
        sa.Column("model_type", sa.String(100), nullable=True),
        sa.Column("training_configuration", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft", "queued", "running", "completed", "failed", "cancelled",
                name="runstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="draft",
        ),
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

    op.create_index("ix_runs_experiment_id", "runs", ["experiment_id"])
    op.create_index("ix_runs_status", "runs", ["status"])
    op.create_index("ix_runs_created_at", "runs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_runs_created_at", table_name="runs")
    op.drop_index("ix_runs_status", table_name="runs")
    op.drop_index("ix_runs_experiment_id", table_name="runs")
    op.drop_table("runs")

    op.drop_index("ix_experiments_created_at", table_name="experiments")
    op.drop_index("ix_experiments_status", table_name="experiments")
    op.drop_index("ix_experiments_dataset_id", table_name="experiments")
    op.drop_index("ix_experiments_name", table_name="experiments")
    op.drop_table("experiments")

    op.execute("DROP TYPE runstatus")
    op.execute("DROP TYPE experimentstatus")
