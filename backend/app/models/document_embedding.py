"""
models/document_embedding.py — Database model for pgvector document embeddings.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, String, Text, JSON, UniqueConstraint
from sqlalchemy.types import TypeDecorator
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class VectorType(TypeDecorator):
    """
    SQLAlchemy TypeDecorator that uses pgvector's Vector(768) on PostgreSQL
    and JSON on SQLite (for unit testing environments).
    """
    impl = Vector
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(768))
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            import json
            try:
                return json.loads(value)
            except Exception:
                cleaned = value.strip("[]")
                if not cleaned:
                    return []
                return [float(x) for x in cleaned.split(",")]
        return list(value)


class DocumentEmbedding(Base):
    """
    SQLAlchemy model for stored vector embeddings of engineering documents
    (AI Reviews, AI Strategies, AI Comparisons, Dataset AI Analyses, Experiment Descriptions).
    """

    __tablename__ = "document_embeddings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_type = Column(String(64), nullable=False, index=True)
    document_id = Column(String(128), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(VectorType(), nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("document_type", "document_id", name="uq_document_embeddings_type_id"),
    )
