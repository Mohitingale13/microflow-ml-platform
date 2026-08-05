"""
experiment_strategy.py — SQLAlchemy model for AI Experiment Strategy recommendations.

Defines:
  ExperimentAIStrategy — Caches evidence-driven recommendations by experiment_id
                         and history_hash.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExperimentAIStrategy(Base):
    """Cached AI Experiment Strategy recommendations generated for an experiment."""

    __tablename__ = "experiment_ai_strategy"

    __table_args__ = (
        UniqueConstraint("experiment_id", "history_hash", name="uq_experiment_ai_strategy_hash"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    experiment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Cache key ─────────────────────────────────────────────────────────────
    # History hash represents the exact chronological run status and metric state + dataset version
    history_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Raw JSON response containing all structured insights ──────────────────
    strategy_json: Mapped[str] = mapped_column(Text, nullable=False)

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
    experiment: Mapped[Any] = relationship("Experiment", foreign_keys=[experiment_id])
