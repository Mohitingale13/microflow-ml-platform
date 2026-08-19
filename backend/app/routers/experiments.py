import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentListItem,
    ExperimentResponse,
    ExperimentUpdate,
    RunListItem,
)
from app.schemas.investigator import InvestigateRequest
from app.services.experiment_service import ExperimentService
from app.utils.response import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/experiments", tags=["experiments"])


def get_experiment_service() -> ExperimentService:
    return ExperimentService(
        experiment_repo=ExperimentRepository(),
        dataset_repo=DatasetRepository(),
    )


# ─── Collection endpoints ────────────────────────────────────────────────────

@router.get("", response_model=ApiResponse)
def list_experiments(
    db: Session = Depends(get_db),
    service: ExperimentService = Depends(get_experiment_service),
) -> ApiResponse:
    experiments = service.get_all(db)
    items = [
        ExperimentListItem.model_validate(e).model_dump(mode="json")
        for e in experiments
    ]
    return ApiResponse.ok(data=items, message=f"{len(items)} experiment(s) found")


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ApiResponse)
def create_experiment(
    payload: ExperimentCreate,
    db: Session = Depends(get_db),
    service: ExperimentService = Depends(get_experiment_service),
) -> ApiResponse:
    experiment = service.create(
        name=payload.name,
        dataset_id=payload.dataset_id,
        description=payload.description,
        objective=payload.objective,
        default_configuration=payload.default_configuration,
        tags=payload.tags,
        db=db,
    )
    return ApiResponse.ok(
        data=ExperimentResponse.model_validate(experiment).model_dump(mode="json"),
        message="Experiment created successfully",
    )


# ─── Item endpoints ──────────────────────────────────────────────────────────

@router.get("/{experiment_id}", response_model=ApiResponse)
def get_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    service: ExperimentService = Depends(get_experiment_service),
) -> ApiResponse:
    experiment = service.get_by_id(experiment_id, db)
    return ApiResponse.ok(
        data=ExperimentResponse.model_validate(experiment).model_dump(mode="json")
    )


@router.put("/{experiment_id}", response_model=ApiResponse)
def update_experiment(
    experiment_id: str,
    payload: ExperimentUpdate,
    db: Session = Depends(get_db),
    service: ExperimentService = Depends(get_experiment_service),
) -> ApiResponse:
    # Only pass fields that were explicitly provided by the client
    updates: dict[str, Any] = payload.model_dump(exclude_unset=True)
    experiment = service.update(experiment_id, updates=updates, db=db)
    return ApiResponse.ok(
        data=ExperimentResponse.model_validate(experiment).model_dump(mode="json"),
        message="Experiment updated successfully",
    )


@router.delete("/{experiment_id}", response_model=ApiResponse)
def delete_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    service: ExperimentService = Depends(get_experiment_service),
) -> ApiResponse:
    service.delete(experiment_id, db)
    return ApiResponse.ok(message="Experiment deleted successfully")


# ─── Nested runs ─────────────────────────────────────────────────────────────

@router.get("/{experiment_id}/runs", response_model=ApiResponse)
def list_experiment_runs(
    experiment_id: str,
    db: Session = Depends(get_db),
    service: ExperimentService = Depends(get_experiment_service),
) -> ApiResponse:
    # Validates experiment exists, then returns its runs via RunRepository
    from app.repositories.run_repository import RunRepository

    service.get_by_id(experiment_id, db)  # 404 if not found
    runs = RunRepository().list_by_experiment(experiment_id, db)
    items = [RunListItem.model_validate(r).model_dump(mode="json") for r in runs]
    return ApiResponse.ok(data=items, message=f"{len(items)} run(s) found")


# ─── AI Experiment Strategy ──────────────────────────────────────────────────


@router.post("/{experiment_id}/strategy", response_model=ApiResponse)
def generate_experiment_strategy(
    experiment_id: str,
    db: Session = Depends(get_db),
) -> ApiResponse:
    from app.services.experiment_strategy_service import ExperimentStrategyService

    service = ExperimentStrategyService()
    strategy = service.get_or_generate_strategy(experiment_id, db)
    return ApiResponse.ok(
        data=strategy.model_dump(mode="json"),
        message="AI Experiment Strategy generated successfully" if not strategy.cached else "Cached experiment strategy retrieved.",
    )


# ─── AI Experiment Investigator ──────────────────────────────────────────────


@router.post("/{experiment_id}/investigate", response_model=ApiResponse)
def investigate_experiment(
    experiment_id: str,
    payload: InvestigateRequest,
    db: Session = Depends(get_db),
) -> ApiResponse:
    """Execute bounded, read-only Agentic ML investigation over experiment data."""
    from app.services.investigator_service import InvestigatorService

    if not payload.objective or not payload.objective.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Investigation objective cannot be empty",
        )

    service = InvestigatorService()
    result = service.investigate_experiment(
        experiment_id=experiment_id,
        objective=payload.objective.strip(),
        db=db,
    )
    return ApiResponse.ok(
        data=result.model_dump(mode="json"),
        message="Investigation completed successfully",
    )
