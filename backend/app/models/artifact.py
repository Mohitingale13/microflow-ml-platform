"""
artifact.py — SQLAlchemy models for the Artifact Registry.

Defines:
  RunResult  — One-to-one with Run. Persists all evaluation metrics and timing.
  Artifact   — Many-to-one with Run. Persists file metadata for each training output.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ArtifactType(str, enum.Enum):
    trained_model = "trained_model"
    metrics_json = "metrics_json"
    evaluation_json = "evaluation_json"
    confusion_matrix_json = "confusion_matrix_json"
    configuration_json = "configuration_json"
    preprocessing_json = "preprocessing_json"


class RunResult(Base):
    """Persisted evaluation result for a completed Run (one-to-one)."""

    __tablename__ = "run_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ── Evaluation metrics ────────────────────────────────────────────────────
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    f1_score: Mapped[float] = mapped_column(Float, nullable=False)
    roc_auc: Mapped[float | None] = mapped_column(Float, nullable=True)
    confusion_matrix: Mapped[list[Any]] = mapped_column(JSON, nullable=False)

    # ── Timing ───────────────────────────────────────────────────────────────
    execution_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Snapshot metadata ─────────────────────────────────────────────────────
    model_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    training_config_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    preprocessing_summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    run: Mapped["Any"] = relationship("Run", back_populates="result", uselist=False)


class Artifact(Base):
    """Immutable file artifact produced by a training run."""

    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    experiment_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    dataset_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # ── File metadata ─────────────────────────────────────────────────────────
    artifact_type: Mapped[ArtifactType] = mapped_column(
        SAEnum(
            ArtifactType,
            name="artifacttype",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    run: Mapped["Any"] = relationship("Run", back_populates="artifacts")
