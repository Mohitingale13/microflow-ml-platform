"""
run_comparison.py — SQLAlchemy model for AI-generated run comparisons.

Defines:
  RunAIComparison — One-per-prompt-hash per (run_a, run_b) pair.
                    Caches the six structured fields parsed from the Gemini
                    comparison response.

Cache key: (run_a_id, run_b_id, prompt_hash)
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RunAIComparison(Base):
    """Cached AI comparison generated for a completed pair of training runs."""

    __tablename__ = "run_ai_comparisons"

    __table_args__ = (
        UniqueConstraint(
            "run_a_id", "run_b_id", "prompt_hash",
            name="uq_run_ai_comparison_hash",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # ── Run pair ──────────────────────────────────────────────────────────────
    run_a_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_b_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Cache key ─────────────────────────────────────────────────────────────
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Six structured fields from Gemini ────────────────────────────────────
    overall_summary: Mapped[str] = mapped_column(Text, nullable=False)
    better_run: Mapped[str] = mapped_column(Text, nullable=False)
    key_improvements: Mapped[str] = mapped_column(Text, nullable=False)
    tradeoffs: Mapped[str] = mapped_column(Text, nullable=False)
    configuration_analysis: Mapped[str] = mapped_column(Text, nullable=False)
    next_recommendation: Mapped[str] = mapped_column(Text, nullable=False)

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

    # ── Relationships ─────────────────────────────────────────────────────────
    run_a: Mapped[Any] = relationship("Run", foreign_keys=[run_a_id])
    run_b: Mapped[Any] = relationship("Run", foreign_keys=[run_b_id])
