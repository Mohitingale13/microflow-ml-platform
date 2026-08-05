"""
routers/ai.py — API endpoints for AI-powered run analysis.

Endpoints:
  POST /api/v1/runs/{run_id}/review   — AI Run Review (Milestone 1)
  POST /api/v1/runs/compare            — AI Run Comparison (Milestone 2)

Neither endpoint contains business logic; all logic lives in the service layer.
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.gemini_service import GeminiService
from app.db.deps import get_db
from app.repositories.ai_review_repository import AIReviewRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.run_repository import RunRepository
from app.repositories.run_result_repository import RunResultRepository
from app.repositories.run_comparison_repository import RunComparisonRepository
from app.services.ai_review_service import AIReviewService
from app.services.run_comparison_service import RunComparisonService
from app.utils.response import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/runs", tags=["ai"])


# ── Dependency factories ───────────────────────────────────────────────────────

def get_ai_review_service() -> AIReviewService:
    return AIReviewService(
        run_repo=RunRepository(),
        experiment_repo=ExperimentRepository(),
        run_result_repo=RunResultRepository(),
        dataset_repo=DatasetRepository(),
        ai_review_repo=AIReviewRepository(),
        gemini_service=GeminiService(),
    )


def get_run_comparison_service() -> RunComparisonService:
    return RunComparisonService(
        run_repo=RunRepository(),
        experiment_repo=ExperimentRepository(),
        run_result_repo=RunResultRepository(),
        dataset_repo=DatasetRepository(),
        comparison_repo=RunComparisonRepository(),
        gemini_service=GeminiService(),
    )


# ── Request schemas ────────────────────────────────────────────────────────────

class CompareRunsRequest(BaseModel):
    run_a_id: str
    run_b_id: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/{run_id}/review", response_model=ApiResponse)
def generate_run_review(
    run_id: str,
    db: Session = Depends(get_db),
    service: AIReviewService = Depends(get_ai_review_service),
) -> ApiResponse:
    """
    Generate or retrieve a cached AI engineering review for a completed run.

    Returns a cached review instantly if one exists for the current run state.
    Otherwise calls Gemini, parses the structured response, caches it, and
    returns the result.

    Requires the run to be in 'completed' status.
    Requires GEMINI_API_KEY to be configured.
    """
    review = service.get_or_generate_review(run_id=run_id, db=db)
    message = "Cached review retrieved." if review.cached else "AI review generated successfully."
    return ApiResponse.ok(data=review.model_dump(mode="json"), message=message)


@router.post("/compare", response_model=ApiResponse)
def compare_runs(
    body: CompareRunsRequest,
    db: Session = Depends(get_db),
    service: RunComparisonService = Depends(get_run_comparison_service),
) -> ApiResponse:
    """
    Generate or retrieve a cached AI engineering comparison for two completed runs.

    Both runs must belong to the same experiment and be in 'completed' status.
    Returns a cached comparison instantly if an identical run pair with the same
    prompt hash already exists.

    Request body:
      run_a_id — UUID of the baseline run.
      run_b_id — UUID of the challenger run.

    Requires GEMINI_API_KEY to be configured.
    """
    comparison = service.get_or_generate_comparison(
        run_a_id=body.run_a_id,
        run_b_id=body.run_b_id,
        db=db,
    )
    message = (
        "Cached comparison retrieved."
        if comparison.cached
        else "AI comparison generated successfully."
    )
    return ApiResponse.ok(data=comparison.model_dump(mode="json"), message=message)
