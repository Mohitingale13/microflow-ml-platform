"""
dashboard.py — FastAPI router for the Dashboard API.

All endpoints are read-only GET requests.
No business logic lives here — everything is delegated to DashboardService.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.dashboard import (
    DashboardActivityResponse,
    DashboardOverviewResponse,
    DashboardQuickStatsResponse,
    DashboardRecentRunsResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_service() -> DashboardService:
    return DashboardService()


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get platform-wide dashboard overview statistics",
)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """
    Return aggregated platform statistics for the dashboard landing page.

    Includes:
    - Entity counts (datasets, experiments, runs, artifacts, models stored)
    - Run status breakdown (completed, running, failed)
    - Performance aggregates (accuracy, F1, ROC AUC, training duration)
    - Storage usage in bytes
    """
    data = service.get_overview(db)
    return {"data": data}


@router.get(
    "/activity",
    response_model=DashboardActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Get recent platform activity feed",
)
def get_dashboard_activity(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of activity items"),
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """
    Return a unified chronological activity feed ordered newest-first.

    Event types include:
    - dataset_uploaded
    - experiment_created
    - run_created, run_queued, run_completed, run_failed
    - artifact_generated
    - metrics_persisted
    """
    data = service.get_activity(db, limit=limit)
    return {"data": data}


@router.get(
    "/recent-runs",
    response_model=DashboardRecentRunsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get most recent training runs with context",
)
def get_recent_runs(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of runs to return"),
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """
    Return the N most recent runs enriched with experiment name, dataset name,
    model type, status, accuracy, duration, and artifact count.
    """
    data = service.get_recent_runs(db, limit=limit)
    return {"data": data}


@router.get(
    "/quick-stats",
    response_model=DashboardQuickStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get platform highlight / quick stats cards",
)
def get_quick_stats(
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """
    Return highlight statistics for the best-performing assets section:
    - Best model type and its average accuracy
    - Best experiment by accuracy
    - Most used dataset by experiment count
    - Most recent artifact
    """
    data = service.get_quick_stats(db)
    return {"data": data}
