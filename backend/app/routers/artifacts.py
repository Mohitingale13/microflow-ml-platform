"""
artifacts.py — Artifact Registry & Run Result router.

Endpoints:
  GET  /api/v1/artifacts                     — list all artifacts
  GET  /api/v1/artifacts/stats               — registry statistics
  GET  /api/v1/artifacts/{artifact_id}       — artifact metadata
  GET  /api/v1/artifacts/{artifact_id}/download — file download
  GET  /api/v1/runs/{run_id}/result          — persisted run result (metrics)
  GET  /api/v1/runs/{run_id}/artifacts       — artifacts for a specific run
"""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.run_result_repository import RunResultRepository
from app.schemas.artifact import (
    ArtifactListItem,
    ArtifactRegistryStats,
    ArtifactResponse,
    RunResultResponse,
)
from app.services.artifact_service import ArtifactService
from app.services.run_result_service import RunResultService
from app.utils.response import ApiResponse

logger = logging.getLogger(__name__)

# Two separate routers to match the endpoint prefixes cleanly
artifacts_router = APIRouter(prefix="/artifacts", tags=["artifacts"])
run_artifacts_router = APIRouter(prefix="/runs", tags=["artifacts"])

router = APIRouter()  # composite — included in api_router


def get_artifact_service() -> ArtifactService:
    return ArtifactService(artifact_repo=ArtifactRepository())


def get_run_result_service() -> RunResultService:
    return RunResultService(run_result_repo=RunResultRepository())


# ── Global Artifact Registry ───────────────────────────────────────────────────

@artifacts_router.get("/stats", response_model=ApiResponse)
def get_registry_stats(
    db: Session = Depends(get_db),
    service: ArtifactService = Depends(get_artifact_service),
) -> ApiResponse:
    stats = service.get_registry_stats(db)
    return ApiResponse.ok(data=stats.model_dump(), message="Registry stats retrieved")


@artifacts_router.get("", response_model=ApiResponse)
def list_artifacts(
    db: Session = Depends(get_db),
    service: ArtifactService = Depends(get_artifact_service),
) -> ApiResponse:
    artifacts = service.list_all(db)
    items = [ArtifactListItem.model_validate(a).model_dump(mode="json") for a in artifacts]
    return ApiResponse.ok(data=items, message=f"{len(items)} artifact(s) found")


@artifacts_router.get("/{artifact_id}", response_model=ApiResponse)
def get_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    service: ArtifactService = Depends(get_artifact_service),
) -> ApiResponse:
    artifact = service.get_by_id(artifact_id, db)
    return ApiResponse.ok(
        data=ArtifactResponse.model_validate(artifact).model_dump(mode="json")
    )


@artifacts_router.get("/{artifact_id}/download")
def download_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    service: ArtifactService = Depends(get_artifact_service),
) -> FileResponse:
    artifact, path = service.get_download_path(artifact_id, db)
    return FileResponse(
        path=str(path),
        media_type=artifact.mime_type,
        filename=artifact.filename,
    )


# ── Run-scoped Artifact endpoints ──────────────────────────────────────────────

@run_artifacts_router.get("/{run_id}/result", response_model=ApiResponse)
def get_run_result(
    run_id: str,
    db: Session = Depends(get_db),
    service: RunResultService = Depends(get_run_result_service),
) -> ApiResponse:
    result = service.get_by_run_id(run_id, db)
    if not result:
        return ApiResponse.ok(data=None, message="No result found for this run")
    return ApiResponse.ok(
        data=RunResultResponse.model_validate(result).model_dump(mode="json"),
        message="Run result retrieved",
    )


@run_artifacts_router.get("/{run_id}/artifacts", response_model=ApiResponse)
def get_run_artifacts(
    run_id: str,
    db: Session = Depends(get_db),
    service: ArtifactService = Depends(get_artifact_service),
) -> ApiResponse:
    artifacts = service.get_run_artifacts(run_id, db)
    items = [ArtifactListItem.model_validate(a).model_dump(mode="json") for a in artifacts]
    return ApiResponse.ok(data=items, message=f"{len(items)} artifact(s) found")


# Register sub-routers
router.include_router(artifacts_router)
router.include_router(run_artifacts_router)
