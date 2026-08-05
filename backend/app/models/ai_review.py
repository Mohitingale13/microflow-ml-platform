"""
ai_review.py — SQLAlchemy model for AI-generated run reviews.

Defines:
  RunAIReview — One-per-prompt-hash per run. Caches the full Gemini response
                alongside the five structured fields parsed from it.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Any

from app.db.base import Base


class RunAIReview(Base):
    """Cached AI review generated for a completed training run."""

    __tablename__ = "run_ai_reviews"

    __table_args__ = (
        UniqueConstraint("run_id", "prompt_hash", name="uq_run_ai_review_hash"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Cache key ─────────────────────────────────────────────────────────────
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Raw response (full JSON string from Gemini) ───────────────────────────
    review_text: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Parsed structured fields ──────────────────────────────────────────────
    overall_assessment: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[str] = mapped_column(Text, nullable=False)
    weaknesses: Mapped[str] = mapped_column(Text, nullable=False)
    comparison: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)

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
    run: Mapped[Any] = relationship("Run", foreign_keys=[run_id])
