"""
dashboard_repository.py — Read-only data access layer for the Dashboard.

Design principles:
  - NEVER duplicates queries already owned by other repositories.
  - Delegates count/aggregate queries to MetricsRepository, ArtifactRepository,
    DatasetRepository, and ExperimentRepository.
  - Only the activity feed and quick-stats queries are new here.

All methods are strictly read-only.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.artifact import Artifact, ArtifactType, RunResult
from app.models.dataset import Dataset
from app.models.experiment import Experiment, Run, RunStatus
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.metrics_repository import MetricsRepository
from app.repositories.pipeline_repository import PipelineRepository


class DashboardRepository:
    """Read-only repository that aggregates cross-module data for the dashboard."""

    def __init__(self) -> None:
        self._metrics_repo = MetricsRepository()
        self._artifact_repo = ArtifactRepository()
        self._dataset_repo = DatasetRepository()
        self._experiment_repo = ExperimentRepository()
        self._pipeline_repo = PipelineRepository()

    # ── Overview ──────────────────────────────────────────────────────────────

    def get_overview(self, db: Session) -> Dict[str, Any]:
        """Compose platform-wide summary by delegating to specialist repositories."""
        # Run metrics — reuse MetricsRepository (no SQL duplication)
        metrics = self._metrics_repo.get_overview(db)

        # Count datasets and experiments
        total_datasets = len(self._dataset_repo.list_all(db))
        total_experiments = self._experiment_repo.count(db)

        # Running runs — separate count
        running_runs = (
            db.query(func.count(Run.id))
            .filter(Run.status == RunStatus.running)
            .scalar()
            or 0
        )

        # Artifact stats — reuse ArtifactRepository methods
        total_artifacts = (
            db.query(func.count(Artifact.id)).scalar() or 0
        )
        models_stored = self._artifact_repo.count_by_type(
            ArtifactType.trained_model, db
        )
        storage_used_bytes = self._artifact_repo.total_size_bytes(db)

        # Average training duration — reuse pipeline overview calculation
        pipeline_overview = self._pipeline_repo.get_overview(db)

        return {
            "total_datasets": total_datasets,
            "total_experiments": total_experiments,
            "total_runs": metrics["total_runs"],
            "completed_runs": metrics["completed_runs"],
            "running_runs": running_runs,
            "failed_runs": metrics["failed_runs"],
            "total_artifacts": total_artifacts,
            "models_stored": models_stored,
            "success_rate": metrics["success_rate"],
            "average_accuracy": metrics["average_accuracy"],
            "average_f1": metrics["average_f1"],
            "average_roc_auc": metrics["average_roc_auc"],
            "average_training_duration_seconds": pipeline_overview.get(
                "average_duration_seconds"
            ),
            "storage_used_bytes": storage_used_bytes,
        }

    # ── Activity Feed ─────────────────────────────────────────────────────────

    def get_activity(self, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Construct a unified activity feed by querying each entity type for recent events.

        Events sourced:
          - Dataset uploaded (Dataset.created_at)
          - Experiment created (Experiment.created_at)
          - Run created / queued (Run.created_at)
          - Run started running (Run where status == running → created_at proxy)
          - Run completed (RunResult.completed_at or Run.updated_at where status=completed)
          - Run failed (Run.updated_at where status=failed)
          - Artifact generated (Artifact.created_at)
          - Metrics persisted (RunResult.created_at)
        """
        events: List[Dict[str, Any]] = []

        # ── Datasets ──────────────────────────────────────────────────────────
        datasets = (
            db.query(Dataset)
            .order_by(Dataset.created_at.desc())
            .limit(limit)
            .all()
        )
        for ds in datasets:
            events.append({
                "event_type": "dataset_uploaded",
                "entity_type": "dataset",
                "entity_id": ds.id,
                "entity_name": ds.name,
                "description": f"Dataset '{ds.name}' uploaded ({ds.row_count or '?'} rows)",
                "occurred_at": ds.created_at,
                "metadata": {
                    "row_count": ds.row_count,
                    "file_size_bytes": ds.file_size_bytes,
                },
            })

        # ── Experiments ───────────────────────────────────────────────────────
        experiments = (
            db.query(Experiment)
            .order_by(Experiment.created_at.desc())
            .limit(limit)
            .all()
        )
        for exp in experiments:
            events.append({
                "event_type": "experiment_created",
                "entity_type": "experiment",
                "entity_id": exp.id,
                "entity_name": exp.name,
                "description": f"Experiment '{exp.name}' created",
                "occurred_at": exp.created_at,
                "metadata": {"status": exp.status.value},
            })

        # ── Runs ──────────────────────────────────────────────────────────────
        runs = (
            db.query(Run)
            .order_by(Run.updated_at.desc())
            .limit(limit * 2)
            .all()
        )
        for run in runs:
            # Creation / queue event
            events.append({
                "event_type": "run_queued" if run.status == RunStatus.queued else "run_created",
                "entity_type": "run",
                "entity_id": run.id,
                "entity_name": f"Run #{run.run_number}",
                "description": f"Run #{run.run_number} created (status: {run.status.value})",
                "occurred_at": run.created_at,
                "metadata": {
                    "model_type": run.model_type,
                    "experiment_id": run.experiment_id,
                    "status": run.status.value,
                },
            })

            # Terminal state events use updated_at as event time
            if run.status == RunStatus.completed and run.updated_at != run.created_at:
                events.append({
                    "event_type": "run_completed",
                    "entity_type": "run",
                    "entity_id": run.id,
                    "entity_name": f"Run #{run.run_number}",
                    "description": f"Run #{run.run_number} completed successfully",
                    "occurred_at": run.updated_at,
                    "metadata": {
                        "model_type": run.model_type,
                        "experiment_id": run.experiment_id,
                    },
                })
            elif run.status == RunStatus.failed and run.updated_at != run.created_at:
                events.append({
                    "event_type": "run_failed",
                    "entity_type": "run",
                    "entity_id": run.id,
                    "entity_name": f"Run #{run.run_number}",
                    "description": f"Run #{run.run_number} failed",
                    "occurred_at": run.updated_at,
                    "metadata": {
                        "model_type": run.model_type,
                        "experiment_id": run.experiment_id,
                    },
                })

        # ── Artifacts ─────────────────────────────────────────────────────────
        artifacts = (
            db.query(Artifact)
            .order_by(Artifact.created_at.desc())
            .limit(limit)
            .all()
        )
        for art in artifacts:
            events.append({
                "event_type": "artifact_generated",
                "entity_type": "artifact",
                "entity_id": art.id,
                "entity_name": art.filename,
                "description": f"Artifact '{art.filename}' saved ({art.artifact_type.value})",
                "occurred_at": art.created_at,
                "metadata": {
                    "artifact_type": art.artifact_type.value,
                    "run_id": art.run_id,
                    "file_size_bytes": art.file_size_bytes,
                },
            })

        # ── RunResults (metrics persisted) ────────────────────────────────────
        results = (
            db.query(RunResult)
            .order_by(RunResult.created_at.desc())
            .limit(limit)
            .all()
        )
        for result in results:
            events.append({
                "event_type": "metrics_persisted",
                "entity_type": "result",
                "entity_id": result.id,
                "entity_name": f"Metrics for run {result.run_id[:8]}",
                "description": (
                    f"Metrics persisted — accuracy: {result.accuracy:.4f}"
                ),
                "occurred_at": result.created_at,
                "metadata": {
                    "accuracy": result.accuracy,
                    "f1_score": result.f1_score,
                    "run_id": result.run_id,
                },
            })

        # Sort all events newest-first and return top N
        events.sort(key=lambda e: e["occurred_at"], reverse=True)
        return events[:limit]

    # ── Recent Runs ───────────────────────────────────────────────────────────

    def get_recent_runs(self, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the N most recent runs with experiment/dataset/result context."""
        rows = self._pipeline_repo.get_runs_with_context(db, limit=limit, offset=0)
        return rows

    # ── Quick Stats ───────────────────────────────────────────────────────────

    def get_quick_stats(self, db: Session) -> Dict[str, Any]:
        """
        Return highlight cards:
          - Best model (highest average accuracy across completed runs)
          - Best experiment (highest best_accuracy)
          - Most used dataset (most experiments associated)
          - Most recent artifact
        """
        result: Dict[str, Any] = {
            "best_model_type": None,
            "best_model_accuracy": None,
            "best_model_run_count": None,
            "best_experiment_id": None,
            "best_experiment_name": None,
            "best_experiment_accuracy": None,
            "best_experiment_run_count": None,
            "most_used_dataset_id": None,
            "most_used_dataset_name": None,
            "most_used_dataset_experiment_count": None,
            "latest_artifact_id": None,
            "latest_artifact_filename": None,
            "latest_artifact_type": None,
            "latest_artifact_run_id": None,
            "latest_artifact_created_at": None,
        }

        # Best model — by average accuracy from RunResult
        effective_model = func.coalesce(
            RunResult.model_type, Run.model_type, "random_forest"
        ).label("model_type")

        best_model_row = (
            db.query(
                effective_model,
                func.avg(RunResult.accuracy).label("avg_acc"),
                func.count(RunResult.id).label("run_count"),
            )
            .join(Run, RunResult.run_id == Run.id)
            .filter(Run.status == RunStatus.completed)
            .group_by(effective_model)
            .order_by(desc("avg_acc"))
            .first()
        )
        if best_model_row and best_model_row.avg_acc is not None:
            result["best_model_type"] = best_model_row.model_type
            result["best_model_accuracy"] = round(float(best_model_row.avg_acc), 4)
            result["best_model_run_count"] = best_model_row.run_count

        # Best experiment — by best_accuracy from RunResult
        best_exp_row = (
            db.query(
                Experiment.id,
                Experiment.name,
                func.max(RunResult.accuracy).label("best_acc"),
                func.count(Run.id).label("run_count"),
            )
            .join(Run, Run.experiment_id == Experiment.id)
            .join(RunResult, RunResult.run_id == Run.id)
            .filter(Run.status == RunStatus.completed)
            .group_by(Experiment.id, Experiment.name)
            .order_by(desc("best_acc"))
            .first()
        )
        if best_exp_row and best_exp_row.best_acc is not None:
            result["best_experiment_id"] = best_exp_row.id
            result["best_experiment_name"] = best_exp_row.name
            result["best_experiment_accuracy"] = round(float(best_exp_row.best_acc), 4)
            result["best_experiment_run_count"] = best_exp_row.run_count

        # Most used dataset — by number of experiments
        most_used_row = (
            db.query(
                Dataset.id,
                Dataset.name,
                func.count(Experiment.id).label("exp_count"),
            )
            .join(Experiment, Experiment.dataset_id == Dataset.id)
            .group_by(Dataset.id, Dataset.name)
            .order_by(desc("exp_count"))
            .first()
        )
        if most_used_row:
            result["most_used_dataset_id"] = most_used_row.id
            result["most_used_dataset_name"] = most_used_row.name
            result["most_used_dataset_experiment_count"] = most_used_row.exp_count

        # Most recent artifact
        latest_artifact: Optional[Artifact] = (
            db.query(Artifact)
            .order_by(Artifact.created_at.desc())
            .first()
        )
        if latest_artifact:
            result["latest_artifact_id"] = latest_artifact.id
            result["latest_artifact_filename"] = latest_artifact.filename
            result["latest_artifact_type"] = latest_artifact.artifact_type.value
            result["latest_artifact_run_id"] = latest_artifact.run_id
            result["latest_artifact_created_at"] = latest_artifact.created_at

        return result
