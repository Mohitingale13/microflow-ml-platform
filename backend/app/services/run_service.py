"""
RunService — business logic for Run management.

Responsibilities:
  - Create, update, queue, cancel, and delete runs
  - Validate experiment existence
  - Automatically assign sequential run numbers
  - Enforce the Run state machine
  - Merge experiment default_configuration with run-specific overrides
"""

import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.experiment import ExperimentStatus, Run, RunStatus
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.run_repository import RunRepository

logger = logging.getLogger(__name__)

# ── State machine ──────────────────────────────────────────────────────────────
# Maps each current status to the set of statuses it may transition to.
_ALLOWED_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.draft:     {RunStatus.queued, RunStatus.cancelled},
    RunStatus.queued:    {RunStatus.running, RunStatus.cancelled},
    RunStatus.running:   {RunStatus.completed, RunStatus.failed},
    RunStatus.completed: set(),   # terminal
    RunStatus.failed:    set(),   # terminal
    RunStatus.cancelled: set(),   # terminal
}


class RunService:
    def __init__(
        self,
        run_repo: RunRepository,
        experiment_repo: ExperimentRepository,
    ) -> None:
        self._repo = run_repo
        self._experiment_repo = experiment_repo

    # ── Queries ────────────────────────────────────────────────────────────────

    def get_all(self, db: Session) -> list[Run]:
        """Return every run across all experiments, newest first."""
        return self._repo.list_all(db)

    def get_by_id(self, run_id: str, db: Session) -> Run:
        run = self._repo.get_by_id(run_id, db)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run '{run_id}' not found",
            )
        return run

    def get_by_experiment(self, experiment_id: str, db: Session) -> list[Run]:
        self._assert_experiment_exists(experiment_id, db)
        return self._repo.list_by_experiment(experiment_id, db)

    # ── Commands ───────────────────────────────────────────────────────────────

    def create(
        self,
        *,
        experiment_id: str,
        model_type: str | None,
        training_configuration: dict[str, Any] | None,
        notes: str | None,
        db: Session,
    ) -> Run:
        experiment = self._assert_experiment_exists(experiment_id, db)

        if experiment.status == ExperimentStatus.draft:
            self._experiment_repo.update(db, experiment, status=ExperimentStatus.active)

        # Inherit and merge configuration: experiment defaults ← run overrides
        merged_config = self._merge_configuration(
            base=experiment.default_configuration,
            override=training_configuration,
        )

        run_number = self._repo.get_next_run_number(experiment_id, db)

        run = self._repo.create(
            db,
            experiment_id=experiment_id,
            run_number=run_number,
            model_type=model_type,
            training_configuration=merged_config,
            notes=notes,
        )
        logger.info(
            "Run created: id=%s experiment_id=%s run_number=%d",
            run.id,
            experiment_id,
            run_number,
        )
        return run

    def update(
        self,
        run_id: str,
        *,
        updates: dict[str, Any],
        db: Session,
    ) -> Run:
        run = self.get_by_id(run_id, db)

        # Status updates must go through the state machine helpers
        new_status = updates.get("status")
        if new_status:
            self._assert_transition_allowed(run.status, new_status)

        # If training_configuration is being updated, re-merge on top of experiment defaults
        if "training_configuration" in updates:
            experiment = self._experiment_repo.get_by_id(run.experiment_id, db)
            updates["training_configuration"] = self._merge_configuration(
                base=experiment.default_configuration if experiment else None,
                override=updates["training_configuration"],
            )

        run = self._repo.update(db, run, **updates)
        logger.info("Run updated: id=%s fields=%s", run_id, list(updates.keys()))
        return run

    def queue(self, run_id: str, db: Session) -> Run:
        run = self.get_by_id(run_id, db)
        self._assert_transition_allowed(run.status, RunStatus.queued)
        run = self._repo.update(db, run, status=RunStatus.queued)
        logger.info("Run queued: id=%s experiment_id=%s", run.id, run.experiment_id)
        return run

    def cancel(self, run_id: str, db: Session) -> Run:
        run = self.get_by_id(run_id, db)
        self._assert_transition_allowed(run.status, RunStatus.cancelled)
        run = self._repo.update(db, run, status=RunStatus.cancelled)
        logger.info("Run cancelled: id=%s experiment_id=%s", run.id, run.experiment_id)
        return run

    def delete(self, run_id: str, db: Session) -> None:
        run = self.get_by_id(run_id, db)
        if run.status in (RunStatus.running, RunStatus.queued):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot delete a run in '{run.status.value}' state. "
                    "Cancel it first."
                ),
            )
        self._repo.delete(run_id, db)
        logger.info("Run deleted: id=%s", run_id)

    # ── Internals ──────────────────────────────────────────────────────────────

    def _assert_experiment_exists(self, experiment_id: str, db: Session):
        experiment = self._experiment_repo.get_by_id(experiment_id, db)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment '{experiment_id}' not found",
            )
        return experiment

    def _assert_transition_allowed(
        self, current: RunStatus, target: RunStatus
    ) -> None:
        allowed = _ALLOWED_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Invalid status transition: '{current.value}' → '{target.value}'. "
                    f"Allowed transitions from '{current.value}': "
                    + (
                        ", ".join(f"'{s.value}'" for s in allowed)
                        if allowed
                        else "none (terminal state)"
                    )
                ),
            )

    @staticmethod
    def _merge_configuration(
        base: dict[str, Any] | None,
        override: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """
        Shallow-merge override on top of base without mutating either dict.

        Returns None if both inputs are None.
        Returns a new dict otherwise.
        """
        if base is None and override is None:
            return None
        merged: dict[str, Any] = {}
        if base:
            merged.update(base)
        if override:
            merged.update(override)
        return merged
