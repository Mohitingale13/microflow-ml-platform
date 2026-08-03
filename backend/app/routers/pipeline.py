"""
pipeline.py — FastAPI router for the Pipeline Visualization module.

All endpoints are read-only GET requests.
No data is created or modified through this router.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.pipeline import (
    PipelineGraphResponse,
    PipelineLineageResponse,
    PipelineOverviewResponse,
    PipelineRunsResponse,
)
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


def get_pipeline_service() -> PipelineService:
    return PipelineService()


@router.get(
    "/overview",
    response_model=PipelineOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get pipeline execution overview statistics",
)
def get_pipeline_overview(
    db: Session = Depends(get_db),
    service: PipelineService = Depends(get_pipeline_service),
) -> dict:
    """Return global pipeline execution statistics (total runs, status counts, artifact count, avg duration)."""
    data = service.get_overview(db)
    return {"data": data}


@router.get(
    "/runs",
    response_model=PipelineRunsResponse,
    status_code=status.HTTP_200_OK,
    summary="List all pipeline runs with context",
)
def get_pipeline_runs(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    experiment_id: Optional[str] = Query(None, description="Filter by experiment ID"),
    status: Optional[str] = Query(None, description="Filter by run status"),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    db: Session = Depends(get_db),
    service: PipelineService = Depends(get_pipeline_service),
) -> dict:
    """
    Return all runs enriched with experiment, dataset, result metrics, and artifact counts.
    Supports optional filtering by dataset, experiment, status, and model type.
    """
    data = service.get_runs(
        db,
        dataset_id=dataset_id,
        experiment_id=experiment_id,
        status=status,
        model_type=model_type,
    )
    return {"data": data}


@router.get(
    "/lineage",
    response_model=PipelineLineageResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dataset lineage tree",
)
def get_pipeline_lineage(
    db: Session = Depends(get_db),
    service: PipelineService = Depends(get_pipeline_service),
) -> dict:
    """
    Return hierarchical lineage: Dataset → Experiments → Runs → Artifacts.
    Used for the collapsible lineage tree visualization.
    """
    data = service.get_lineage(db)
    return {"data": data}


@router.get(
    "/{run_id}",
    response_model=PipelineGraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full execution graph and timeline for a run",
)
def get_pipeline_graph(
    run_id: str,
    db: Session = Depends(get_db),
    service: PipelineService = Depends(get_pipeline_service),
) -> dict:
    """
    Return the full 8-stage execution graph and chronological timeline for a specific run.
    Each node includes status, timestamps, duration, and navigation links.
    """
    result = service.get_pipeline_graph(run_id, db)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )
    return {"data": result["graph"], "timeline": result["timeline"]}
