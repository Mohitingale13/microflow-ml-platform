import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExperimentStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class RunStatus(str, enum.Enum):
    draft = "draft"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    objective: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    default_configuration: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    tags: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[ExperimentStatus] = mapped_column(
        SAEnum(
            ExperimentStatus,
            name="experimentstatus",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ExperimentStatus.draft,
        index=True,
    )
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
    )

    # Relationships
    runs: Mapped[list["Run"]] = relationship(
        "Run", back_populates="experiment", cascade="all, delete-orphan"
    )


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    experiment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    model_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    training_configuration: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RunStatus] = mapped_column(
        SAEnum(
            RunStatus,
            name="runstatus",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=RunStatus.draft,
        index=True,
    )
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
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="runs")
    result: Mapped["Any"] = relationship(
        "RunResult", back_populates="run", uselist=False, cascade="all, delete-orphan"
    )
    artifacts: Mapped[list["Any"]] = relationship(
        "Artifact", back_populates="run", cascade="all, delete-orphan"
    )
