import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum as SAEnum, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DatasetStatus(str, enum.Enum):
    uploaded = "uploaded"
    analysing = "analysing"
    ready = "ready"
    error = "error"


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1")
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_path: Mapped[str] = mapped_column(
        String(1024), nullable=False, default=""
    )
    status: Mapped[DatasetStatus] = mapped_column(
        SAEnum(
            DatasetStatus, 
            name="datasetstatuse", 
            values_callable=lambda obj: [e.value for e in obj]
        ),
        nullable=False,
        default=DatasetStatus.uploaded,
    )
    column_names: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    dtypes: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    missing_values: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
