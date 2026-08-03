"""
artifact.py — Pydantic schemas for the Artifact Registry endpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.artifact import ArtifactType


class RunResultResponse(BaseModel):
    """Full persisted evaluation result for a completed run."""

    id: str
    run_id: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float | None
    confusion_matrix: list[list[int]]
    execution_time_seconds: float | None
    started_at: datetime | None
    completed_at: datetime | None
    model_type: str | None
    dataset_id: str | None
    training_config_snapshot: dict[str, Any] | None
    preprocessing_summary: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ArtifactResponse(BaseModel):
    """Full artifact metadata."""

    id: str
    run_id: str
    experiment_id: str
    dataset_id: str
    artifact_type: ArtifactType
    filename: str
    mime_type: str
    storage_path: str
    file_size_bytes: int
    sha256_checksum: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ArtifactListItem(BaseModel):
    """Lightweight item for table listings."""

    id: str
    run_id: str
    experiment_id: str
    dataset_id: str
    artifact_type: ArtifactType
    filename: str
    file_size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ArtifactRegistryStats(BaseModel):
    """Summary statistics for the Artifact Registry page."""

    total_artifacts: int
    models_stored: int
    json_reports: int
    total_size_bytes: int
