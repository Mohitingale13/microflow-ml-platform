"""
routers/assistant.py — API endpoints for Ask MicroFlow (Natural Language Assistant).

Endpoints:
  POST /api/v1/assistant/query        — Process natural language question
  GET  /api/v1/assistant/recent       — Retrieve recent cached queries
  GET  /api/v1/assistant/suggestions  — Return example suggested questions
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.gemini_service import GeminiService
from app.ai.schemas import AIQueryRequest
from app.db.deps import get_db
from app.repositories.ai_query_repository import AIQueryRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.run_repository import RunRepository
from app.repositories.run_result_repository import RunResultRepository
from app.services.ai_query_service import AIQueryService
from app.utils.response import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["assistant"])


from app.services.ai_evaluation_service import AIEvaluationService

def get_ai_query_service() -> AIQueryService:
    return AIQueryService(
        query_repo=AIQueryRepository(),
        dataset_repo=DatasetRepository(),
        experiment_repo=ExperimentRepository(),
        run_repo=RunRepository(),
        run_result_repo=RunResultRepository(),
        gemini_service=GeminiService(),
    )


def get_ai_evaluation_service() -> AIEvaluationService:
    return AIEvaluationService(
        query_repo=AIQueryRepository(),
        gemini_service=GeminiService(),
    )


@router.post("/evaluate", response_model=ApiResponse)
def trigger_ragas_evaluation(
    limit: int = 10,
    db: Session = Depends(get_db),
    service: AIEvaluationService = Depends(get_ai_evaluation_service),
) -> ApiResponse:
    """
    Manually trigger a batch evaluation of recent assistant queries.
    This will score the Context Relevance, Faithfulness, and Answer Relevance.
    """
    evaluated_count = service.evaluate_batch(limit=limit, db=db)
    return ApiResponse.ok(data={"evaluated_count": evaluated_count}, message=f"Evaluated {evaluated_count} queries.")


@router.post("/query", response_model=ApiResponse)
def ask_assistant(
    body: AIQueryRequest,
    db: Session = Depends(get_db),
    service: AIQueryService = Depends(get_ai_query_service),
) -> ApiResponse:
    """
    Process a natural language user question about the ML platform.

    Uses Gemini intent extraction and repository data retrieval without direct DB access by AI.
    Returns structured answer with reasoning, supporting data, and recommendations.
    """
    response = service.process_query(question=body.question, context=body.context, db=db)
    message = "Cached assistant response retrieved." if response.cached else "Assistant answer generated successfully."
    return ApiResponse.ok(data=response.model_dump(mode="json"), message=message)


@router.get("/recent", response_model=ApiResponse)
def get_recent_queries(
    limit: int = 10,
    db: Session = Depends(get_db),
    service: AIQueryService = Depends(get_ai_query_service),
) -> ApiResponse:
    """Retrieve recently cached assistant questions and answers."""
    recent = service.get_recent_queries(limit=limit, db=db)
    return ApiResponse.ok(data=[r.model_dump(mode="json") for r in recent], message="Recent queries retrieved.")


@router.get("/suggestions", response_model=ApiResponse)
def get_suggested_questions() -> ApiResponse:
    """Return common domain example questions for the frontend UI."""
    suggestions = [
        "Which experiment has the best accuracy?",
        "Show failed runs.",
        "Which Random Forest run performed best?",
        "Compare all XGBoost runs.",
        "What should I improve next?",
        "Summarize active experiments and dataset sizes.",
    ]
    return ApiResponse.ok(data=suggestions, message="Suggestions retrieved.")
