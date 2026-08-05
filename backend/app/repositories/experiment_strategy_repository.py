"""
experiment_strategy_repository.py — Data access for ExperimentAIStrategy records.

Follows existing repository pattern:
  - Session-based
  - No business logic
  - Clean query and create methods
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.experiment_strategy import ExperimentAIStrategy


class ExperimentStrategyRepository:

    def get_by_experiment_and_hash(
        self, experiment_id: str, history_hash: str, db: Session
    ) -> ExperimentAIStrategy | None:
        """Return a cached strategy recommendation for this exact (experiment_id, history_hash) pair."""
        return (
            db.query(ExperimentAIStrategy)
            .filter(
                ExperimentAIStrategy.experiment_id == experiment_id,
                ExperimentAIStrategy.history_hash == history_hash,
            )
            .first()
        )

    def get_latest_by_experiment(self, experiment_id: str, db: Session) -> ExperimentAIStrategy | None:
        """Return the most recent AI strategy recommendation for an experiment regardless of hash."""
        return (
            db.query(ExperimentAIStrategy)
            .filter(ExperimentAIStrategy.experiment_id == experiment_id)
            .order_by(ExperimentAIStrategy.created_at.desc())
            .first()
        )

    def create(
        self,
        db: Session,
        *,
        experiment_id: str,
        history_hash: str,
        model_name: str,
        strategy_json: str,
    ) -> ExperimentAIStrategy:
        record = ExperimentAIStrategy(
            experiment_id=experiment_id,
            history_hash=history_hash,
            model_name=model_name,
            strategy_json=strategy_json,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
