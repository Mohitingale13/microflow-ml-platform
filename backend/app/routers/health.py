from datetime import datetime, timezone
from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.utils.response import ApiResponse
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse)
def health_check() -> ApiResponse:
    payload = HealthResponse(
        service="microflow-backend",
        version="1.0.0",
        status="healthy",
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
    )
    return ApiResponse.ok(data=payload.model_dump(mode="json"), message="Service is healthy")
