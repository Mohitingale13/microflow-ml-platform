from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.dataset import DatasetStatus


class DatasetUploadForm(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1024)


class DatasetListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    version: str
    original_filename: str
    file_size_bytes: int
    row_count: int | None
    column_count: int | None
    status: DatasetStatus
    created_at: datetime
    updated_at: datetime


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    version: str
    original_filename: str
    file_hash: str
    file_size_bytes: int
    row_count: int | None
    column_count: int | None
    storage_path: str
    status: DatasetStatus
    column_names: list[str] | None
    dtypes: dict[str, str] | None
    missing_values: dict[str, int] | None
    created_at: datetime
    updated_at: datetime


class DatasetPreviewResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int | None


class NumericColumnStat(BaseModel):
    type: str = "numeric"
    min: float | None
    max: float | None
    mean: float | None
    median: float | None
    std: float | None
    missing_count: int


class CategoricalColumnStat(BaseModel):
    type: str = "categorical"
    unique_values: int
    most_frequent: str | None
    missing_count: int


class DatasetStatisticsResponse(BaseModel):
    dataset_id: str
    statistics: dict[str, NumericColumnStat | CategoricalColumnStat]
