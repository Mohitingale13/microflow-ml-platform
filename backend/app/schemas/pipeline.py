"""
pipeline.py — Pydantic response schemas for the Pipeline Visualization module.

Defines response models for:
  - Pipeline overview statistics
  - Pipeline run summaries (execution table)
  - Pipeline execution graph (stages + edges)
  - Pipeline execution timeline
  - Dataset lineage tree
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


# ─── Node & Graph Types ────────────────────────────────────────────────────────

class PipelineNode(BaseModel):
    """A single stage node in the pipeline execution graph."""

    model_config = ConfigDict(from_attributes=True)

    id: str                         # e.g. "dataset", "experiment", "training"
    label: str                      # Display label
    stage_type: str                 # Canonical stage type identifier
    status: str                     # "pending", "running", "completed", "failed", "skipped"
    icon: str                       # Lucide icon name
    color: str                      # CSS color hint for the node
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    detail: Optional[Dict[str, Any]] = None   # Stage-specific metadata (model type, row count, etc.)
    link: Optional[str] = None                # Frontend route for navigation


class PipelineEdge(BaseModel):
    """Directed connection between two pipeline nodes."""

    model_config = ConfigDict(from_attributes=True)

    source: str      # Source node id
    target: str      # Target node id
    active: bool = True   # False if target has not been reached yet


class PipelineGraph(BaseModel):
    """Full execution graph for a single run."""

    model_config = ConfigDict(from_attributes=True)

    run_id: str
    run_number: int
    experiment_id: str
    experiment_name: str
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    status: str
    nodes: List[PipelineNode]
    edges: List[PipelineEdge]


# ─── Timeline ─────────────────────────────────────────────────────────────────

class TimelineEvent(BaseModel):
    """A single chronological event in the pipeline execution timeline."""

    model_config = ConfigDict(from_attributes=True)

    order: int
    event: str                        # Human-readable event name
    stage_type: str                   # Stage identifier
    status: str                       # "completed", "pending", "failed", "running"
    timestamp: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    detail: Optional[str] = None


class PipelineTimeline(BaseModel):
    """Ordered list of execution events for a run."""

    model_config = ConfigDict(from_attributes=True)

    run_id: str
    run_number: int
    experiment_name: str
    total_duration_seconds: Optional[float] = None
    events: List[TimelineEvent]


# ─── Run Summary (Execution Table) ────────────────────────────────────────────

class PipelineRunSummary(BaseModel):
    """A single row in the pipeline execution table."""

    model_config = ConfigDict(from_attributes=True)

    run_id: str
    run_number: int
    experiment_id: str
    experiment_name: str
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    model: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    artifact_count: int = 0
    accuracy: Optional[float] = None


# ─── Overview ─────────────────────────────────────────────────────────────────

class PipelineOverview(BaseModel):
    """Global pipeline execution statistics."""

    model_config = ConfigDict(from_attributes=True)

    total_pipelines: int          # All runs that have been executed (queued+)
    running: int
    completed: int
    failed: int
    queued: int
    draft: int
    average_duration_seconds: Optional[float] = None
    total_artifacts_produced: int
    success_rate: float


# ─── Lineage ──────────────────────────────────────────────────────────────────

class LineageArtifact(BaseModel):
    """Artifact node in the lineage tree."""

    model_config = ConfigDict(from_attributes=True)

    artifact_id: str
    artifact_type: str
    filename: str
    created_at: Optional[datetime] = None


class LineageRun(BaseModel):
    """Run node in the lineage tree."""

    model_config = ConfigDict(from_attributes=True)

    run_id: str
    run_number: int
    model: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    artifacts: List[LineageArtifact] = []


class LineageExperiment(BaseModel):
    """Experiment node in the lineage tree."""

    model_config = ConfigDict(from_attributes=True)

    experiment_id: str
    experiment_name: str
    status: str
    created_at: Optional[datetime] = None
    total_runs: int
    completed_runs: int
    runs: List[LineageRun] = []


class LineageDataset(BaseModel):
    """Dataset root node in the lineage tree."""

    model_config = ConfigDict(from_attributes=True)

    dataset_id: str
    dataset_name: str
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    created_at: Optional[datetime] = None
    total_experiments: int
    total_runs: int
    experiments: List[LineageExperiment] = []


# ─── Envelope Responses ───────────────────────────────────────────────────────

class PipelineOverviewResponse(BaseModel):
    data: PipelineOverview


class PipelineRunsResponse(BaseModel):
    data: List[PipelineRunSummary]


class PipelineGraphResponse(BaseModel):
    data: PipelineGraph
    timeline: PipelineTimeline


class PipelineLineageResponse(BaseModel):
    data: List[LineageDataset]
