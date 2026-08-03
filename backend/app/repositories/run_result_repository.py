"""
run_result_repository.py — Data access for RunResult records.
"""

from typing import Any
from sqlalchemy.orm import Session

from app.models.artifact import RunResult


class RunResultRepository:
    def create(
        self,
        db: Session,
        *,
        run_id: str,
        accuracy: float,
        precision: float,
        recall: float,
        f1_score: float,
        roc_auc: float | None,
        confusion_matrix: list[list[int]],
        execution_time_seconds: float | None = None,
        started_at: Any = None,
        completed_at: Any = None,
        model_type: str | None = None,
        dataset_id: str | None = None,
        training_config_snapshot: dict[str, Any] | None = None,
        preprocessing_summary: dict[str, Any] | None = None,
    ) -> RunResult:
        result = RunResult(
            run_id=run_id,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            roc_auc=roc_auc,
            confusion_matrix=confusion_matrix,
            execution_time_seconds=execution_time_seconds,
            started_at=started_at,
            completed_at=completed_at,
            model_type=model_type,
            dataset_id=dataset_id,
            training_config_snapshot=training_config_snapshot,
            preprocessing_summary=preprocessing_summary,
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return result

    def get_by_run_id(self, run_id: str, db: Session) -> RunResult | None:
        return (
            db.query(RunResult)
            .filter(RunResult.run_id == run_id)
            .first()
        )

    def delete_by_run_id(self, run_id: str, db: Session) -> None:
        result = self.get_by_run_id(run_id, db)
        if result:
            db.delete(result)
            db.commit()
