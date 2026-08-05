import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.schemas.dataset import (
    DatasetListItem,
    DatasetPreviewResponse,
    DatasetResponse,
    DatasetStatisticsResponse,
)
from app.services.dataset_service import DatasetService
from app.ai.gemini_service import GeminiService
from app.repositories.dataset_ai_analysis_repository import DatasetAIAnalysisRepository
from app.services.dataset_ai_service import DatasetAIService
from app.utils.response import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasets", tags=["datasets"])


def get_dataset_service() -> DatasetService:
    return DatasetService(
        repository=DatasetRepository(),
        experiment_repository=ExperimentRepository(),
    )


def get_dataset_ai_service() -> DatasetAIService:
    return DatasetAIService(
        dataset_repo=DatasetRepository(),
        analysis_repo=DatasetAIAnalysisRepository(),
        gemini_service=GeminiService(),
        dataset_service=get_dataset_service(),
    )


@router.get("", response_model=ApiResponse)
def list_datasets(
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
) -> ApiResponse:
    datasets = service.get_all(db)
    items = [DatasetListItem.model_validate(d).model_dump(mode="json") for d in datasets]
    return ApiResponse.ok(data=items, message=f"{len(items)} dataset(s) found")


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ApiResponse)
async def upload_dataset(
    name: str = Form(..., min_length=1, max_length=255),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
) -> ApiResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV files are accepted",
        )
    content = await file.read()
    dataset = service.upload(
        content=content,
        filename=file.filename,
        name=name,
        description=description,
        db=db,
    )
    return ApiResponse.ok(
        data=DatasetResponse.model_validate(dataset).model_dump(mode="json"),
        message="Dataset uploaded and analysed successfully",
    )


@router.get("/{dataset_id}", response_model=ApiResponse)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
) -> ApiResponse:
    dataset = service.get_by_id(dataset_id, db)
    return ApiResponse.ok(
        data=DatasetResponse.model_validate(dataset).model_dump(mode="json")
    )


@router.get("/{dataset_id}/preview", response_model=ApiResponse)
def get_dataset_preview(
    dataset_id: str,
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
) -> ApiResponse:
    preview = service.get_preview(dataset_id, db)
    return ApiResponse.ok(data=DatasetPreviewResponse(**preview).model_dump(mode="json"))


@router.get("/{dataset_id}/statistics", response_model=ApiResponse)
def get_dataset_statistics(
    dataset_id: str,
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
) -> ApiResponse:
    stats = service.get_statistics(dataset_id, db)
    payload = DatasetStatisticsResponse(
        dataset_id=dataset_id, statistics=stats
    ).model_dump(mode="json")
    return ApiResponse.ok(data=payload)


@router.delete("/{dataset_id}", response_model=ApiResponse)
def delete_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
) -> ApiResponse:
    service.delete(dataset_id, db)
    return ApiResponse.ok(message="Dataset deleted successfully")


@router.post("/{dataset_id}/analyze", response_model=ApiResponse)
def analyze_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    service: DatasetAIService = Depends(get_dataset_ai_service),
) -> ApiResponse:
    """
    Generate or retrieve a cached AI Dataset Intelligence review for a ready dataset.
    """
    analysis = service.get_or_generate_analysis(dataset_id=dataset_id, db=db)
    message = (
        "Cached dataset analysis retrieved."
        if analysis.cached
        else "AI Dataset Intelligence generated successfully."
    )
    return ApiResponse.ok(data=analysis.model_dump(mode="json"), message=message)
