from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.experiment import Run, RunStatus


class RunRepository:
    def create(
        self,
        db: Session,
        *,
        experiment_id: str,
        run_number: int,
        model_type: str | None = None,
        training_configuration: dict[str, Any] | None = None,
        notes: str | None = None,
    ) -> Run:
        run = Run(
            experiment_id=experiment_id,
            run_number=run_number,
            model_type=model_type,
            training_configuration=training_configuration,
            notes=notes,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    def get_by_id(self, run_id: str, db: Session) -> Run | None:
        return db.query(Run).filter(Run.id == run_id).first()

    def list_all(self, db: Session) -> list[Run]:
        return db.query(Run).order_by(Run.created_at.desc()).all()

    def list_by_experiment(
        self, experiment_id: str, db: Session
    ) -> list[Run]:
        return (
            db.query(Run)
            .filter(Run.experiment_id == experiment_id)
            .order_by(Run.run_number.asc())
            .all()
        )

    def list_by_status(self, status: RunStatus, db: Session) -> list[Run]:
        return (
            db.query(Run)
            .filter(Run.status == status)
            .order_by(Run.created_at.desc())
            .all()
        )

    def get_next_run_number(self, experiment_id: str, db: Session) -> int:
        """Return the next sequential run number for a given experiment."""
        max_number = (
            db.query(func.max(Run.run_number))
            .filter(Run.experiment_id == experiment_id)
            .scalar()
        )
        return (max_number or 0) + 1

    def update(self, db: Session, run: Run, **kwargs: Any) -> Run:
        for key, value in kwargs.items():
            setattr(run, key, value)
        run.updated_at = datetime.now(timezone.utc)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    def delete(self, run_id: str, db: Session) -> None:
        run = self.get_by_id(run_id, db)
        if run:
            db.delete(run)
            db.commit()

    def count_by_experiment(self, experiment_id: str, db: Session) -> int:
        return (
            db.query(func.count(Run.id))
            .filter(Run.experiment_id == experiment_id)
            .scalar()
            or 0
        )
