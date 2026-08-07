"""
experiment_strategy_service.py — Business logic and evidence engine for AI Experiment Strategy.

Computes comprehensive empirical evidence across an experiment's runs and dataset,
applies plateau detection and variance analysis, queries cache, and invokes Gemini
to provide grounded engineering recommendations.
"""

import hashlib
import json
import logging
import math
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.gemini_service import GeminiService
from app.ai.prompt_builder import build_experiment_strategy_prompt
from app.ai.response_parser import parse_experiment_strategy_response
from app.ai.schemas import ExperimentStrategyResponse
from app.models.experiment import ExperimentStatus, RunStatus
from app.models.experiment_strategy import ExperimentAIStrategy
from app.repositories.dataset_ai_analysis_repository import DatasetAIAnalysisRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.experiment_strategy_repository import ExperimentStrategyRepository
from app.repositories.run_repository import RunRepository

logger = logging.getLogger(__name__)

CANONICAL_MODELS = {"Random Forest", "XGBoost", "Logistic Regression"}
MODEL_ALIASES = {
    "randomforestclassifier": "Random Forest",
    "random forest": "Random Forest",
    "xgbclassifier": "XGBoost",
    "xgboost": "XGBoost",
    "logisticregression": "Logistic Regression",
    "logistic regression": "Logistic Regression",
}


class ExperimentStrategyService:

    def __init__(
        self,
        experiment_repo: ExperimentRepository | None = None,
        run_repo: RunRepository | None = None,
        dataset_repo: DatasetRepository | None = None,
        strategy_repo: ExperimentStrategyRepository | None = None,
        dataset_analysis_repo: DatasetAIAnalysisRepository | None = None,
        gemini_service: GeminiService | None = None,
    ):
        self._experiment_repo = experiment_repo or ExperimentRepository()
        self._run_repo = run_repo or RunRepository()
        self._dataset_repo = dataset_repo or DatasetRepository()
        self._strategy_repo = strategy_repo or ExperimentStrategyRepository()
        self._dataset_analysis_repo = dataset_analysis_repo or DatasetAIAnalysisRepository()
        self._gemini_service = gemini_service or GeminiService()

    def get_or_generate_strategy(
        self, experiment_id: str, db: Session
    ) -> ExperimentStrategyResponse:
        """
        Compute quantitative evidence, check cache by state hash, and generate or return
        evidence-driven strategy recommendations for an experiment.
        """
        experiment = self._experiment_repo.get_by_id(experiment_id, db)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment '{experiment_id}' not found.",
            )

        dataset = self._dataset_repo.get_by_id(experiment.dataset_id, db)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Associated dataset '{experiment.dataset_id}' not found.",
            )

        runs = self._run_repo.list_by_experiment(experiment_id, db)

        # 1. Compute state hash representing exact history and dataset version
        history_hash = self._compute_history_hash(runs, dataset.version or 1)

        # 2. Check cache layer
        cached = self._strategy_repo.get_by_experiment_and_hash(experiment_id, history_hash, db)
        if cached:
            try:
                data_map = json.loads(cached.strategy_json)
                evidence_summary = self._compute_evidence(experiment, dataset, runs, db)
                return self._to_response_schema(cached, data_map, is_cached=True, evidence_summary=evidence_summary)
            except Exception as exc:
                logger.warning("Cached strategy JSON malformed for %s: %s. Regenerating.", experiment_id, exc)

        # 3. Compute structured quantitative evidence
        evidence_summary = self._compute_evidence(experiment, dataset, runs, db)

        # 4. Build deterministic prompt and generate via Gemini
        prompt = build_experiment_strategy_prompt(experiment, dataset, evidence_summary)
        try:
            raw_text = self._gemini_service.generate_experiment_strategy(prompt)
            parsed = parse_experiment_strategy_response(raw_text)
        except Exception as exc:
            logger.error("Gemini experiment strategy evaluation failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI experiment strategy evaluation failed: {exc}",
            ) from exc

        # 5. Save to database cache
        try:
            record = self._strategy_repo.create(
                db=db,
                experiment_id=experiment_id,
                history_hash=history_hash,
                model_name=self._gemini_service.model_name,
                strategy_json=json.dumps(parsed, ensure_ascii=False),
            )
        except Exception as exc:
            logger.error("Failed to persist experiment strategy cache: %s", exc)
            # Return transient response if DB commit encountered race condition
            record = ExperimentAIStrategy(
                id="transient-" + experiment_id,
                experiment_id=experiment_id,
                history_hash=history_hash,
                model_name=self._gemini_service.model_name,
                strategy_json=json.dumps(parsed, ensure_ascii=False),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

        try:
            from app.services.embedding_service import EmbeddingService
            EmbeddingService(gemini_service=self._gemini_service).index_ai_strategy(db, record, experiment)
        except Exception as exc:
            logger.warning("Embedding indexing failed for AI Strategy %s: %s", record.id, exc)

        return self._to_response_schema(record, parsed, is_cached=False, evidence_summary=evidence_summary)

    def _compute_history_hash(self, runs: list[Any], dataset_version: str | int) -> str:
        """Generate SHA-256 hash representing exact run status, timestamps, and metrics."""
        signature_items = [f"ds_ver:{dataset_version}"]
        for r in sorted(runs, key=lambda x: x.run_number):
            status_val = r.status.value if hasattr(r.status, "value") else str(r.status)
            res_str = ""
            if getattr(r, "result", None):
                res = r.result
                res_str = f"|acc={res.accuracy:.5f}|f1={res.f1_score:.5f}|auc={res.roc_auc or 0:.5f}"
            signature_items.append(f"run_{r.run_number}:{status_val}{res_str}")
        signature_str = "||".join(signature_items)
        return hashlib.sha256(signature_str.encode("utf-8")).hexdigest()

    def _normalize_model_name(self, name: str | None) -> str:
        if not name:
            return "Unknown"
        clean = name.strip().lower()
        return MODEL_ALIASES.get(clean, name.strip())

    def _compute_evidence(
        self, experiment: Any, dataset: Any, runs: list[Any], db: Session
    ) -> dict[str, Any]:
        """Compute exhaustive empirical evidence for the experiment strategist."""
        # A. Dataset intelligence review
        dt_analysis = self._dataset_analysis_repo.get_latest_by_dataset(str(dataset.id), db)
        dt_info: dict[str, Any] = {
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "file_size_bytes": dataset.file_size_bytes,
            "version": dataset.version,
        }
        if dt_analysis and dt_analysis.analysis_json:
            try:
                dt_map = json.loads(dt_analysis.analysis_json)
                dt_info["ai_insights"] = {
                    "overall_summary": dt_map.get("overall_summary"),
                    "recommended_target": dt_map.get("recommended_target"),
                    "quality": dt_map.get("dataset_quality"),
                    "potential_issues": dt_map.get("potential_issues", []),
                }
            except Exception:
                pass

        # B. Organize completed and failed runs
        completed_runs = []
        failed_runs = []
        in_progress_runs = []

        for r in sorted(runs, key=lambda x: x.run_number):
            status_str = r.status.value if hasattr(r.status, "value") else str(r.status)
            if status_str == "completed" and getattr(r, "result", None):
                completed_runs.append(r)
            elif status_str == "failed":
                failed_runs.append({
                    "run_number": r.run_number,
                    "model_type": self._normalize_model_name(r.model_type),
                    "notes": r.notes or "No diagnostic details recorded.",
                })
            else:
                in_progress_runs.append(r.run_number)

        total_completed = len(completed_runs)

        if total_completed == 0:
            return {
                "dataset_summary": dt_info,
                "run_counts": {"completed": 0, "failed": len(failed_runs), "in_progress": len(in_progress_runs)},
                "failed_runs_history": failed_runs,
                "metrics_analysis": {"status": "No completed training runs available."},
                "search_space": {
                    "evaluated_models": [],
                    "unexplored_model_families": sorted(list(CANONICAL_MODELS)),
                    "hyperparameter_summary": "No hyperparameters tested yet.",
                },
                "trend_and_plateau_analysis": {
                    "plateau_detected": False,
                    "improvement_trend": "No baseline established.",
                    "recommendation_hint": "Execute baseline training runs across all supported model families (Random Forest, XGBoost, Logistic Regression).",
                }
            }

        # C. Calculate metric statistics (averages, bests, variance)
        accuracies = [r.result.accuracy for r in completed_runs]
        f1_scores = [r.result.f1_score for r in completed_runs]
        precisions = [r.result.precision for r in completed_runs]
        recalls = [r.result.recall for r in completed_runs]
        roc_aucs = [r.result.roc_auc for r in completed_runs if r.result.roc_auc is not None]

        avg_acc = sum(accuracies) / total_completed
        avg_f1 = sum(f1_scores) / total_completed

        # Variance & Standard Deviation
        var_acc = sum((x - avg_acc) ** 2 for x in accuracies) / total_completed
        std_acc = math.sqrt(var_acc)
        var_f1 = sum((x - avg_f1) ** 2 for x in f1_scores) / total_completed

        best_run_acc = max(completed_runs, key=lambda x: x.result.accuracy)
        best_run_f1 = max(completed_runs, key=lambda x: x.result.f1_score)

        # D. Speed comparison (Fastest vs Slowest)
        timed_runs = [r for r in completed_runs if r.result.execution_time_seconds is not None and r.result.execution_time_seconds > 0]
        fastest_model = "N/A"
        slowest_model = "N/A"
        if timed_runs:
            f_run = min(timed_runs, key=lambda x: x.result.execution_time_seconds)
            s_run = max(timed_runs, key=lambda x: x.result.execution_time_seconds)
            fastest_model = f"Experiment: {experiment.name} — Run #{f_run.run_number} ({self._normalize_model_name(f_run.model_type)}) - {f_run.result.execution_time_seconds:.2f}s"
            slowest_model = f"Experiment: {experiment.name} — Run #{s_run.run_number} ({self._normalize_model_name(s_run.model_type)}) - {s_run.result.execution_time_seconds:.2f}s"

        # E. Configurations already tested & Search space coverage
        evaluated_families = set()
        config_summaries = []
        hp_explored: dict[str, list[Any]] = {}

        for r in completed_runs:
            fam = self._normalize_model_name(r.model_type or getattr(r.result, "model_type", None))
            evaluated_families.add(fam)
            cfg = r.training_configuration or r.result.training_config_snapshot or {}
            config_summaries.append({
                "run_name": f"Experiment: {experiment.name} — Run #{r.run_number}",
                "model": fam,
                "accuracy": round(r.result.accuracy, 4),
                "f1_score": round(r.result.f1_score, 4),
                "parameters": cfg,
            })
            for k, v in cfg.items():
                if isinstance(v, (int, float, str, bool)):
                    hp_explored.setdefault(k, []).append(v)

        unexplored_families = sorted(list(CANONICAL_MODELS - evaluated_families))

        # F. Hyperparameter gap analysis
        hp_insights = []
        for param, vals in hp_explored.items():
            nums = [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
            if nums:
                min_v, max_v = min(nums), max(nums)
                if param == "n_estimators" and max_v <= 100:
                    hp_insights.append(f"n_estimators tested only up to {max_v}; higher tree ensembles (200-500) remain untested.")
                elif param == "max_depth" and max_v <= 5:
                    hp_insights.append(f"max_depth tested up to {max_v}; deeper architectures remain unvisited.")
                elif param == "learning_rate" and min_v >= 0.1:
                    hp_insights.append(f"learning_rate tested down to {min_v}; smaller rates (0.01, 0.05) with higher tree counts unprobed.")

        if not hp_insights:
            hp_insights.append("Standard parameter ranges explored across evaluated trials.")

        # G. Trend & Plateau detection
        plateau_detected = False
        improvement_trend = "Insufficient historical sequence for trend evaluation."
        stopping_advice = ""

        if total_completed >= 2:
            first_acc = completed_runs[0].result.accuracy
            latest_acc = completed_runs[-1].result.accuracy
            delta = latest_acc - first_acc
            if delta > 0.01:
                improvement_trend = f"Positive upward trajectory: +{delta*100:.2f}% accuracy improvement from initial baseline."
            elif delta < -0.01:
                improvement_trend = f"Regressive trend: {delta*100:.2f}% accuracy shift from initial baseline."
            else:
                improvement_trend = "Stable / horizontal trajectory: metric fluctuations remain bounded within minor tolerances."

            # Plateau condition check: if 3+ runs and recent metric gain < 0.005 (0.5%) or overall variance is extremely low
            if total_completed >= 3:
                last_two = [r.result.accuracy for r in completed_runs[-2:]]
                last_two_gain = max(last_two) - min(last_two)
                recent_accs = [r.result.accuracy for r in completed_runs[-3:]]
                recent_gain = max(recent_accs) - min(recent_accs)
                if last_two_gain < 0.005 or recent_gain < 0.005 or std_acc < 0.003:
                    plateau_detected = True
                    stopping_advice = (
                        "CRITICAL: Performance plateau detected. Recent runs demonstrate negligible variation (<0.5%). "
                        "Hyperparameter optimization has reached diminishing returns. Recommend concluding tuning and migrating focus to "
                        "dataset expansion, feature transformation, or sample balancing."
                    )

        return {
            "dataset_summary": dt_info,
            "run_counts": {"completed": total_completed, "failed": len(failed_runs), "in_progress": len(in_progress_runs)},
            "metrics_analysis": {
                "average_accuracy": round(avg_acc, 4),
                "best_accuracy": round(best_run_acc.result.accuracy, 4),
                "best_accuracy_run": f"Run #{best_run_acc.run_number} ({self._normalize_model_name(best_run_acc.model_type)})",
                "average_f1": round(avg_f1, 4),
                "best_f1": round(best_run_f1.result.f1_score, 4),
                "accuracy_variance": round(var_acc, 6),
                "accuracy_std_dev": round(std_acc, 4),
                "fastest_execution": fastest_model,
                "slowest_execution": slowest_model,
            },
            "configurations_tested": config_summaries,
            "failed_runs_history": failed_runs,
            "search_space": {
                "evaluated_model_families": sorted(list(evaluated_families)),
                "unexplored_model_families": unexplored_families,
                "untested_parameter_regions": hp_insights,
            },
            "trend_and_plateau_analysis": {
                "plateau_detected": plateau_detected,
                "improvement_trend": improvement_trend,
                "stopping_guidance": stopping_advice if plateau_detected else "Continued exploration is empirically justified.",
            }
        }

    def _to_response_schema(
        self,
        record: Any,
        data: dict[str, Any],
        *,
        is_cached: bool,
        evidence_summary: dict[str, Any] | None = None,
    ) -> ExperimentStrategyResponse:
        return ExperimentStrategyResponse(
            id=str(record.id),
            experiment_id=str(record.experiment_id),
            overall_assessment=str(data.get("overall_assessment", "No assessment generated.")),
            current_experiment_status=str(data.get("current_experiment_status", "Active")),
            observed_trends=data.get("observed_trends", []),
            strongest_model=str(data.get("strongest_model", "N/A")),
            most_stable_model=str(data.get("most_stable_model", "N/A")),
            what_has_been_learned=data.get("what_has_been_learned", []),
            remaining_search_space=data.get("remaining_search_space", []),
            recommended_next_experiment=data.get("recommended_next_experiment", "No further action recommended."),
            confidence=str(data.get("confidence", "Medium")),
            evidence_used=data.get("evidence_used", []),
            potential_risks=data.get("potential_risks", []),
            model_name=str(record.model_name),
            generated_at=record.created_at or datetime.now(timezone.utc),
            cached=is_cached,
            evidence_summary=evidence_summary,
        )
