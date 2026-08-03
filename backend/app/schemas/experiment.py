from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.experiment import ExperimentStatus, RunStatus


# ─── Experiment Schemas ────────────────────────────────────────────────────────

class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=4096)
    dataset_id: str = Field(..., min_length=1, max_length=36)
    objective: str | None = Field(None, max_length=1024)
    default_configuration: dict[str, Any] | None = Field(None)
    tags: list[str] | None = Field(None)


class ExperimentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=4096)
    objective: str | None = Field(None, max_length=1024)
    default_configuration: dict[str, Any] | None = Field(None)
    tags: list[str] | None = Field(None)
    status: ExperimentStatus | None = Field(None)


class ExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    dataset_id: str
    objective: str | None
    default_configuration: dict[str, Any] | None
    tags: list[str] | None
    status: ExperimentStatus
    created_at: datetime
    updated_at: datetime


class ExperimentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    dataset_id: str
    objective: str | None
    tags: list[str] | None
    status: ExperimentStatus
    created_at: datetime
    updated_at: datetime


class ExperimentListResponse(BaseModel):
    experiments: list[ExperimentListItem]
    total: int


# ─── Run Schemas ───────────────────────────────────────────────────────────────

class RunCreate(BaseModel):
    experiment_id: str = Field(..., min_length=1, max_length=36)
    model_type: str | None = Field(None, max_length=100)
    training_configuration: dict[str, Any] | None = Field(None)
    notes: str | None = Field(None, max_length=4096)


class RunUpdate(BaseModel):
    model_type: str | None = Field(None, max_length=100)
    training_configuration: dict[str, Any] | None = Field(None)
    notes: str | None = Field(None, max_length=4096)
    status: RunStatus | None = Field(None)


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    experiment_id: str
    run_number: int
    model_type: str | None
    training_configuration: dict[str, Any] | None
    notes: str | None
    status: RunStatus
    created_at: datetime
    updated_at: datetime


class RunListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    experiment_id: str
    run_number: int
    model_type: str | None
    status: RunStatus
    created_at: datetime
    updated_at: datetime


class RunListResponse(BaseModel):
    runs: list[RunListItem]
    total: int
