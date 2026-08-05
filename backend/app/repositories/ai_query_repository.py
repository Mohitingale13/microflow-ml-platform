"""
ai_query_repository.py — Data access for AIQueryCache records.

Follows existing repository patterns:
  - Session-based
  - No business logic
  - Clean data CRUD
"""

from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.ai_query import AIQueryCache


class AIQueryRepository:

    def get_by_hash(self, query_hash: str, db: Session) -> AIQueryCache | None:
        """Return a cached query response by its deterministic SHA-256 hash."""
        return (
            db.query(AIQueryCache)
            .filter(AIQueryCache.query_hash == query_hash)
            .first()
        )

    def get_recent(self, limit: int, db: Session) -> list[AIQueryCache]:
        """Return the most recently answered assistant queries."""
        return (
            db.query(AIQueryCache)
            .order_by(AIQueryCache.created_at.desc())
            .limit(limit)
            .all()
        )

    def create(
        self,
        db: Session,
        *,
        query_hash: str,
        question: str,
        intent: str,
        filters_json: str,
        model_name: str,
        answer: str,
        reasoning: str,
        supporting_data: str,
        recommendation: str,
    ) -> AIQueryCache:
        record = AIQueryCache(
            query_hash=query_hash,
            question=question,
            intent=intent,
            filters_json=filters_json,
            model_name=model_name,
            answer=answer,
            reasoning=reasoning,
            supporting_data=supporting_data,
            recommendation=recommendation or "",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
