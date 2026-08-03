"""add run_results and artifacts tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-03
"""

from alembic import op
import sqlalchemy as sa

revision: str = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── run_results table ────────────────────────────────────────────────────
    op.create_table(
        "run_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # Evaluation metrics
        sa.Column("accuracy", sa.Float(), nullable=False),
        sa.Column("precision", sa.Float(), nullable=False),
        sa.Column("recall", sa.Float(), nullable=False),
        sa.Column("f1_score", sa.Float(), nullable=False),
        sa.Column("roc_auc", sa.Float(), nullable=True),
        sa.Column("confusion_matrix", sa.JSON(), nullable=False),
        # Timing
        sa.Column("execution_time_seconds", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Snapshot metadata
        sa.Column("model_type", sa.String(100), nullable=True),
        sa.Column("dataset_id", sa.String(36), nullable=True),
        sa.Column("training_config_snapshot", sa.JSON(), nullable=True),
        sa.Column("preprocessing_summary", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_run_results_run_id", "run_results", ["run_id"])

    # ── artifacts table ───────────────────────────────────────────────────────
    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("experiment_id", sa.String(36), nullable=False),
        sa.Column("dataset_id", sa.String(36), nullable=False),
        sa.Column(
            "artifact_type",
            sa.Enum(
                "trained_model",
                "metrics_json",
                "evaluation_json",
                "confusion_matrix_json",
                "configuration_json",
                "preprocessing_json",
                name="artifacttype",
            ),
            nullable=False,
        ),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256_checksum", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_artifacts_run_id", "artifacts", ["run_id"])
    op.create_index("ix_artifacts_experiment_id", "artifacts", ["experiment_id"])
    op.create_index("ix_artifacts_artifact_type", "artifacts", ["artifact_type"])
    op.create_index("ix_artifacts_created_at", "artifacts", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_artifacts_created_at", table_name="artifacts")
    op.drop_index("ix_artifacts_artifact_type", table_name="artifacts")
    op.drop_index("ix_artifacts_experiment_id", table_name="artifacts")
    op.drop_index("ix_artifacts_run_id", table_name="artifacts")
    op.drop_table("artifacts")
    op.execute("DROP TYPE IF EXISTS artifacttype")

    op.drop_index("ix_run_results_run_id", table_name="run_results")
    op.drop_table("run_results")
