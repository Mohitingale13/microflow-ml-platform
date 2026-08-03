"""
metrics.py — FastAPI router for historical analytics and metrics dashboard.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.metrics import (
    DatasetMetricsResponse,
    ExperimentMetricsResponse,
    MetricsOverviewResponse,
    ModelMetricsResponse,
    RunComparisonResponse,
)
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


def get_metrics_service() -> MetricsService:
    return MetricsService()


@router.get(
    "/overview",
    response_model=MetricsOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get global metrics overview",
)
def get_metrics_overview(
    db: Session = Depends(get_db),
    service: MetricsService = Depends(get_metrics_service),
) -> dict:
    """Return system-wide aggregated metrics across all experiments."""
    data = service.get_overview(db)
    return {"data": data}


@router.get(
    "/models",
    response_model=ModelMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get model leaderboard metrics",
)
def get_model_metrics(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    experiment_id: Optional[str] = Query(None, description="Filter by experiment ID"),
    db: Session = Depends(get_db),
    service: MetricsService = Depends(get_metrics_service),
) -> dict:
    """Return aggregated statistics grouped by model family."""
    data = service.get_model_metrics(
        db, dataset_id=dataset_id, experiment_id=experiment_id
    )
    return {"data": data}


@router.get(
    "/experiments",
    response_model=ExperimentMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get experiment performance metrics",
)
def get_experiment_metrics(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    db: Session = Depends(get_db),
    service: MetricsService = Depends(get_metrics_service),
) -> dict:
    """Return experiment-level statistics and best run performance."""
    data = service.get_experiment_metrics(
        db, dataset_id=dataset_id, model_type=model_type
    )
    return {"data": data}


@router.get(
    "/datasets",
    response_model=DatasetMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dataset performance metrics",
)
def get_dataset_metrics(
    db: Session = Depends(get_db),
    service: MetricsService = Depends(get_metrics_service),
) -> dict:
    """Return dataset-level performance statistics."""
    data = service.get_dataset_metrics(db)
    return {"data": data}


@router.get(
    "/runs/compare",
    response_model=RunComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare multiple runs side-by-side",
)
def compare_runs(
    run_ids: str = Query(
        "", description="Comma-separated list of run IDs to compare"
    ),
    db: Session = Depends(get_db),
    service: MetricsService = Depends(get_metrics_service),
) -> dict:
    """Return detailed metrics and configuration for comparison across multiple runs."""
    data = service.compare_runs(run_ids, db)
    return {"data": data}
