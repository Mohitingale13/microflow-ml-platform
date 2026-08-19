"""
services/investigator_service.py — Service coordinating the Experiment Investigator Agent.
"""

from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from app.ai.gemini_service import GeminiService
from app.ai.investigator_agent import InvestigatorAgent, MAX_AGENT_ITERATIONS
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.metrics_repository import MetricsRepository
from app.repositories.run_repository import RunRepository
from app.repositories.run_result_repository import RunResultRepository
from app.schemas.investigator import InvestigateResponseData
from app.services.experiment_service import ExperimentService
from app.services.metrics_service import MetricsService
from app.services.run_result_service import RunResultService
from app.services.run_service import RunService

logger = logging.getLogger(__name__)


class InvestigatorService:
    def __init__(
        self,
        experiment_service: ExperimentService | None = None,
        run_service: RunService | None = None,
        run_result_service: RunResultService | None = None,
        metrics_service: MetricsService | None = None,
        gemini_service: GeminiService | None = None,
    ) -> None:
        exp_repo = ExperimentRepository()
        run_repo = RunRepository()
        result_repo = RunResultRepository()
        dataset_repo = DatasetRepository()
        metrics_repo = MetricsRepository()

        self._experiment_service = experiment_service or ExperimentService(
            experiment_repo=exp_repo,
            dataset_repo=dataset_repo,
        )
        self._run_service = run_service or RunService(
            run_repo=run_repo,
            experiment_repo=exp_repo,
        )
        self._run_result_service = run_result_service or RunResultService(
            run_result_repo=result_repo,
        )
        self._metrics_service = metrics_service or MetricsService(
            metrics_repo=metrics_repo,
        )
        self._gemini = gemini_service or GeminiService()
        self._agent = InvestigatorAgent(gemini_service=self._gemini)

    def investigate_experiment(
        self,
        experiment_id: str,
        objective: str,
        db: Session,
    ) -> InvestigateResponseData:
        """
        Validate experiment and execute agent investigation over real experiment data.
        """
        # 1. Assert experiment exists (raises 404 if not found)
        self._experiment_service.get_by_id(experiment_id, db)

        # 2. Run agent loop
        report, trace, iterations_used = self._agent.run_investigation(
            experiment_id=experiment_id,
            objective=objective,
            db=db,
            run_service=self._run_service,
            run_result_service=self._run_result_service,
            metrics_service=self._metrics_service,
        )

        return InvestigateResponseData(
            experiment_id=experiment_id,
            objective=objective,
            conclusion=report.conclusion,
            evidence=report.evidence,
            recommendations=report.recommendations,
            limitations=report.limitations,
            trace=trace,
            iterations_used=iterations_used,
            max_iterations=MAX_AGENT_ITERATIONS,
        )
