"""
pipeline_service.py — Business logic for the Pipeline Visualization module.

Transforms raw DB data from PipelineRepository into structured graph,
timeline, and lineage response objects.

All operations are read-only. No data is created or modified.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.repositories.pipeline_repository import PipelineRepository
from app.models.experiment import RunStatus


class PipelineService:
    """Encapsulates pipeline visualization business logic."""

    # Status → display properties
    STATUS_COLOR: Dict[str, str] = {
        "completed": "completed",
        "running": "running",
        "failed": "failed",
        "queued": "queued",
        "draft": "draft",
        "pending": "pending",
        "skipped": "skipped",
        "cancelled": "cancelled",
    }

    # Stage node definitions (order matters)
    STAGES = [
        {"id": "dataset",    "label": "Dataset",    "icon": "Database",    "stage_type": "dataset"},
        {"id": "experiment", "label": "Experiment", "icon": "FlaskConical","stage_type": "experiment"},
        {"id": "run",        "label": "Run",        "icon": "Play",        "stage_type": "run"},
        {"id": "training",   "label": "Training",   "icon": "BrainCircuit","stage_type": "training"},
        {"id": "evaluation", "label": "Evaluation", "icon": "BarChart2",   "stage_type": "evaluation"},
        {"id": "artifacts",  "label": "Artifacts",  "icon": "Package",     "stage_type": "artifacts"},
        {"id": "metrics",    "label": "Metrics",    "icon": "TrendingUp",  "stage_type": "metrics"},
        {"id": "completed",  "label": "Completed",  "icon": "CheckCircle2","stage_type": "completed"},
    ]

    def __init__(self) -> None:
        self._repo = PipelineRepository()

    # ── Overview ─────────────────────────────────────────────────────────────

    def get_overview(self, db: Session) -> Dict[str, Any]:
        return self._repo.get_overview(db)

    # ── Runs List ─────────────────────────────────────────────────────────────

    def get_runs(
        self,
        db: Session,
        dataset_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
        status: Optional[str] = None,
        model_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self._repo.get_runs_with_context(
            db,
            dataset_id=dataset_id,
            experiment_id=experiment_id,
            status=status,
            model_type=model_type,
        )

    # ── Execution Graph ───────────────────────────────────────────────────────

    def get_pipeline_graph(self, run_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Build the execution graph and timeline for a single run.
        Returns None if the run does not exist.
        """
        raw = self._repo.get_run_graph_data(run_id, db)
        if raw is None:
            return None

        run = raw["run"]
        experiment = raw["experiment"]
        dataset = raw["dataset"]
        result = raw["result"]
        artifacts = raw["artifacts"]

        run_status = run.status.value if run.status else "draft"
        has_result = result is not None
        has_artifacts = len(artifacts) > 0

        def _node_status(stage: str) -> str:
            """Determine the status of each stage node based on run progress."""
            if run_status == "draft":
                if stage in ("dataset", "experiment"):
                    return "completed"
                return "pending"

            if run_status == "queued":
                if stage in ("dataset", "experiment", "run"):
                    return "completed"
                return "pending"

            if run_status == "running":
                if stage in ("dataset", "experiment", "run"):
                    return "completed"
                if stage == "training":
                    return "running"
                return "pending"

            if run_status == "completed":
                if stage == "metrics" or stage == "completed":
                    return "completed" if has_result else "skipped"
                if stage == "artifacts":
                    return "completed" if has_artifacts else "skipped"
                return "completed"

            if run_status == "failed":
                if stage in ("dataset", "experiment", "run"):
                    return "completed"
                if stage == "training":
                    return "failed"
                return "skipped"

            if run_status == "cancelled":
                if stage in ("dataset", "experiment", "run"):
                    return "completed"
                return "skipped"

            return "pending"

        nodes = []
        for i, stage in enumerate(self.STAGES):
            stage_id = stage["id"]
            st = _node_status(stage_id)

            # Build detail dict for each node
            detail: Dict[str, Any] = {}
            link: Optional[str] = None

            if stage_id == "dataset" and dataset:
                detail = {
                    "name": dataset.name,
                    "rows": dataset.row_count,
                    "columns": dataset.column_count,
                }
                link = f"/datasets/{dataset.id}"

            elif stage_id == "experiment":
                detail = {
                    "name": experiment.name,
                    "status": experiment.status.value,
                    "objective": experiment.objective or "",
                }
                link = f"/experiments/{experiment.id}"

            elif stage_id == "run":
                detail = {
                    "run_number": run.run_number,
                    "model": run.model_type or "default",
                    "status": run.status.value,
                }
                link = f"/runs/{run.id}"

            elif stage_id == "training":
                detail = {
                    "model": (result.model_type or run.model_type or "default") if result else run.model_type or "default",
                    "config": run.training_configuration or {},
                }
                if result and result.execution_time_seconds:
                    detail["duration_seconds"] = round(result.execution_time_seconds, 2)

            elif stage_id == "evaluation" and result:
                detail = {
                    "accuracy": round(result.accuracy, 4) if result.accuracy else None,
                    "f1_score": round(result.f1_score, 4) if result.f1_score else None,
                    "roc_auc": round(result.roc_auc, 4) if result.roc_auc else None,
                    "precision": round(result.precision, 4) if result.precision else None,
                    "recall": round(result.recall, 4) if result.recall else None,
                }

            elif stage_id == "artifacts":
                detail = {
                    "count": len(artifacts),
                    "types": [a.artifact_type.value for a in artifacts],
                }
                if artifacts:
                    link = "/artifacts"

            elif stage_id == "metrics" and result:
                detail = {
                    "accuracy": round(result.accuracy, 4) if result.accuracy else None,
                    "f1_score": round(result.f1_score, 4) if result.f1_score else None,
                }
                link = "/metrics"

            # Timestamps
            started_at = None
            completed_at = None
            duration_seconds = None

            if stage_id in ("training", "evaluation") and result:
                started_at = result.started_at
                completed_at = result.completed_at
                if result.execution_time_seconds:
                    duration_seconds = round(result.execution_time_seconds, 2)

            elif stage_id == "run":
                started_at = run.created_at

            elif stage_id == "dataset" and dataset:
                completed_at = dataset.created_at

            elif stage_id == "experiment":
                completed_at = experiment.created_at

            nodes.append({
                "id": stage_id,
                "label": stage["label"],
                "stage_type": stage["stage_type"],
                "status": st,
                "icon": stage["icon"],
                "color": st,
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_seconds": duration_seconds,
                "detail": detail,
                "link": link,
            })

        # Build edges
        edges = []
        for i in range(len(self.STAGES) - 1):
            src = self.STAGES[i]["id"]
            tgt = self.STAGES[i + 1]["id"]
            src_status = nodes[i]["status"]
            tgt_status = nodes[i + 1]["status"]
            active = src_status == "completed"
            edges.append({
                "source": src,
                "target": tgt,
                "active": active,
            })

        graph = {
            "run_id": run.id,
            "run_number": run.run_number,
            "experiment_id": experiment.id,
            "experiment_name": experiment.name,
            "dataset_id": dataset.id if dataset else None,
            "dataset_name": dataset.name if dataset else None,
            "status": run_status,
            "nodes": nodes,
            "edges": edges,
        }

        timeline = self._build_timeline(run, experiment, result, artifacts)

        return {"graph": graph, "timeline": timeline}

    def _build_timeline(self, run: Any, experiment: Any, result: Any, artifacts: List[Any]) -> Dict[str, Any]:
        """Build the ordered chronological event timeline for a run."""
        events = []
        run_status = run.status.value

        # Always include: Dataset Loaded
        events.append({
            "order": 1,
            "event": "Dataset Loaded",
            "stage_type": "dataset",
            "status": "completed",
            "timestamp": experiment.created_at,
            "duration_seconds": None,
            "detail": "CSV validated and metadata stored",
        })

        # Experiment Defined
        events.append({
            "order": 2,
            "event": "Experiment Defined",
            "stage_type": "experiment",
            "status": "completed",
            "timestamp": experiment.created_at,
            "duration_seconds": None,
            "detail": f"Experiment '{experiment.name}' configured",
        })

        # Run Created
        events.append({
            "order": 3,
            "event": "Run Created",
            "stage_type": "run",
            "status": "completed",
            "timestamp": run.created_at,
            "duration_seconds": None,
            "detail": f"Run #{run.run_number} initialized",
        })

        # Training events depend on status
        if run_status in ("running", "completed", "failed"):
            started_at = result.started_at if result and result.started_at else run.updated_at
            events.append({
                "order": 4,
                "event": "Training Started",
                "stage_type": "training",
                "status": "running" if run_status == "running" else "completed",
                "timestamp": started_at,
                "duration_seconds": None,
                "detail": f"Model: {run.model_type or 'default'}",
            })

        if run_status == "failed":
            events.append({
                "order": 5,
                "event": "Training Failed",
                "stage_type": "training",
                "status": "failed",
                "timestamp": run.updated_at,
                "duration_seconds": None,
                "detail": "Run marked as failed",
            })

        if run_status == "completed" and result:
            completed_at = result.completed_at or run.updated_at
            duration = result.execution_time_seconds
            events.append({
                "order": 5,
                "event": "Training Completed",
                "stage_type": "training",
                "status": "completed",
                "timestamp": completed_at,
                "duration_seconds": round(duration, 2) if duration else None,
                "detail": f"Duration: {round(duration, 2)}s" if duration else "Training finished",
            })

            events.append({
                "order": 6,
                "event": "Evaluation Completed",
                "stage_type": "evaluation",
                "status": "completed",
                "timestamp": completed_at,
                "duration_seconds": None,
                "detail": (
                    f"Accuracy: {round(result.accuracy * 100, 2)}%, "
                    f"F1: {round(result.f1_score * 100, 2)}%"
                    if result.accuracy and result.f1_score else "Metrics computed"
                ),
            })

            if artifacts:
                events.append({
                    "order": 7,
                    "event": "Artifacts Saved",
                    "stage_type": "artifacts",
                    "status": "completed",
                    "timestamp": artifacts[-1].created_at,
                    "duration_seconds": None,
                    "detail": f"{len(artifacts)} artifact(s) registered",
                })

            events.append({
                "order": 8,
                "event": "Metrics Stored",
                "stage_type": "metrics",
                "status": "completed",
                "timestamp": result.created_at,
                "duration_seconds": None,
                "detail": "RunResult persisted to database",
            })

            events.append({
                "order": 9,
                "event": "Pipeline Finished",
                "stage_type": "completed",
                "status": "completed",
                "timestamp": completed_at,
                "duration_seconds": None,
                "detail": "Run successfully completed",
            })

        return {
            "run_id": run.id,
            "run_number": run.run_number,
            "experiment_name": experiment.name,
            "total_duration_seconds": (
                round(result.execution_time_seconds, 2)
                if result and result.execution_time_seconds
                else None
            ),
            "events": events,
        }

    # ── Lineage ───────────────────────────────────────────────────────────────

    def get_lineage(self, db: Session) -> List[Dict[str, Any]]:
        """Return full hierarchical lineage: Dataset → Experiments → Runs → Artifacts."""
        raw = self._repo.get_lineage_data(db)

        results = []
        for ds_data in raw:
            dataset = ds_data["dataset"]

            exp_list = []
            for exp_data in ds_data["experiments"]:
                exp = exp_data["experiment"]

                run_list = []
                for run_data in exp_data["runs"]:
                    run = run_data["run"]
                    artifact_list = [
                        {
                            "artifact_id": a.id,
                            "artifact_type": a.artifact_type.value,
                            "filename": a.filename,
                            "created_at": a.created_at,
                        }
                        for a in run_data["artifacts"]
                    ]
                    run_list.append({
                        "run_id": run.id,
                        "run_number": run.run_number,
                        "model": run.model_type,
                        "status": run.status.value,
                        "created_at": run.created_at,
                        "artifacts": artifact_list,
                    })

                exp_list.append({
                    "experiment_id": exp.id,
                    "experiment_name": exp.name,
                    "status": exp.status.value,
                    "created_at": exp.created_at,
                    "total_runs": exp_data["total_runs"],
                    "completed_runs": exp_data["completed_runs"],
                    "runs": run_list,
                })

            results.append({
                "dataset_id": dataset.id,
                "dataset_name": dataset.name,
                "row_count": dataset.row_count,
                "column_count": dataset.column_count,
                "created_at": dataset.created_at,
                "total_experiments": ds_data["total_experiments"],
                "total_runs": ds_data["total_runs"],
                "experiments": exp_list,
            })

        return results
