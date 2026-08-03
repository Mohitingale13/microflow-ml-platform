"""
training_service.py — TrainingService: Orchestrates the ML pipeline for a Run.

Responsibilities:
  - Validate Run exists and is in the Queued state.
  - Load the associated dataset from storage.
  - Preprocess the data.
  - Build the estimator via the model factory.
  - Train the model.
  - Evaluate the model.
  - Persist RunResult and Artifacts via dedicated services.
  - Update Run status (Queued → Running → Completed | Failed).
  - Return evaluation metrics.

This service coordinates independent training modules; it contains no ML logic
of its own.  It also contains no HTTP dependencies — that belongs in the router.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.artifact import ArtifactType
from app.models.experiment import Run, RunStatus
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.run_repository import RunRepository
from app.repositories.run_result_repository import RunResultRepository
from app.services.artifact_storage_service import ArtifactStorageService, ArtifactStorageError
from app.training.evaluation import evaluate_model, EvaluationError
from app.training.loader import load_dataset, DatasetLoaderError
from app.training.model_factory import build_estimator, ModelFactoryError
from app.training.preprocessing import preprocess_dataframe, PreprocessingError, PreprocessedData
from app.training.trainer import train_model, TrainerError

logger = logging.getLogger(__name__)


class TrainingService:
    def __init__(
        self,
        run_repo: RunRepository,
        experiment_repo: ExperimentRepository,
        dataset_repo: DatasetRepository,
        run_result_repo: RunResultRepository | None = None,
        artifact_repo: ArtifactRepository | None = None,
        artifact_storage: ArtifactStorageService | None = None,
    ) -> None:
        self._run_repo = run_repo
        self._experiment_repo = experiment_repo
        self._dataset_repo = dataset_repo
        self._run_result_repo = run_result_repo or RunResultRepository()
        self._artifact_repo = artifact_repo or ArtifactRepository()
        self._artifact_storage = artifact_storage or ArtifactStorageService()

    # ── Public command ─────────────────────────────────────────────────────────

    def execute(
        self,
        run_id: str,
        *,
        target_column: str,
        test_split: float | None,
        db: Session,
    ) -> dict[str, Any]:
        """
        Execute the full training pipeline for *run_id*.

        State transitions
        -----------------
        queued → running → completed  (success)
        queued → running → failed     (any exception)

        Returns
        -------
        dict[str, Any]
            Evaluation metrics dict (JSON-serialisable).
        """
        # ── Validate run ───────────────────────────────────────────────────────
        run = self._get_run_or_404(run_id, db)
        self._assert_run_is_queued(run)

        # ── Transition: queued → running ───────────────────────────────────────
        started_at = datetime.now(timezone.utc)
        run = self._run_repo.update(db, run, status=RunStatus.running)
        logger.info("Run %s: queued → running", run_id)

        try:
            metrics, estimator, preprocessed, experiment, dataset = self._run_pipeline(
                run, target_column=target_column, test_split=test_split, db=db
            )
        except HTTPException:
            self._run_repo.update(db, run, status=RunStatus.failed)
            logger.error("Run %s: running → failed (HTTP error)", run_id)
            raise
        except (
            DatasetLoaderError,
            PreprocessingError,
            ModelFactoryError,
            TrainerError,
            EvaluationError,
        ) as exc:
            self._run_repo.update(db, run, status=RunStatus.failed)
            logger.error("Run %s: running → failed — %s", run_id, exc)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            self._run_repo.update(db, run, status=RunStatus.failed)
            logger.exception("Run %s: running → failed (unexpected error)", run_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Training failed with an unexpected error: {exc}",
            ) from exc

        # ── Persist artifacts (best-effort — do not fail the run on storage errors) ──
        completed_at = datetime.now(timezone.utc)
        try:
            self._persist_results(
                run=run,
                metrics=metrics,
                estimator=estimator,
                preprocessed=preprocessed,
                experiment=experiment,
                dataset=dataset,
                started_at=started_at,
                completed_at=completed_at,
                db=db,
            )
        except Exception as exc:
            logger.error(
                "Run %s: artifact persistence failed (run still marked completed) — %s",
                run_id,
                exc,
            )

        # ── Transition: running → completed ────────────────────────────────────
        self._run_repo.update(db, run, status=RunStatus.completed)
        logger.info("Run %s: running → completed  accuracy=%.4f", run_id, metrics["accuracy"])
        return metrics

    # ── Private helpers ────────────────────────────────────────────────────────

    def _run_pipeline(
        self,
        run: Run,
        *,
        target_column: str,
        test_split: float | None,
        db: Session,
    ) -> tuple[dict[str, Any], Any, PreprocessedData, Any, Any]:
        """Execute loader → preprocess → factory → train → evaluate.
        
        Returns (metrics, estimator, preprocessed, experiment, dataset)
        """
        config: dict[str, Any] = run.training_configuration or {}
        effective_test_split = float(
            test_split
            if test_split is not None
            else config.get("test_split", 0.2)
        )
        random_state = int(config.get("random_state", config.get("seed", 42)))

        # ── Load dataset ───────────────────────────────────────────────────────
        experiment = self._experiment_repo.get_by_id(run.experiment_id, db)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment '{run.experiment_id}' not found",
            )

        dataset = self._dataset_repo.get_by_id(experiment.dataset_id, db)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset '{experiment.dataset_id}' not found",
            )

        logger.info("Run %s: loading dataset from %r", run.id, dataset.storage_path)
        df = load_dataset(dataset.storage_path)

        # ── Preprocess ─────────────────────────────────────────────────────────
        logger.info(
            "Run %s: preprocessing (target=%r, test_split=%.2f)",
            run.id, target_column, effective_test_split,
        )
        preprocessed = preprocess_dataframe(
            df,
            target_column=target_column,
            test_size=effective_test_split,
            random_state=random_state,
        )

        # ── Build estimator ────────────────────────────────────────────────────
        logger.info("Run %s: building estimator (model_type=%r)", run.id, run.model_type)
        estimator = build_estimator(
            model_type=run.model_type,
            training_configuration=config,
        )

        # ── Train ──────────────────────────────────────────────────────────────
        logger.info("Run %s: training", run.id)
        trained_estimator = train_model(
            estimator,
            preprocessed.X_train,
            preprocessed.y_train,
        )

        # ── Evaluate ───────────────────────────────────────────────────────────
        logger.info("Run %s: evaluating", run.id)
        metrics = evaluate_model(
            trained_estimator,
            preprocessed.X_test,
            preprocessed.y_test,
        )

        return metrics, trained_estimator, preprocessed, experiment, dataset

    def _persist_results(
        self,
        *,
        run: Run,
        metrics: dict[str, Any],
        estimator: Any,
        preprocessed: PreprocessedData,
        experiment: Any,
        dataset: Any,
        started_at: datetime,
        completed_at: datetime,
        db: Session,
    ) -> None:
        """
        Persist RunResult and all Artifacts.  Cleans up on failure.
        """
        run_id = run.id
        experiment_id = run.experiment_id
        dataset_id = dataset.id

        # Track created artifacts for rollback
        artifact_ids: list[str] = []

        try:
            # ── Save model ────────────────────────────────────────────────────
            model_filename, model_path, model_size, model_checksum = (
                self._artifact_storage.save_model(run_id, estimator)
            )
            art = self._artifact_repo.create(
                db,
                run_id=run_id,
                experiment_id=experiment_id,
                dataset_id=dataset_id,
                artifact_type=ArtifactType.trained_model,
                filename=model_filename,
                mime_type="application/octet-stream",
                storage_path=model_path,
                file_size_bytes=model_size,
                sha256_checksum=model_checksum,
            )
            artifact_ids.append(art.id)

            # ── Save metrics.json ─────────────────────────────────────────────
            metrics_data = {
                "accuracy": metrics["accuracy"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1_score": metrics["f1_score"],
                "roc_auc": metrics.get("roc_auc"),
            }
            fn, path, size, checksum = self._artifact_storage.save_json(
                run_id, "metrics.json", metrics_data
            )
            art = self._artifact_repo.create(
                db,
                run_id=run_id,
                experiment_id=experiment_id,
                dataset_id=dataset_id,
                artifact_type=ArtifactType.metrics_json,
                filename=fn,
                mime_type="application/json",
                storage_path=path,
                file_size_bytes=size,
                sha256_checksum=checksum,
            )
            artifact_ids.append(art.id)

            # ── Save evaluation.json ──────────────────────────────────────────
            evaluation_data = {**metrics_data, "confusion_matrix": metrics["confusion_matrix"]}
            fn, path, size, checksum = self._artifact_storage.save_json(
                run_id, "evaluation.json", evaluation_data
            )
            art = self._artifact_repo.create(
                db,
                run_id=run_id,
                experiment_id=experiment_id,
                dataset_id=dataset_id,
                artifact_type=ArtifactType.evaluation_json,
                filename=fn,
                mime_type="application/json",
                storage_path=path,
                file_size_bytes=size,
                sha256_checksum=checksum,
            )
            artifact_ids.append(art.id)

            # ── Save confusion_matrix.json ────────────────────────────────────
            cm_data = {"confusion_matrix": metrics["confusion_matrix"]}
            fn, path, size, checksum = self._artifact_storage.save_json(
                run_id, "confusion_matrix.json", cm_data
            )
            art = self._artifact_repo.create(
                db,
                run_id=run_id,
                experiment_id=experiment_id,
                dataset_id=dataset_id,
                artifact_type=ArtifactType.confusion_matrix_json,
                filename=fn,
                mime_type="application/json",
                storage_path=path,
                file_size_bytes=size,
                sha256_checksum=checksum,
            )
            artifact_ids.append(art.id)

            # ── Save configuration.json ───────────────────────────────────────
            config_data = {
                "run_id": run_id,
                "model_type": run.model_type,
                "training_configuration": run.training_configuration,
                "experiment_id": experiment_id,
                "dataset_id": dataset_id,
            }
            fn, path, size, checksum = self._artifact_storage.save_json(
                run_id, "configuration.json", config_data
            )
            art = self._artifact_repo.create(
                db,
                run_id=run_id,
                experiment_id=experiment_id,
                dataset_id=dataset_id,
                artifact_type=ArtifactType.configuration_json,
                filename=fn,
                mime_type="application/json",
                storage_path=path,
                file_size_bytes=size,
                sha256_checksum=checksum,
            )
            artifact_ids.append(art.id)

            # ── Save preprocessing.json ───────────────────────────────────────
            preprocessing_data = {
                "feature_names": preprocessed.feature_names,
                "train_samples": len(preprocessed.X_train),
                "test_samples": len(preprocessed.X_test),
                "target_encoder_classes": (
                    preprocessed.target_encoder.classes_.tolist()
                    if preprocessed.target_encoder is not None
                    else None
                ),
            }
            fn, path, size, checksum = self._artifact_storage.save_json(
                run_id, "preprocessing.json", preprocessing_data
            )
            art = self._artifact_repo.create(
                db,
                run_id=run_id,
                experiment_id=experiment_id,
                dataset_id=dataset_id,
                artifact_type=ArtifactType.preprocessing_json,
                filename=fn,
                mime_type="application/json",
                storage_path=path,
                file_size_bytes=size,
                sha256_checksum=checksum,
            )
            artifact_ids.append(art.id)

            exec_time = float((completed_at - started_at).total_seconds())
            if exec_time < 0:
                exec_time = 0.0

            # ── Persist RunResult ─────────────────────────────────────────────
            self._run_result_repo.create(
                db,
                run_id=run_id,
                accuracy=metrics["accuracy"],
                precision=metrics["precision"],
                recall=metrics["recall"],
                f1_score=metrics["f1_score"],
                roc_auc=metrics.get("roc_auc"),
                confusion_matrix=metrics["confusion_matrix"],
                started_at=started_at,
                completed_at=completed_at,
                execution_time_seconds=round(exec_time, 4),
                model_type=run.model_type or "random_forest",
                dataset_id=dataset_id,
                training_config_snapshot=run.training_configuration,
                preprocessing_summary=preprocessing_data,
            )

            logger.info(
                "Run %s: persisted %d artifacts and RunResult", run_id, len(artifact_ids)
            )

        except ArtifactStorageError as exc:
            # Clean up files and DB records
            logger.error("Run %s: storage error during persistence — %s", run_id, exc)
            self._artifact_repo.delete_by_run(run_id, db)
            self._run_result_repo.delete_by_run_id(run_id, db)
            self._artifact_storage.cleanup_run_directory(run_id)
            raise

        except Exception as exc:
            logger.error("Run %s: unexpected error during persistence — %s", run_id, exc)
            self._artifact_repo.delete_by_run(run_id, db)
            self._run_result_repo.delete_by_run_id(run_id, db)
            self._artifact_storage.cleanup_run_directory(run_id)
            raise

    def _get_run_or_404(self, run_id: str, db: Session) -> Run:
        run = self._run_repo.get_by_id(run_id, db)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run '{run_id}' not found",
            )
        return run

    def _assert_run_is_queued(self, run: Run) -> None:
        if run.status != RunStatus.queued:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Run can only be executed from the 'queued' state. "
                    f"Current status: '{run.status.value}'"
                ),
            )
