"""
metrics_repository.py — Data access layer for analytics and historical performance metrics.

Performs SQL aggregations directly on persisted RunResult, Run, Experiment, and Dataset records.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.artifact import RunResult
from app.models.dataset import Dataset
from app.models.experiment import Experiment, Run, RunStatus


class MetricsRepository:
    """Repository executing aggregate analytics queries on persisted experiment data."""

    def get_overview(self, db: Session) -> Dict[str, Any]:
        """Compute system-wide overview statistics across all runs and results."""
        total_runs = db.query(func.count(Run.id)).scalar() or 0
        completed_runs = (
            db.query(func.count(Run.id))
            .filter(Run.status == RunStatus.completed)
            .scalar()
            or 0
        )
        failed_runs = (
            db.query(func.count(Run.id))
            .filter(Run.status == RunStatus.failed)
            .scalar()
            or 0
        )

        success_rate = (completed_runs / total_runs) if total_runs > 0 else 0.0

        # Aggregate metrics from RunResult (completed runs)
        avg_row = (
            db.query(
                func.avg(RunResult.accuracy).label("avg_acc"),
                func.avg(RunResult.precision).label("avg_prec"),
                func.avg(RunResult.recall).label("avg_rec"),
                func.avg(RunResult.f1_score).label("avg_f1"),
                func.avg(RunResult.roc_auc).label("avg_roc"),
                func.avg(RunResult.execution_time_seconds).label("avg_duration"),
            )
            .first()
        )

        return {
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "success_rate": round(success_rate, 4),
            "average_accuracy": (
                round(float(avg_row.avg_acc), 4)
                if avg_row and avg_row.avg_acc is not None
                else None
            ),
            "average_precision": (
                round(float(avg_row.avg_prec), 4)
                if avg_row and avg_row.avg_prec is not None
                else None
            ),
            "average_recall": (
                round(float(avg_row.avg_rec), 4)
                if avg_row and avg_row.avg_rec is not None
                else None
            ),
            "average_f1": (
                round(float(avg_row.avg_f1), 4)
                if avg_row and avg_row.avg_f1 is not None
                else None
            ),
            "average_roc_auc": (
                round(float(avg_row.avg_roc), 4)
                if avg_row and avg_row.avg_roc is not None
                else None
            ),
            "average_training_duration": (
                round(float(avg_row.avg_duration), 2)
                if avg_row and avg_row.avg_duration is not None
                else None
            ),
        }

    def get_model_metrics(
        self,
        db: Session,
        dataset_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get aggregated metrics grouped by model family."""
        effective_model = func.coalesce(
            RunResult.model_type, Run.model_type, "random_forest"
        ).label("model_type")

        query = (
            db.query(
                effective_model,
                func.count(RunResult.id).label("number_of_runs"),
                func.max(RunResult.accuracy).label("best_accuracy"),
                func.avg(RunResult.accuracy).label("average_accuracy"),
                func.max(RunResult.f1_score).label("best_f1"),
                func.avg(RunResult.f1_score).label("average_f1"),
                func.avg(RunResult.roc_auc).label("average_roc_auc"),
                func.avg(RunResult.execution_time_seconds).label("average_duration"),
            )
            .join(Run, RunResult.run_id == Run.id)
            .join(Experiment, Run.experiment_id == Experiment.id)
            .filter(Run.status == RunStatus.completed)
        )

        if dataset_id:
            query = query.filter(Experiment.dataset_id == dataset_id)
        if experiment_id:
            query = query.filter(Experiment.id == experiment_id)

        rows = query.group_by(effective_model).order_by(desc("best_accuracy")).all()

        results = []
        for r in rows:
            results.append({
                "model_type": str(r.model_type),
                "number_of_runs": int(r.number_of_runs),
                "best_accuracy": (
                    round(float(r.best_accuracy), 4)
                    if r.best_accuracy is not None
                    else None
                ),
                "average_accuracy": (
                    round(float(r.average_accuracy), 4)
                    if r.average_accuracy is not None
                    else None
                ),
                "best_f1": (
                    round(float(r.best_f1), 4) if r.best_f1 is not None else None
                ),
                "average_f1": (
                    round(float(r.average_f1), 4) if r.average_f1 is not None else None
                ),
                "average_roc_auc": (
                    round(float(r.average_roc_auc), 4)
                    if r.average_roc_auc is not None
                    else None
                ),
                "average_duration": (
                    round(float(r.average_duration), 2)
                    if r.average_duration is not None
                    else None
                ),
            })
        return results

    def get_experiment_metrics(
        self,
        db: Session,
        dataset_id: Optional[str] = None,
        model_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get experiment-level statistics and best run performance."""
        exp_query = db.query(Experiment, Dataset.name.label("dataset_name")).outerjoin(
            Dataset, Experiment.dataset_id == Dataset.id
        )

        if dataset_id:
            exp_query = exp_query.filter(Experiment.dataset_id == dataset_id)

        experiments = exp_query.order_by(Experiment.created_at.desc()).all()

        results = []
        for exp, dataset_name in experiments:
            # Runs query for this experiment
            run_query = db.query(Run).filter(Run.experiment_id == exp.id)
            if model_type:
                run_query = run_query.filter(Run.model_type == model_type)

            total_runs = run_query.count()

            # Latest run
            latest_run = (
                run_query.order_by(Run.created_at.desc()).first()
            )

            # Best run among completed
            best_run_row = (
                db.query(Run, RunResult)
                .join(RunResult, Run.id == RunResult.run_id)
                .filter(Run.experiment_id == exp.id)
            )
            if model_type:
                best_run_row = best_run_row.filter(Run.model_type == model_type)

            best_item = best_run_row.order_by(desc(RunResult.accuracy)).first()

            # Avg accuracy among completed
            avg_acc_row = (
                db.query(func.avg(RunResult.accuracy))
                .join(Run, Run.id == RunResult.run_id)
                .filter(Run.experiment_id == exp.id)
            )
            if model_type:
                avg_acc_row = avg_acc_row.filter(Run.model_type == model_type)
            avg_acc = avg_acc_row.scalar()

            results.append({
                "experiment_id": exp.id,
                "experiment_name": exp.name,
                "dataset_id": exp.dataset_id,
                "dataset_name": dataset_name or "Unknown",
                "total_runs": total_runs,
                "best_run_id": best_item[0].id if best_item else None,
                "best_run_number": best_item[0].run_number if best_item else None,
                "best_accuracy": (
                    round(float(best_item[1].accuracy), 4) if best_item else None
                ),
                "average_accuracy": (
                    round(float(avg_acc), 4) if avg_acc is not None else None
                ),
                "latest_run_id": latest_run.id if latest_run else None,
                "latest_run_number": latest_run.run_number if latest_run else None,
                "latest_run_status": latest_run.status.value if latest_run else None,
                "latest_run_created_at": (
                    latest_run.created_at if latest_run else None
                ),
            })

        return results

    def get_dataset_metrics(self, db: Session) -> List[Dict[str, Any]]:
        """Get dataset-level statistics with best performing model."""
        datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()

        results = []
        for ds in datasets:
            # Count experiments
            num_experiments = (
                db.query(func.count(Experiment.id))
                .filter(Experiment.dataset_id == ds.id)
                .scalar()
                or 0
            )

            # Count total runs across experiments of this dataset
            num_runs = (
                db.query(func.count(Run.id))
                .join(Experiment, Run.experiment_id == Experiment.id)
                .filter(Experiment.dataset_id == ds.id)
                .scalar()
                or 0
            )

            # Best model and accuracy on this dataset
            best_res = (
                db.query(RunResult.model_type, RunResult.accuracy)
                .join(Run, RunResult.run_id == Run.id)
                .join(Experiment, Run.experiment_id == Experiment.id)
                .filter(Experiment.dataset_id == ds.id)
                .order_by(desc(RunResult.accuracy))
                .first()
            )

            results.append({
                "dataset_id": ds.id,
                "dataset_name": ds.name,
                "number_of_experiments": num_experiments,
                "number_of_runs": num_runs,
                "best_model": str(best_res[0]) if best_res and best_res[0] else None,
                "best_accuracy": (
                    round(float(best_res[1]), 4) if best_res and best_res[1] is not None else None
                ),
            })

        return results

    def compare_runs(self, run_ids: List[str], db: Session) -> List[Dict[str, Any]]:
        """Fetch detailed run information and metrics for multiple runs."""
        if not run_ids:
            return []

        rows = (
            db.query(
                Run,
                Experiment.name.label("experiment_name"),
                Experiment.dataset_id.label("dataset_id"),
                Dataset.name.label("dataset_name"),
                RunResult,
            )
            .join(Experiment, Run.experiment_id == Experiment.id)
            .outerjoin(Dataset, Experiment.dataset_id == Dataset.id)
            .outerjoin(RunResult, Run.id == RunResult.run_id)
            .filter(Run.id.in_(run_ids))
            .all()
        )

        # Map by run id so we can preserve requested run_ids order
        row_map = {r[0].id: r for r in rows}

        results = []
        for rid in run_ids:
            if rid not in row_map:
                continue
            run_obj, exp_name, ds_id, ds_name, result_obj = row_map[rid]

            results.append({
                "run_id": run_obj.id,
                "run_number": run_obj.run_number,
                "experiment_id": run_obj.experiment_id,
                "experiment_name": exp_name,
                "dataset_id": ds_id,
                "dataset_name": ds_name or "Unknown",
                "model": (
                    result_obj.model_type
                    if result_obj and result_obj.model_type
                    else run_obj.model_type
                ),
                "accuracy": (
                    round(float(result_obj.accuracy), 4)
                    if result_obj and result_obj.accuracy is not None
                    else None
                ),
                "precision": (
                    round(float(result_obj.precision), 4)
                    if result_obj and result_obj.precision is not None
                    else None
                ),
                "recall": (
                    round(float(result_obj.recall), 4)
                    if result_obj and result_obj.recall is not None
                    else None
                ),
                "f1": (
                    round(float(result_obj.f1_score), 4)
                    if result_obj and result_obj.f1_score is not None
                    else None
                ),
                "roc_auc": (
                    round(float(result_obj.roc_auc), 4)
                    if result_obj and result_obj.roc_auc is not None
                    else None
                ),
                "duration": (
                    round(float(result_obj.execution_time_seconds), 2)
                    if result_obj and result_obj.execution_time_seconds is not None
                    else None
                ),
                "training_configuration": run_obj.training_configuration or {},
                "completed_at": (
                    result_obj.completed_at
                    if result_obj
                    else run_obj.updated_at
                ),
            })

        return results
