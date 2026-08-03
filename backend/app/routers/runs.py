import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.run_repository import RunRepository
from app.schemas.experiment import (
    RunCreate,
    RunListItem,
    RunResponse,
    RunUpdate,
)
from app.services.run_service import RunService
from app.utils.response import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/runs", tags=["runs"])


def get_run_service() -> RunService:
    return RunService(
        run_repo=RunRepository(),
        experiment_repo=ExperimentRepository(),
    )


# ── Collection endpoints ───────────────────────────────────────────────────────

@router.get("", response_model=ApiResponse)
def list_runs(
    db: Session = Depends(get_db),
    service: RunService = Depends(get_run_service),
) -> ApiResponse:
    runs = service.get_all(db)
    items = [RunListItem.model_validate(r).model_dump(mode="json") for r in runs]
    return ApiResponse.ok(data=items, message=f"{len(items)} run(s) found")


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ApiResponse)
def create_run(
    payload: RunCreate,
    db: Session = Depends(get_db),
    service: RunService = Depends(get_run_service),
) -> ApiResponse:
    run = service.create(
        experiment_id=payload.experiment_id,
        model_type=payload.model_type,
        training_configuration=payload.training_configuration,
        notes=payload.notes,
        db=db,
    )
    return ApiResponse.ok(
        data=RunResponse.model_validate(run).model_dump(mode="json"),
        message="Run created successfully",
    )


# ── Item endpoints ─────────────────────────────────────────────────────────────

@router.get("/{run_id}", response_model=ApiResponse)
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
    service: RunService = Depends(get_run_service),
) -> ApiResponse:
    run = service.get_by_id(run_id, db)
    return ApiResponse.ok(
        data=RunResponse.model_validate(run).model_dump(mode="json")
    )


@router.put("/{run_id}", response_model=ApiResponse)
def update_run(
    run_id: str,
    payload: RunUpdate,
    db: Session = Depends(get_db),
    service: RunService = Depends(get_run_service),
) -> ApiResponse:
    updates: dict[str, Any] = payload.model_dump(exclude_unset=True)
    run = service.update(run_id, updates=updates, db=db)
    return ApiResponse.ok(
        data=RunResponse.model_validate(run).model_dump(mode="json"),
        message="Run updated successfully",
    )


@router.delete("/{run_id}", response_model=ApiResponse)
def delete_run(
    run_id: str,
    db: Session = Depends(get_db),
    service: RunService = Depends(get_run_service),
) -> ApiResponse:
    service.delete(run_id, db)
    return ApiResponse.ok(message="Run deleted successfully")


# ── State machine endpoints ────────────────────────────────────────────────────

@router.post("/{run_id}/queue", response_model=ApiResponse)
def queue_run(
    run_id: str,
    db: Session = Depends(get_db),
    service: RunService = Depends(get_run_service),
) -> ApiResponse:
    run = service.queue(run_id, db)
    return ApiResponse.ok(
        data=RunResponse.model_validate(run).model_dump(mode="json"),
        message="Run queued successfully",
    )


@router.post("/{run_id}/cancel", response_model=ApiResponse)
def cancel_run(
    run_id: str,
    db: Session = Depends(get_db),
    service: RunService = Depends(get_run_service),
) -> ApiResponse:
    run = service.cancel(run_id, db)
    return ApiResponse.ok(
        data=RunResponse.model_validate(run).model_dump(mode="json"),
        message="Run cancelled successfully",
    )
