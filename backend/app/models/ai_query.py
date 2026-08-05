"""
ai_query.py — SQLAlchemy model for AI Assistant query caching.

Defines:
  AIQueryCache — Caches natural language assistant answers by query_hash
                 (hash of normalized question + resolved intent and filters).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AIQueryCache(Base):
    """Cached AI assistant responses for natural language queries."""

    __tablename__ = "ai_query_caches"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # ── Cache key ─────────────────────────────────────────────────────────────
    query_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    # ── Query metadata ────────────────────────────────────────────────────────
    question: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    filters_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Structured answer from Gemini ─────────────────────────────────────────
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_data: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
