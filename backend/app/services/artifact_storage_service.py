"""
artifact_storage_service.py — Handles all file I/O for training artifacts.

Responsibilities:
  - Create the per-run artifact directory.
  - Serialize trained models with joblib.
  - Write JSON metadata files.
  - Compute SHA-256 checksums.
  - Clean up orphan files on failure.

No ORM or HTTP dependencies — pure file system and serialization logic.
"""

import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import Any

import joblib
from sklearn.base import ClassifierMixin

from app.core.config import settings

logger = logging.getLogger(__name__)


class ArtifactStorageError(Exception):
    """Raised when file storage operations fail."""


class ArtifactStorageService:
    """Manages artifact file storage for training runs."""

    def get_artifact_dir(self, run_id: str) -> Path:
        """Return (and create if needed) the storage directory for a run."""
        base = Path(settings.STORAGE_BASE_PATH)
        artifact_dir = base / "artifacts" / run_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir

    def save_model(
        self,
        run_id: str,
        estimator: ClassifierMixin,
    ) -> tuple[str, str, int, str]:
        """
        Serialize trained model to disk with joblib.

        Returns
        -------
        (filename, storage_path_str, file_size_bytes, sha256_checksum)
        """
        artifact_dir = self.get_artifact_dir(run_id)
        filename = "model.joblib"
        path = artifact_dir / filename

        try:
            joblib.dump(estimator, path)
        except Exception as exc:
            raise ArtifactStorageError(f"Failed to serialize model: {exc}") from exc

        size = path.stat().st_size
        checksum = self._compute_sha256(path)
        logger.info("Model saved: path=%s size=%d sha256=%s", path, size, checksum)
        return filename, str(path), size, checksum

    def save_json(
        self,
        run_id: str,
        filename: str,
        data: Any,
    ) -> tuple[str, str, int, str]:
        """
        Write data as a pretty-printed JSON file.

        Returns
        -------
        (filename, storage_path_str, file_size_bytes, sha256_checksum)
        """
        artifact_dir = self.get_artifact_dir(run_id)
        path = artifact_dir / filename

        try:
            content = json.dumps(data, indent=2, default=str)
            path.write_text(content, encoding="utf-8")
        except Exception as exc:
            raise ArtifactStorageError(
                f"Failed to write JSON artifact '{filename}': {exc}"
            ) from exc

        size = path.stat().st_size
        checksum = self._compute_sha256(path)
        logger.info("JSON artifact saved: path=%s size=%d", path, size)
        return filename, str(path), size, checksum

    def cleanup_run_directory(self, run_id: str) -> None:
        """Remove the entire artifact directory for a run (rollback on failure)."""
        artifact_dir = Path(settings.STORAGE_BASE_PATH) / "artifacts" / run_id
        if artifact_dir.exists():
            try:
                shutil.rmtree(artifact_dir)
                logger.info("Cleaned up artifact directory: %s", artifact_dir)
            except Exception as exc:
                logger.error("Failed to clean up artifact directory %s: %s", artifact_dir, exc)

    @staticmethod
    def _compute_sha256(path: Path) -> str:
        """Compute SHA-256 hex digest of a file."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
