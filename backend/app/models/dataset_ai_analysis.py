"""
dataset_ai_analysis.py — SQLAlchemy model for AI Dataset Intelligence analysis caching.

Defines:
  DatasetAIAnalysis — Caches automated dataset quality, feature observations, and
                      recommendations by dataset_id and prompt_hash.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DatasetAIAnalysis(Base):
    """Cached AI Dataset Intelligence report generated for an uploaded dataset."""

    __tablename__ = "dataset_ai_analysis"

    __table_args__ = (
        UniqueConstraint("dataset_id", "prompt_hash", name="uq_dataset_ai_analysis_hash"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Cache key ─────────────────────────────────────────────────────────────
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Raw JSON response containing all structured insights ──────────────────
    analysis_json: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    dataset: Mapped[Any] = relationship("Dataset", foreign_keys=[dataset_id])
