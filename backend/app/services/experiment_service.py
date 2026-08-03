"""
ExperimentService — business logic for Experiment management.

Responsibilities:
  - Create, update, archive, and delete experiments
  - Validate dataset existence
  - Enforce unique experiment names per dataset
  - List and retrieve experiments
"""

import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.experiment import Experiment, ExperimentStatus
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository

logger = logging.getLogger(__name__)


class ExperimentService:
    def __init__(
        self,
        experiment_repo: ExperimentRepository,
        dataset_repo: DatasetRepository,
    ) -> None:
        self._repo = experiment_repo
        self._dataset_repo = dataset_repo

    # ── Queries ────────────────────────────────────────────────────────────────

    def get_all(self, db: Session) -> list[Experiment]:
        return self._repo.list_all(db)

    def get_by_id(self, experiment_id: str, db: Session) -> Experiment:
        experiment = self._repo.get_by_id(experiment_id, db)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment '{experiment_id}' not found",
            )
        return experiment

    def get_by_dataset(self, dataset_id: str, db: Session) -> list[Experiment]:
        self._assert_dataset_exists(dataset_id, db)
        return self._repo.list_by_dataset(dataset_id, db)

    # ── Commands ───────────────────────────────────────────────────────────────

    def create(
        self,
        *,
        name: str,
        dataset_id: str,
        description: str | None,
        objective: str | None,
        default_configuration: dict[str, Any] | None,
        tags: list[str] | None,
        db: Session,
    ) -> Experiment:
        self._assert_dataset_exists(dataset_id, db)
        self._assert_unique_name_in_dataset(name, dataset_id, exclude_id=None, db=db)

        experiment = self._repo.create(
            db,
            name=name,
            dataset_id=dataset_id,
            description=description,
            objective=objective,
            default_configuration=default_configuration,
            tags=tags,
        )
        logger.info(
            "Experiment created: id=%s name=%r dataset_id=%s",
            experiment.id,
            experiment.name,
            dataset_id,
        )
        return experiment

    def update(
        self,
        experiment_id: str,
        *,
        updates: dict[str, Any],
        db: Session,
    ) -> Experiment:
        experiment = self.get_by_id(experiment_id, db)

        # If name is being changed, re-validate uniqueness
        new_name = updates.get("name")
        if new_name and new_name != experiment.name:
            self._assert_unique_name_in_dataset(
                new_name, experiment.dataset_id, exclude_id=experiment_id, db=db
            )

        # Reject invalid status transitions via update (archive is the allowed path)
        new_status = updates.get("status")
        if new_status and new_status not in (
            ExperimentStatus.draft,
            ExperimentStatus.active,
            ExperimentStatus.archived,
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status transition to '{new_status}'",
            )

        experiment = self._repo.update(db, experiment, **updates)
        logger.info("Experiment updated: id=%s fields=%s", experiment_id, list(updates.keys()))
        return experiment

    def archive(self, experiment_id: str, db: Session) -> Experiment:
        experiment = self.get_by_id(experiment_id, db)
        if experiment.status == ExperimentStatus.archived:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Experiment is already archived",
            )
        experiment = self._repo.update(db, experiment, status=ExperimentStatus.archived)
        logger.info("Experiment archived: id=%s", experiment_id)
        return experiment

    def delete(self, experiment_id: str, db: Session) -> None:
        experiment = self.get_by_id(experiment_id, db)
        if experiment.status == ExperimentStatus.active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete an active experiment. Archive it first.",
            )
        self._repo.delete(experiment_id, db)
        logger.info("Experiment deleted: id=%s", experiment_id)

    # ── Internals ──────────────────────────────────────────────────────────────

    def _assert_dataset_exists(self, dataset_id: str, db: Session) -> None:
        if not self._dataset_repo.get_by_id(dataset_id, db):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset '{dataset_id}' not found",
            )

    def _assert_unique_name_in_dataset(
        self,
        name: str,
        dataset_id: str,
        exclude_id: str | None,
        db: Session,
    ) -> None:
        experiments = self._repo.list_by_dataset(dataset_id, db)
        for exp in experiments:
            if exp.name == name and exp.id != exclude_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"An experiment named '{name}' already exists "
                        f"in dataset '{dataset_id}'"
                    ),
                )
