"""
dashboard.py — Pydantic schemas for the Dashboard API.

Defines response models for:
  - Platform overview statistics
  - Activity feed items
  - Recent runs with experiment/dataset context
  - Quick stats (best model, best dataset, most active experiment)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


# ── Overview ──────────────────────────────────────────────────────────────────

class DashboardOverview(BaseModel):
    """Platform-wide summary statistics for the dashboard landing page."""

    model_config = ConfigDict(from_attributes=True)

    # Counts
    total_datasets: int
    total_experiments: int
    total_runs: int
    completed_runs: int
    running_runs: int
    failed_runs: int
    total_artifacts: int
    models_stored: int

    # Performance aggregates (None when no runs have completed)
    success_rate: float
    average_accuracy: Optional[float] = None
    average_f1: Optional[float] = None
    average_roc_auc: Optional[float] = None
    average_training_duration_seconds: Optional[float] = None

    # Storage
    storage_used_bytes: int


class DashboardOverviewResponse(BaseModel):
    data: DashboardOverview


# ── Activity Feed ─────────────────────────────────────────────────────────────

class ActivityItem(BaseModel):
    """A single timestamped platform event for the activity feed."""

    model_config = ConfigDict(from_attributes=True)

    event_type: str          # e.g. "dataset_uploaded", "run_completed"
    entity_type: str         # "dataset" | "experiment" | "run" | "artifact" | "result"
    entity_id: str
    entity_name: str
    description: str
    occurred_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class DashboardActivityResponse(BaseModel):
    data: List[ActivityItem]


# ── Recent Runs ───────────────────────────────────────────────────────────────

class RecentRunItem(BaseModel):
    """A run summary row for the Recent Runs table."""

    model_config = ConfigDict(from_attributes=True)

    run_id: str
    run_number: int
    experiment_id: str
    experiment_name: str
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    model: Optional[str] = None
    status: str
    accuracy: Optional[float] = None
    duration_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    artifact_count: int = 0


class DashboardRecentRunsResponse(BaseModel):
    data: List[RecentRunItem]


# ── Quick Stats ───────────────────────────────────────────────────────────────

class QuickStats(BaseModel):
    """Highlight cards: best model, best experiment, best dataset."""

    model_config = ConfigDict(from_attributes=True)

    # Best performing model
    best_model_type: Optional[str] = None
    best_model_accuracy: Optional[float] = None
    best_model_run_count: Optional[int] = None

    # Best experiment
    best_experiment_id: Optional[str] = None
    best_experiment_name: Optional[str] = None
    best_experiment_accuracy: Optional[float] = None
    best_experiment_run_count: Optional[int] = None

    # Most used dataset
    most_used_dataset_id: Optional[str] = None
    most_used_dataset_name: Optional[str] = None
    most_used_dataset_experiment_count: Optional[int] = None

    # Most recent artifact
    latest_artifact_id: Optional[str] = None
    latest_artifact_filename: Optional[str] = None
    latest_artifact_type: Optional[str] = None
    latest_artifact_run_id: Optional[str] = None
    latest_artifact_created_at: Optional[datetime] = None


class DashboardQuickStatsResponse(BaseModel):
    data: QuickStats
