"""
dashboard_service.py — Business logic for the Dashboard.

Single responsibility: coordinate DashboardRepository and enforce
any business rules (validation, defaults) before returning data.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    """Service providing aggregated platform-wide data for the dashboard."""

    def __init__(self, dashboard_repo: Optional[DashboardRepository] = None) -> None:
        self._repo = dashboard_repo or DashboardRepository()

    def get_overview(self, db: Session) -> Dict[str, Any]:
        """Return platform-wide summary statistics."""
        return self._repo.get_overview(db)

    def get_activity(self, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recent platform activity feed, newest first."""
        limit = max(1, min(limit, 100))  # clamp between 1 and 100
        return self._repo.get_activity(db, limit=limit)

    def get_recent_runs(self, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the N most recent runs with full execution context."""
        limit = max(1, min(limit, 50))  # clamp between 1 and 50
        return self._repo.get_recent_runs(db, limit=limit)

    def get_quick_stats(self, db: Session) -> Dict[str, Any]:
        """Return best model, best experiment, most used dataset, latest artifact."""
        return self._repo.get_quick_stats(db)
