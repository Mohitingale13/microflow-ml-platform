"""
run_result_service.py — Business logic for RunResult retrieval.
"""

import logging

from sqlalchemy.orm import Session

from app.models.artifact import RunResult
from app.repositories.run_result_repository import RunResultRepository

logger = logging.getLogger(__name__)


class RunResultService:
    def __init__(self, run_result_repo: RunResultRepository) -> None:
        self._repo = run_result_repo

    def get_by_run_id(self, run_id: str, db: Session) -> RunResult | None:
        """Return the RunResult for a given run, or None if not yet persisted."""
        return self._repo.get_by_run_id(run_id, db)
