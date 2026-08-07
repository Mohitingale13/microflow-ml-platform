"""
repositories/document_embedding_repository.py — Data access layer for pgvector document embeddings.
"""

from __future__ import annotations

import logging
from typing import Any, Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.document_embedding import DocumentEmbedding

logger = logging.getLogger(__name__)


class DocumentEmbeddingRepository:
    """Repository handling CRUD operations and pgvector similarity search on document_embeddings."""

    def upsert_embedding(
        self,
        db: Session,
        document_type: str,
        document_id: str,
        content: str,
        embedding: list[float],
        metadata_json: dict[str, Any] | None = None,
    ) -> DocumentEmbedding:
        """Create or update an embedding record by (document_type, document_id)."""
        existing = db.execute(
            select(DocumentEmbedding).where(
                DocumentEmbedding.document_type == document_type,
                DocumentEmbedding.document_id == document_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.content = content  # type: ignore
            existing.embedding = embedding  # type: ignore
            existing.metadata_json = metadata_json  # type: ignore
            db.commit()
            db.refresh(existing)
            logger.info("Updated vector embedding for %s / %s", document_type, document_id)
            return existing
        else:
            record = DocumentEmbedding(
                document_type=document_type,
                document_id=document_id,
                content=content,
                embedding=embedding,
                metadata_json=metadata_json,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info("Created vector embedding for %s / %s", document_type, document_id)
            return record

    def search_similar(
        self,
        db: Session,
        query_vector: list[float],
        limit: int = 5,
        document_types: list[str] | None = None,
    ) -> Sequence[tuple[DocumentEmbedding, float]]:
        """
        Execute vector similarity search using pgvector cosine distance (<=>).
        Falls back to in-memory Python cosine distance for SQLite unit test environments.
        """
        is_postgres = db.bind is not None and db.bind.dialect.name == "postgresql"

        if is_postgres:
            distance_col = DocumentEmbedding.embedding.cosine_distance(query_vector).label("distance")
            stmt = select(DocumentEmbedding, distance_col)
            if document_types:
                stmt = stmt.where(DocumentEmbedding.document_type.in_(document_types))
            stmt = stmt.order_by(distance_col).limit(limit)
            results = db.execute(stmt).all()
            return [(row[0], float(row[1])) for row in results]
        else:
            # Fallback for SQLite in unit tests
            stmt = select(DocumentEmbedding)
            if document_types:
                stmt = stmt.where(DocumentEmbedding.document_type.in_(document_types))
            all_docs = db.execute(stmt).scalars().all()

            def _cosine_dist(vec_a: list[float], vec_b: list[float]) -> float:
                if not vec_a or not vec_b or len(vec_a) != len(vec_b):
                    return 1.0
                dot = sum(a * b for a, b in zip(vec_a, vec_b))
                norm_a = sum(a * a for a in vec_a) ** 0.5
                norm_b = sum(b * b for b in vec_b) ** 0.5
                if norm_a == 0 or norm_b == 0:
                    return 1.0
                return 1.0 - (dot / (norm_a * norm_b))

            scored = [(doc, _cosine_dist(query_vector, list(doc.embedding))) for doc in all_docs]  # type: ignore
            scored.sort(key=lambda x: x[1])
            return scored[:limit]

    def get_by_type_and_id(
        self, db: Session, document_type: str, document_id: str
    ) -> DocumentEmbedding | None:
        """Retrieve a specific document embedding by document_type and document_id."""
        return db.execute(
            select(DocumentEmbedding).where(
                DocumentEmbedding.document_type == document_type,
                DocumentEmbedding.document_id == document_id,
            )
        ).scalar_one_or_none()
