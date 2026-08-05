"""
run_comparison_service.py — Business logic for AI Run Comparison generation.

Orchestrates the full comparison lifecycle:
  1. Load and validate both runs (must exist, both completed, same experiment).
  2. Load experiment, dataset, and RunResult for each run.
  3. Compute metric deltas (Accuracy, Precision, Recall, F1, ROC AUC, Exec Time).
  4. Build the structured Gemini comparison prompt.
  5. Compute prompt hash and check cache.
  6. If cached, return immediately — no Gemini call is made.
  7. If not cached, call GeminiService.generate_comparison(), parse, store, return.

This service never calls HTTP endpoints and never contains SQL.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.cache_service import compute_prompt_hash
from app.ai.gemini_service import GeminiService
from app.ai.prompt_builder import build_comparison_prompt, _compute_delta
from app.ai.response_parser import parse_comparison_response
from app.ai.schemas import AIComparisonResponse, MetricDelta
from app.models.run_comparison import RunAIComparison
from app.models.artifact import RunResult
from app.models.experiment import Run, RunStatus
from app.repositories.run_comparison_repository import RunComparisonRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.run_repository import RunRepository
from app.repositories.run_result_repository import RunResultRepository
from app.repositories.dataset_repository import DatasetRepository

logger = logging.getLogger(__name__)


def _build_metric_deltas(result_a: RunResult | None, result_b: RunResult | None) -> list[MetricDelta]:
    """Compute a MetricDelta list from two RunResult objects."""

    def _delta(metric: str, a_val: float | None, b_val: float | None) -> MetricDelta:
        _, direction = _compute_delta(a_val, b_val)
        delta_val = (b_val - a_val) if (a_val is not None and b_val is not None) else None
        return MetricDelta(
            metric=metric,
            run_a_value=a_val,
            run_b_value=b_val,
            delta=delta_val,
            direction=direction,
        )

    return [
        _delta("Accuracy",       result_a.accuracy if result_a else None,        result_b.accuracy if result_b else None),
        _delta("Precision",      result_a.precision if result_a else None,        result_b.precision if result_b else None),
        _delta("Recall",         result_a.recall if result_a else None,           result_b.recall if result_b else None),
        _delta("F1 Score",       result_a.f1_score if result_a else None,         result_b.f1_score if result_b else None),
        _delta("ROC AUC",        result_a.roc_auc if result_a else None,          result_b.roc_auc if result_b else None),
        _delta(
            "Execution Time (s)",
            result_a.execution_time_seconds if result_a else None,
            result_b.execution_time_seconds if result_b else None,
        ),
    ]


def _to_response(
    record: RunAIComparison,
    metric_deltas: list[MetricDelta],
    *,
    cached: bool,
) -> AIComparisonResponse:
    return AIComparisonResponse(
        id=record.id,
        run_a_id=record.run_a_id,
        run_b_id=record.run_b_id,
        overall_summary=record.overall_summary,
        better_run=record.better_run,
        key_improvements=record.key_improvements,
        tradeoffs=record.tradeoffs,
        configuration_analysis=record.configuration_analysis,
        next_recommendation=record.next_recommendation,
        metric_deltas=metric_deltas,
        model_name=record.model_name,
        generated_at=record.created_at,
        cached=cached,
    )


class RunComparisonService:
    def __init__(
        self,
        run_repo: RunRepository,
        experiment_repo: ExperimentRepository,
        run_result_repo: RunResultRepository,
        dataset_repo: DatasetRepository,
        comparison_repo: RunComparisonRepository,
        gemini_service: GeminiService,
    ) -> None:
        self._run_repo = run_repo
        self._experiment_repo = experiment_repo
        self._run_result_repo = run_result_repo
        self._dataset_repo = dataset_repo
        self._comparison_repo = comparison_repo
        self._gemini = gemini_service

    def get_or_generate_comparison(
        self,
        run_a_id: str,
        run_b_id: str,
        db: Session,
    ) -> AIComparisonResponse:
        """
        Return an AI comparison for the given run pair, generating one via Gemini
        if no cached comparison exists for the current prompt hash.

        Raises
        ------
        HTTPException 400
            If run_a_id == run_b_id (comparing a run to itself).
        HTTPException 404
            If either run does not exist.
        HTTPException 422
            If either run is not 'completed', or if they belong to different experiments.
        HTTPException 503
            If the Gemini API call fails (key missing or API error).
        """

        # ── Validate inputs ───────────────────────────────────────────────────
        if run_a_id == run_b_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="run_a_id and run_b_id must be different runs.",
            )

        # ── 1. Load both runs ─────────────────────────────────────────────────
        run_a: Run | None = self._run_repo.get_by_id(run_a_id, db)
        if not run_a:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run '{run_a_id}' not found.",
            )

        run_b: Run | None = self._run_repo.get_by_id(run_b_id, db)
        if not run_b:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run '{run_b_id}' not found.",
            )

        # ── 2. Validate — both completed ──────────────────────────────────────
        if run_a.status != RunStatus.completed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Run A (#{run_a.run_number}) must be completed before comparison. "
                    f"Current status: '{run_a.status.value}'."
                ),
            )
        if run_b.status != RunStatus.completed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Run B (#{run_b.run_number}) must be completed before comparison. "
                    f"Current status: '{run_b.status.value}'."
                ),
            )

        # ── 3. Validate — same experiment ────────────────────────────────────
        if run_a.experiment_id != run_b.experiment_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Both runs must belong to the same experiment. "
                    f"Run A belongs to experiment '{run_a.experiment_id}', "
                    f"Run B belongs to experiment '{run_b.experiment_id}'."
                ),
            )

        # ── 4. Load experiment, dataset, and results ──────────────────────────
        experiment = self._experiment_repo.get_by_id(run_a.experiment_id, db)
        dataset = (
            self._dataset_repo.get_by_id(experiment.dataset_id, db)
            if experiment and experiment.dataset_id
            else None
        )
        result_a: RunResult | None = self._run_result_repo.get_by_run_id(run_a_id, db)
        result_b: RunResult | None = self._run_result_repo.get_by_run_id(run_b_id, db)

        # ── 5. Build prompt ───────────────────────────────────────────────────
        prompt = build_comparison_prompt(
            run_a=run_a,
            run_b=run_b,
            experiment=experiment,
            dataset=dataset,
            result_a=result_a,
            result_b=result_b,
        )

        # ── 6. Compute metric deltas (used in both cached + fresh responses) ──
        metric_deltas = _build_metric_deltas(result_a, result_b)

        # ── 7. Check cache ────────────────────────────────────────────────────
        prompt_hash = compute_prompt_hash(prompt)
        cached_record = self._comparison_repo.get_by_pair_and_hash(
            run_a_id, run_b_id, prompt_hash, db
        )
        if cached_record:
            logger.info(
                "Returning cached AI comparison for runs '%s' vs '%s' (hash=%s)",
                run_a_id,
                run_b_id,
                prompt_hash[:8],
            )
            return _to_response(cached_record, metric_deltas, cached=True)

        # ── 8. Call Gemini ────────────────────────────────────────────────────
        logger.info(
            "Generating fresh AI comparison for runs '%s' vs '%s' via Gemini",
            run_a_id,
            run_b_id,
        )
        try:
            raw_response = self._gemini.generate_comparison(prompt)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        # ── 9. Parse response ─────────────────────────────────────────────────
        try:
            content = parse_comparison_response(raw_response)
        except ValueError as exc:
            logger.error(
                "Failed to parse Gemini comparison for runs '%s' vs '%s': %s",
                run_a_id,
                run_b_id,
                exc,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI comparison response could not be parsed: {exc}",
            ) from exc

        # ── 10. Store in cache ────────────────────────────────────────────────
        record = self._comparison_repo.create(
            db,
            run_a_id=run_a_id,
            run_b_id=run_b_id,
            prompt_hash=prompt_hash,
            model_name=self._gemini.model_name,
            overall_summary=content.overall_summary,
            better_run=content.better_run,
            key_improvements=content.key_improvements,
            tradeoffs=content.tradeoffs,
            configuration_analysis=content.configuration_analysis,
            next_recommendation=content.next_recommendation,
        )

        return _to_response(record, metric_deltas, cached=False)
