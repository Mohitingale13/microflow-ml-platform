"""
ai_review_service.py — Business logic for AI Run Review generation.

Orchestrates the full review lifecycle:
  1. Fetch and validate the run (must be completed).
  2. Fetch the experiment and dataset.
  3. Fetch all completed runs in the same experiment to determine best run.
  4. Build the structured Gemini prompt.
  5. Compute prompt hash and check cache.
  6. If cached, return immediately.
  7. If not cached, call Gemini, parse response, store, return.

This service never calls HTTP endpoints and never contains SQL.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.cache_service import compute_prompt_hash
from app.ai.gemini_service import GeminiService
from app.ai.prompt_builder import build_review_prompt
from app.ai.response_parser import parse_gemini_response
from app.ai.schemas import AIReviewResponse
from app.models.ai_review import RunAIReview
from app.models.artifact import RunResult
from app.models.experiment import Run, RunStatus
from app.repositories.ai_review_repository import AIReviewRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.run_repository import RunRepository
from app.repositories.run_result_repository import RunResultRepository
from app.repositories.dataset_repository import DatasetRepository

logger = logging.getLogger(__name__)


def _to_response(record: RunAIReview, *, cached: bool) -> AIReviewResponse:
    return AIReviewResponse(
        id=record.id,
        run_id=record.run_id,
        overall_assessment=record.overall_assessment,
        strengths=record.strengths,
        weaknesses=record.weaknesses,
        comparison=record.comparison,
        recommendation=record.recommendation,
        model_name=record.model_name,
        generated_at=record.created_at,
        cached=cached,
    )


class AIReviewService:
    def __init__(
        self,
        run_repo: RunRepository,
        experiment_repo: ExperimentRepository,
        run_result_repo: RunResultRepository,
        dataset_repo: DatasetRepository,
        ai_review_repo: AIReviewRepository,
        gemini_service: GeminiService,
    ) -> None:
        self._run_repo = run_repo
        self._experiment_repo = experiment_repo
        self._run_result_repo = run_result_repo
        self._dataset_repo = dataset_repo
        self._ai_review_repo = ai_review_repo
        self._gemini = gemini_service

    def get_or_generate_review(self, run_id: str, db: Session) -> AIReviewResponse:
        """
        Return an AI review for the given run, generating one via Gemini if
        no cached review exists for the current prompt hash.

        Raises
        ------
        HTTPException 404
            If the run does not exist.
        HTTPException 422
            If the run is not in 'completed' status.
        HTTPException 503
            If the Gemini API call fails (key missing or API error).
        """
        # ── 1. Fetch & validate run ───────────────────────────────────────────
        run: Run | None = self._run_repo.get_by_id(run_id, db)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run '{run_id}' not found.",
            )
        if run.status != RunStatus.completed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"AI reviews can only be generated for completed runs. "
                    f"Current status: '{run.status.value}'."
                ),
            )

        # ── 2. Fetch experiment, dataset, run result ───────────────────────────
        experiment = self._experiment_repo.get_by_id(run.experiment_id, db)
        dataset = (
            self._dataset_repo.get_by_id(experiment.dataset_id, db)
            if experiment and experiment.dataset_id
            else None
        )
        run_result: RunResult | None = self._run_result_repo.get_by_run_id(run_id, db)

        # ── 3. Determine best run in experiment ───────────────────────────────
        best_run: Run | None = None
        best_result: RunResult | None = None
        all_runs = self._run_repo.list_by_experiment(run.experiment_id, db)
        completed_runs = [
            r for r in all_runs if r.status == RunStatus.completed
        ]

        if completed_runs:
            # Resolve results for each completed run and pick highest accuracy
            run_results_map: dict[str, RunResult] = {}
            for r in completed_runs:
                rr = self._run_result_repo.get_by_run_id(r.id, db)
                if rr:
                    run_results_map[r.id] = rr

            best_run = max(
                (r for r in completed_runs if r.id in run_results_map),
                key=lambda r: run_results_map[r.id].accuracy,
                default=None,
            )
            if best_run:
                best_result = run_results_map.get(best_run.id)

        # ── 4. Build prompt ───────────────────────────────────────────────────
        prompt = build_review_prompt(
            run=run,
            experiment=experiment,
            dataset=dataset,
            run_result=run_result,
            best_run=best_run,
            best_result=best_result,
        )

        # ── 5. Check cache ────────────────────────────────────────────────────
        prompt_hash = compute_prompt_hash(prompt)
        cached_record = self._ai_review_repo.get_by_run_and_hash(
            run_id, prompt_hash, db
        )
        if cached_record:
            logger.info(
                "Returning cached AI review for run '%s' (hash=%s)",
                run_id,
                prompt_hash[:8],
            )
            return _to_response(cached_record, cached=True)

        # ── 6. Call Gemini ────────────────────────────────────────────────────
        logger.info(
            "Generating fresh AI review for run '%s' via Gemini", run_id
        )
        try:
            raw_response = self._gemini.generate_review(prompt)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        # ── 7. Parse response ─────────────────────────────────────────────────
        try:
            content = parse_gemini_response(raw_response)
        except ValueError as exc:
            logger.error(
                "Failed to parse Gemini response for run '%s': %s", run_id, exc
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI response could not be parsed: {exc}",
            ) from exc

        # ── 8. Store in cache ─────────────────────────────────────────────────
        record = self._ai_review_repo.create(
            db,
            run_id=run_id,
            prompt_hash=prompt_hash,
            model_name=self._gemini.model_name,
            review_text=raw_response,
            overall_assessment=content.overall_assessment,
            strengths=content.strengths,
            weaknesses=content.weaknesses,
            comparison=content.comparison,
            recommendation=content.recommendation,
        )

        try:
            from app.services.embedding_service import EmbeddingService
            EmbeddingService(gemini_service=self._gemini).index_ai_review(db, record, run, experiment)
        except Exception as exc:
            logger.warning("Embedding indexing failed for AI Review %s: %s", record.id, exc)

        return _to_response(record, cached=False)
