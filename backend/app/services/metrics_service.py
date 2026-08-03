"""
metrics_service.py — Business logic service for analytics and performance metrics.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.repositories.metrics_repository import MetricsRepository


class MetricsService:
    """Service providing aggregated experiment performance analytics."""

    def __init__(self, metrics_repo: Optional[MetricsRepository] = None) -> None:
        self._repo = metrics_repo or MetricsRepository()

    def get_overview(self, db: Session) -> Dict[str, Any]:
        """Fetch global overview metrics."""
        return self._repo.get_overview(db)

    def get_model_metrics(
        self,
        db: Session,
        dataset_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch aggregated metrics grouped by model family."""
        return self._repo.get_model_metrics(
            db, dataset_id=dataset_id, experiment_id=experiment_id
        )

    def get_experiment_metrics(
        self,
        db: Session,
        dataset_id: Optional[str] = None,
        model_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch experiment-level statistics."""
        return self._repo.get_experiment_metrics(
            db, dataset_id=dataset_id, model_type=model_type
        )

    def get_dataset_metrics(self, db: Session) -> List[Dict[str, Any]]:
        """Fetch dataset-level statistics."""
        return self._repo.get_dataset_metrics(db)

    def compare_runs(self, run_ids_input: str | List[str], db: Session) -> List[Dict[str, Any]]:
        """Parse run IDs and return side-by-side run comparison metrics."""
        if isinstance(run_ids_input, str):
            # Split comma-separated IDs and strip whitespace
            run_ids = [r.strip() for r in run_ids_input.split(",") if r.strip()]
        else:
            run_ids = [r.strip() for r in run_ids_input if r and r.strip()]

        if not run_ids:
            return []

        # Deduplicate while preserving order
        seen = set()
        unique_ids = []
        for rid in run_ids:
            if rid not in seen:
                seen.add(rid)
                unique_ids.append(rid)

        return self._repo.compare_runs(unique_ids, db)
