"""Add pgvector extension and document_embeddings table

Revision ID: g7h8i9j0k1l2
Revises: 96c25a0c4cd8
Create Date: 2026-08-06 11:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
# pyrefly: ignore [missing-import]
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "g7h8i9j0k1l2"
down_revision: Union[str, None] = "b0107acce356"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create document_embeddings table
    op.create_table(
        "document_embeddings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_type", sa.String(64), nullable=False),
        sa.Column("document_id", sa.String(128), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
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

    op.create_index(
        "ix_document_embeddings_document_type",
        "document_embeddings",
        ["document_type"],
    )
    op.create_index(
        "ix_document_embeddings_document_id",
        "document_embeddings",
        ["document_id"],
    )
    op.create_unique_constraint(
        "uq_document_embeddings_type_id",
        "document_embeddings",
        ["document_type", "document_id"],
    )


def downgrade() -> None:
    op.drop_table("document_embeddings")
