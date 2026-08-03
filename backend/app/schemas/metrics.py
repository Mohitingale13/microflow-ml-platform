"""
metrics.py — Pydantic schemas for the Metrics Dashboard API.

Defines response models for:
  - Global overview metrics
  - Per-model aggregated statistics (leaderboard)
  - Per-experiment performance summaries
  - Per-dataset performance summaries
  - Multi-run side-by-side comparison
"""

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict


class MetricsOverview(BaseModel):
    """Global system-wide performance overview."""

    model_config = ConfigDict(from_attributes=True)

    total_runs: int
    completed_runs: int
    failed_runs: int
    success_rate: float
    average_accuracy: Optional[float] = None
    average_precision: Optional[float] = None
    average_recall: Optional[float] = None
    average_f1: Optional[float] = None
    average_roc_auc: Optional[float] = None
    average_training_duration: Optional[float] = None


class ModelMetricSummary(BaseModel):
    """Aggregated statistics for a specific model family."""

    model_config = ConfigDict(from_attributes=True)

    model_type: str
    number_of_runs: int
    best_accuracy: Optional[float] = None
    average_accuracy: Optional[float] = None
    best_f1: Optional[float] = None
    average_f1: Optional[float] = None
    average_roc_auc: Optional[float] = None
    average_duration: Optional[float] = None


class ExperimentMetricSummary(BaseModel):
    """Aggregated performance statistics for an experiment."""

    model_config = ConfigDict(from_attributes=True)

    experiment_id: str
    experiment_name: str
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    total_runs: int
    best_run_id: Optional[str] = None
    best_run_number: Optional[int] = None
    best_accuracy: Optional[float] = None
    average_accuracy: Optional[float] = None
    latest_run_id: Optional[str] = None
    latest_run_number: Optional[int] = None
    latest_run_status: Optional[str] = None
    latest_run_created_at: Optional[datetime] = None


class DatasetMetricSummary(BaseModel):
    """Aggregated performance statistics for a dataset."""

    model_config = ConfigDict(from_attributes=True)

    dataset_id: str
    dataset_name: str
    number_of_experiments: int
    number_of_runs: int
    best_model: Optional[str] = None
    best_accuracy: Optional[float] = None


class RunComparisonItem(BaseModel):
    """Detailed run metrics and configuration for side-by-side comparison."""

    model_config = ConfigDict(from_attributes=True)

    run_id: str
    run_number: int
    experiment_id: str
    experiment_name: str
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    model: Optional[str] = None
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    roc_auc: Optional[float] = None
    duration: Optional[float] = None
    training_configuration: Optional[dict[str, Any]] = None
    completed_at: Optional[datetime] = None


# Generic Envelope Responses
class MetricsOverviewResponse(BaseModel):
    data: MetricsOverview


class ModelMetricsResponse(BaseModel):
    data: List[ModelMetricSummary]


class ExperimentMetricsResponse(BaseModel):
    data: List[ExperimentMetricSummary]


class DatasetMetricsResponse(BaseModel):
    data: List[DatasetMetricSummary]


class RunComparisonResponse(BaseModel):
    data: List[RunComparisonItem]
