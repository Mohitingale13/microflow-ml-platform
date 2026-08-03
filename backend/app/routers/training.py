"""
training.py — Training Engine router.

Exposes:
  POST /api/v1/runs/{run_id}/execute
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.run_repository import RunRepository
from app.schemas.training import (
    ExecuteRunRequest,
    ExecuteRunResponse,
    EvaluationMetrics,
)
from app.schemas.experiment import RunResponse
from app.services.run_service import RunService
from app.services.training_service import TrainingService
from app.utils.response import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/runs", tags=["training"])


def get_training_service() -> TrainingService:
    return TrainingService(
        run_repo=RunRepository(),
        experiment_repo=ExperimentRepository(),
        dataset_repo=DatasetRepository(),
    )


def get_run_service() -> RunService:
    return RunService(
        run_repo=RunRepository(),
        experiment_repo=ExperimentRepository(),
    )


@router.post("/{run_id}/execute", response_model=ApiResponse)
def execute_run(
    run_id: str,
    payload: ExecuteRunRequest,
    db: Session = Depends(get_db),
    training_service: TrainingService = Depends(get_training_service),
    run_service: RunService = Depends(get_run_service),
) -> ApiResponse:
    """
    Execute training for a queued Run.

    Transitions the Run:
      queued → running → completed  (success)
      queued → running → failed     (error)

    Returns evaluation metrics in the response body.
    """
    metrics = training_service.execute(
        run_id,
        target_column=payload.target_column,
        test_split=payload.test_split,
        db=db,
    )

    # Fetch updated run for the response
    run = run_service.get_by_id(run_id, db)

    response_data = ExecuteRunResponse(
        run_id=run.id,
        status=run.status.value,
        model_type=run.model_type,
        metrics=EvaluationMetrics(
            accuracy=metrics["accuracy"],
            precision=metrics["precision"],
            recall=metrics["recall"],
            f1_score=metrics["f1_score"],
            roc_auc=metrics.get("roc_auc"),
            confusion_matrix=metrics["confusion_matrix"],
        ),
    )

    return ApiResponse.ok(
        data=response_data.model_dump(),
        message="Training completed successfully",
    )
