"""
pipeline_repository.py — Read-only data access layer for Pipeline Visualization.

Composes across existing Run, Experiment, Dataset, Artifact, and RunResult tables.
Does NOT duplicate existing repository logic — uses JOINs to aggregate lineage.

All methods are strictly read-only. Nothing is written or modified.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.artifact import Artifact, RunResult
from app.models.dataset import Dataset
from app.models.experiment import Experiment, Run, RunStatus


class PipelineRepository:
    """Read-only repository for pipeline visualization data."""

    # ── Overview ─────────────────────────────────────────────────────────────

    def get_overview(self, db: Session) -> Dict[str, Any]:
        """Return global pipeline execution statistics."""
        # Status counts — include all runs that have been submitted (non-draft)
        status_counts = (
            db.query(Run.status, func.count(Run.id).label("cnt"))
            .group_by(Run.status)
            .all()
        )
        counts: Dict[str, int] = {row.status.value: row.cnt for row in status_counts}

        total_non_draft = (
            counts.get("queued", 0)
            + counts.get("running", 0)
            + counts.get("completed", 0)
            + counts.get("failed", 0)
            + counts.get("cancelled", 0)
        )
        completed = counts.get("completed", 0)
        total_runs = sum(counts.values())

        completed_rows = (
            db.query(Run, RunResult)
            .outerjoin(RunResult, Run.id == RunResult.run_id)
            .filter(Run.status == RunStatus.completed)
            .all()
        )
        durations: list[float] = []
        for run, res in completed_rows:
            if res and res.execution_time_seconds is not None:
                durations.append(float(res.execution_time_seconds))
            elif run.updated_at and run.created_at and run.updated_at >= run.created_at:
                durations.append(float((run.updated_at - run.created_at).total_seconds()))
        avg_duration = (sum(durations) / len(durations)) if durations else None

        total_artifacts = db.query(func.count(Artifact.id)).scalar() or 0
        success_rate = (completed / total_non_draft) if total_non_draft > 0 else 0.0

        return {
            "total_pipelines": total_non_draft,
            "running": counts.get("running", 0),
            "completed": completed,
            "failed": counts.get("failed", 0),
            "queued": counts.get("queued", 0),
            "draft": counts.get("draft", 0),
            "average_duration_seconds": (
                round(float(avg_duration), 2) if avg_duration is not None else None
            ),
            "total_artifacts_produced": total_artifacts,
            "success_rate": round(success_rate, 4),
        }

    # ── Runs List ─────────────────────────────────────────────────────────────

    def get_runs_with_context(
        self,
        db: Session,
        dataset_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
        status: Optional[str] = None,
        model_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Return all runs enriched with experiment, dataset, result, and artifact counts."""
        query = (
            db.query(
                Run,
                Experiment.name.label("experiment_name"),
                Experiment.dataset_id.label("dataset_id"),
                Dataset.name.label("dataset_name"),
                RunResult,
                func.count(Artifact.id).label("artifact_count"),
            )
            .join(Experiment, Run.experiment_id == Experiment.id)
            .outerjoin(Dataset, Experiment.dataset_id == Dataset.id)
            .outerjoin(RunResult, Run.id == RunResult.run_id)
            .outerjoin(Artifact, Run.id == Artifact.run_id)
        )

        if dataset_id:
            query = query.filter(Experiment.dataset_id == dataset_id)
        if experiment_id:
            query = query.filter(Run.experiment_id == experiment_id)
        if status:
            try:
                query = query.filter(Run.status == RunStatus(status))
            except ValueError:
                pass
        if model_type:
            query = query.filter(
                (Run.model_type == model_type)
                | (RunResult.model_type == model_type)
            )

        rows = (
            query.group_by(Run.id, Experiment.name, Experiment.dataset_id, Dataset.name, RunResult.id)
            .order_by(Run.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        results = []
        for run, exp_name, ds_id, ds_name, result, artifact_count in rows:
            model = (
                result.model_type
                if result and result.model_type
                else run.model_type
            )
            if not model and run.status == RunStatus.completed:
                model = "random_forest"

            started_at = result.started_at if (result and result.started_at) else None
            if not started_at and run.status in (RunStatus.running, RunStatus.completed, RunStatus.failed):
                started_at = run.created_at

            completed_at = result.completed_at if (result and result.completed_at) else None
            if not completed_at and run.status in (RunStatus.completed, RunStatus.failed):
                completed_at = run.updated_at

            dur = (
                float(result.execution_time_seconds)
                if result and result.execution_time_seconds is not None
                else None
            )
            if dur is None and run.status == RunStatus.completed and completed_at and started_at and completed_at >= started_at:
                dur = float((completed_at - started_at).total_seconds())

            results.append({
                "run_id": run.id,
                "run_number": run.run_number,
                "experiment_id": run.experiment_id,
                "experiment_name": exp_name,
                "dataset_id": ds_id,
                "dataset_name": ds_name,
                "model": model,
                "status": run.status.value,
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_seconds": (
                    round(dur, 2) if dur is not None else None
                ),
                "artifact_count": artifact_count or 0,
                "accuracy": (
                    round(float(result.accuracy), 4)
                    if result and result.accuracy is not None
                    else None
                ),
            })

        return results

    # ── Single Run Graph ──────────────────────────────────────────────────────

    def get_run_graph_data(self, run_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """Fetch all data required to build the execution graph for one run."""
        row = (
            db.query(
                Run,
                Experiment,
                Dataset,
                RunResult,
            )
            .join(Experiment, Run.experiment_id == Experiment.id)
            .outerjoin(Dataset, Experiment.dataset_id == Dataset.id)
            .outerjoin(RunResult, Run.id == RunResult.run_id)
            .filter(Run.id == run_id)
            .first()
        )

        if not row:
            return None

        run, experiment, dataset, result = row

        artifacts = (
            db.query(Artifact)
            .filter(Artifact.run_id == run_id)
            .order_by(Artifact.artifact_type)
            .all()
        )

        return {
            "run": run,
            "experiment": experiment,
            "dataset": dataset,
            "result": result,
            "artifacts": artifacts,
        }

    # ── Lineage ───────────────────────────────────────────────────────────────

    def get_lineage_data(self, db: Session) -> List[Dict[str, Any]]:
        """
        Fetch hierarchical lineage: Dataset → Experiments → Runs → Artifacts.

        Returns a list of dataset dicts each containing nested experiments
        which contain nested runs which contain nested artifacts.
        """
        datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()

        results = []
        for dataset in datasets:
            experiments = (
                db.query(Experiment)
                .filter(Experiment.dataset_id == dataset.id)
                .order_by(Experiment.created_at.desc())
                .all()
            )

            exp_data = []
            ds_total_runs = 0

            for exp in experiments:
                runs = (
                    db.query(Run)
                    .filter(Run.experiment_id == exp.id)
                    .order_by(Run.run_number.asc())
                    .all()
                )
                ds_total_runs += len(runs)
                completed_runs = sum(1 for r in runs if r.status == RunStatus.completed)

                run_data = []
                for run in runs:
                    artifacts = (
                        db.query(Artifact)
                        .filter(Artifact.run_id == run.id)
                        .order_by(Artifact.artifact_type)
                        .all()
                    )
                    run_data.append({
                        "run": run,
                        "artifacts": artifacts,
                    })

                exp_data.append({
                    "experiment": exp,
                    "total_runs": len(runs),
                    "completed_runs": completed_runs,
                    "runs": run_data,
                })

            results.append({
                "dataset": dataset,
                "total_experiments": len(experiments),
                "total_runs": ds_total_runs,
                "experiments": exp_data,
            })

        return results
