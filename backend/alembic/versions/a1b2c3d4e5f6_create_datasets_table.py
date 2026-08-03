"""create datasets table

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("version", sa.String(50), nullable=False, server_default="v1"),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("column_count", sa.Integer(), nullable=True),
        sa.Column("storage_path", sa.String(1024), nullable=False, server_default=""),
        sa.Column(
            "status",
            sa.Enum("uploaded", "analysing", "ready", "error", name="datasetstatuse", create_type=False),
            nullable=False,
            server_default="uploaded",
        ),
        sa.Column("column_names", sa.JSON(), nullable=True),
        sa.Column("dtypes", sa.JSON(), nullable=True),
        sa.Column("missing_values", sa.JSON(), nullable=True),
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

    op.create_index("ix_datasets_name", "datasets", ["name"])
    op.create_index("ix_datasets_file_hash", "datasets", ["file_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_datasets_file_hash", table_name="datasets")
    op.drop_index("ix_datasets_name", table_name="datasets")
    op.drop_table("datasets")
    op.execute("DROP TYPE datasetstatuse")
