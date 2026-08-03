"""
artifact_service.py — Business logic for Artifact Registry operations.

Responsibilities:
  - Validate artifact existence.
  - Validate storage file exists on disk before serving downloads.
  - Provide listing with global registry stats.
"""

import logging
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.artifact import Artifact, ArtifactType
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.artifact import ArtifactRegistryStats

logger = logging.getLogger(__name__)


class ArtifactService:
    def __init__(self, artifact_repo: ArtifactRepository) -> None:
        self._repo = artifact_repo

    def list_all(self, db: Session) -> list[Artifact]:
        return self._repo.list_all(db)

    def get_by_id(self, artifact_id: str, db: Session) -> Artifact:
        artifact = self._repo.get_by_id(artifact_id, db)
        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact '{artifact_id}' not found",
            )
        return artifact

    def get_run_artifacts(self, run_id: str, db: Session) -> list[Artifact]:
        return self._repo.list_by_run(run_id, db)

    def get_download_path(self, artifact_id: str, db: Session) -> tuple[Artifact, Path]:
        """
        Return the artifact and its validated storage path.

        Raises 404 if the artifact or the file does not exist.
        """
        artifact = self.get_by_id(artifact_id, db)
        path = Path(artifact.storage_path)
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact file not found on disk: '{artifact.filename}'",
            )
        return artifact, path

    def get_registry_stats(self, db: Session) -> ArtifactRegistryStats:
        all_artifacts = self._repo.list_all(db)
        total = len(all_artifacts)
        models = sum(
            1 for a in all_artifacts if a.artifact_type == ArtifactType.trained_model
        )
        json_reports = sum(
            1 for a in all_artifacts if a.artifact_type != ArtifactType.trained_model
        )
        total_bytes = self._repo.total_size_bytes(db)
        return ArtifactRegistryStats(
            total_artifacts=total,
            models_stored=models,
            json_reports=json_reports,
            total_size_bytes=total_bytes,
        )
