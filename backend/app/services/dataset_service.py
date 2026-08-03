import hashlib
import io
import logging
from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.dataset import Dataset, DatasetStatus
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.utils.csv_validator import validate_csv_content
from app.utils.file_storage import (
    delete_dataset_files,
    get_raw_csv_path,
    save_metadata_json,
    save_raw_csv,
)

logger = logging.getLogger(__name__)


class DatasetService:
    def __init__(
        self,
        repository: DatasetRepository,
        experiment_repository: ExperimentRepository | None = None,
    ) -> None:
        self._repo = repository
        self._experiment_repo = experiment_repository or ExperimentRepository()

    def get_all(self, db: Session) -> list[Dataset]:
        return self._repo.list_all(db)

    def get_by_id(self, dataset_id: str, db: Session) -> Dataset:
        dataset = self._repo.get_by_id(dataset_id, db)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset '{dataset_id}' not found",
            )
        return dataset

    def upload(
        self,
        content: bytes,
        filename: str,
        name: str,
        description: str | None,
        db: Session,
    ) -> Dataset:
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds the maximum upload size of {settings.MAX_UPLOAD_SIZE_MB} MB",
            )

        validation = validate_csv_content(content)
        if not validation.valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=validation.error,
            )

        file_hash = hashlib.sha256(content).hexdigest()
        existing = self._repo.get_by_hash(file_hash, db)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A dataset with identical content already exists (id: {existing.id})",
            )

        dataset = self._repo.create(
            db,
            name=name,
            description=description,
            original_filename=filename,
            file_hash=file_hash,
            file_size_bytes=len(content),
            storage_path="",
        )

        csv_path = save_raw_csv(dataset.id, content)
        self._repo.update(db, dataset, storage_path=csv_path)

        self._analyse(dataset, content, db)
        return dataset

    def _analyse(self, dataset: Dataset, content: bytes, db: Session) -> None:
        self._repo.update(db, dataset, status=DatasetStatus.analysing)
        try:
            df = pd.read_csv(io.BytesIO(content))

            column_names: list[str] = df.columns.tolist()
            dtypes: dict[str, str] = {
                str(col): str(dtype) for col, dtype in df.dtypes.items()
            }  # type: ignore
            missing_values: dict[str, int] = {
                str(col): int(count) for col, count in df.isnull().sum().items()
            }  # type: ignore

            metadata: dict[str, Any] = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "column_names": column_names,
                "dtypes": dtypes,
                "missing_values": missing_values,
                "numeric_columns": df.select_dtypes(include="number").columns.tolist(),
                "categorical_columns": df.select_dtypes(exclude="number").columns.tolist(),
            }

            save_metadata_json(dataset.id, metadata)

            self._repo.update(
                db,
                dataset,
                row_count=len(df),
                column_count=len(df.columns),
                column_names=column_names,
                dtypes=dtypes,
                missing_values=missing_values,
                status=DatasetStatus.ready,
            )
            logger.info(
                "Dataset %s analysed: %d rows, %d columns",
                dataset.id,
                len(df),
                len(df.columns),
            )
        except Exception as exc:
            logger.error("Analysis failed for dataset %s: %s", dataset.id, exc)
            self._repo.update(db, dataset, status=DatasetStatus.error)

    def get_preview(self, dataset_id: str, db: Session) -> dict[str, Any]:
        dataset = self.get_by_id(dataset_id, db)
        csv_path = get_raw_csv_path(dataset_id)
        if not csv_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset file not found on disk",
            )
        df = pd.read_csv(csv_path, nrows=100)
        return {
            "columns": df.columns.tolist(),
            "rows": df.where(pd.notnull(df), None).to_dict(orient="records"),  # type: ignore
            "total_rows": dataset.row_count,
        }

    def get_statistics(self, dataset_id: str, db: Session) -> dict[str, Any]:
        self.get_by_id(dataset_id, db)
        csv_path = get_raw_csv_path(dataset_id)
        if not csv_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset file not found on disk",
            )

        df = pd.read_csv(csv_path)
        stats: dict[str, Any] = {}

        for col in df.select_dtypes(include="number").columns:
            series = df[col]
            stats[col] = {
                "type": "numeric",
                "min": _safe_float(series.min()),
                "max": _safe_float(series.max()),
                "mean": _safe_float(series.mean()),
                "median": _safe_float(series.median()),
                "std": _safe_float(series.std()),
                "missing_count": int(series.isnull().sum()),  # type: ignore
            }

        for col in df.select_dtypes(exclude="number").columns:
            series = df[col]
            non_null = series.dropna()
            most_frequent = (
                str(non_null.value_counts().idxmax()) if not non_null.empty else None
            )
            stats[col] = {
                "type": "categorical",
                "unique_values": int(series.nunique()),  # type: ignore
                "most_frequent": most_frequent,
                "missing_count": int(series.isnull().sum()),  # type: ignore
            }

        return stats

    def delete(self, dataset_id: str, db: Session) -> None:
        self.get_by_id(dataset_id, db)
        
        # Check if any experiments are referencing this dataset
        experiments = self._experiment_repo.list_by_dataset(dataset_id, db)
        if experiments:
            names = ", ".join(f"'{exp.name}'" for exp in experiments[:3])
            extra = f" and {len(experiments) - 3} more" if len(experiments) > 3 else ""
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot delete dataset because it is linked to {len(experiments)} experiment(s) "
                    f"({names}{extra}). Delete those experiments first."
                ),
            )

        try:
            self._repo.delete(dataset_id, db)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete dataset because it is referenced by other records.",
            ) from exc

        delete_dataset_files(dataset_id)
        logger.info("Dataset %s deleted", dataset_id)


def _safe_float(value: Any) -> float | None:
    try:
        return float(value) if pd.notna(value) else None
    except (TypeError, ValueError):
        return None
