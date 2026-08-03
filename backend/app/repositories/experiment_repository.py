from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.experiment import Experiment, ExperimentStatus


class ExperimentRepository:
    def create(
        self,
        db: Session,
        *,
        name: str,
        dataset_id: str,
        description: str | None = None,
        objective: str | None = None,
        default_configuration: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> Experiment:
        experiment = Experiment(
            name=name,
            dataset_id=dataset_id,
            description=description,
            objective=objective,
            default_configuration=default_configuration,
            tags=tags,
        )
        db.add(experiment)
        db.commit()
        db.refresh(experiment)
        return experiment

    def get_by_id(self, experiment_id: str, db: Session) -> Experiment | None:
        return (
            db.query(Experiment)
            .filter(Experiment.id == experiment_id)
            .first()
        )

    def list_all(self, db: Session) -> list[Experiment]:
        return (
            db.query(Experiment)
            .order_by(Experiment.created_at.desc())
            .all()
        )

    def list_by_dataset(self, dataset_id: str, db: Session) -> list[Experiment]:
        return (
            db.query(Experiment)
            .filter(Experiment.dataset_id == dataset_id)
            .order_by(Experiment.created_at.desc())
            .all()
        )

    def list_by_status(
        self, status: ExperimentStatus, db: Session
    ) -> list[Experiment]:
        return (
            db.query(Experiment)
            .filter(Experiment.status == status)
            .order_by(Experiment.created_at.desc())
            .all()
        )

    def update(
        self, db: Session, experiment: Experiment, **kwargs: Any
    ) -> Experiment:
        for key, value in kwargs.items():
            setattr(experiment, key, value)
        experiment.updated_at = datetime.now(timezone.utc)
        db.add(experiment)
        db.commit()
        db.refresh(experiment)
        return experiment

    def delete(self, experiment_id: str, db: Session) -> None:
        experiment = self.get_by_id(experiment_id, db)
        if experiment:
            db.delete(experiment)
            db.commit()

    def count(self, db: Session) -> int:
        return db.query(func.count(Experiment.id)).scalar() or 0
