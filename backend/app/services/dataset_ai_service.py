"""
dataset_ai_service.py — Core business logic for AI Dataset Intelligence.

Orchestrates:
  1. Validating dataset readiness and schema completeness.
  2. Retrieving column statistics and preview rows via DatasetService (no SQL by Gemini).
  3. Deterministically computing Dataset Quality Score (0–100) and qualitative label.
  4. Prompt hashing via compute_prompt_hash and looking up cached analysis in DB.
  5. Generating fresh insights from Gemini if uncached, verifying and caching the report.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.cache_service import compute_prompt_hash
from app.ai.gemini_service import GeminiService
from app.ai.prompt_builder import build_dataset_analysis_prompt
from app.ai.response_parser import parse_dataset_analysis_response
from app.ai.schemas import DatasetAIAnalysisResponse
from app.models.dataset import DatasetStatus
from app.repositories.dataset_ai_analysis_repository import DatasetAIAnalysisRepository
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService

logger = logging.getLogger(__name__)


class DatasetAIService:
    def __init__(
        self,
        dataset_repo: DatasetRepository,
        analysis_repo: DatasetAIAnalysisRepository,
        gemini_service: GeminiService,
        dataset_service: DatasetService,
    ) -> None:
        self._dataset_repo = dataset_repo
        self._analysis_repo = analysis_repo
        self._gemini_service = gemini_service
        self._dataset_service = dataset_service

    def get_or_generate_analysis(
        self, dataset_id: str, db: Session
    ) -> DatasetAIAnalysisResponse:
        """
        Return cached AI Dataset Intelligence report if available; otherwise generate,
        verify, cache, and return fresh analysis.
        """
        dataset = self._dataset_repo.get_by_id(dataset_id, db)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset '{dataset_id}' not found.",
            )

        if dataset.status != DatasetStatus.ready:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset analysis requires status 'ready', but current status is '{dataset.status.value}'.",
            )

        row_count = dataset.row_count or 0
        col_count = dataset.column_count or 0
        if row_count == 0 or col_count == 0 or not dataset.column_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset is empty or missing schema metadata. AI intelligence analysis cannot be performed.",
            )

        # Retrieve statistics and preview without letting Gemini touch SQL or files directly
        try:
            stats = self._dataset_service.get_statistics(dataset_id, db)
            preview_data = self._dataset_service.get_preview(dataset_id, db)
            preview_rows: list[dict[str, Any]] = preview_data.get("rows", [])
        except Exception as exc:
            logger.error("Failed to retrieve dataset preview or statistics for %s: %s", dataset_id, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not read dataset statistics or sample rows from disk.",
            ) from exc

        # Deterministic quality scoring in pure Python
        score, label = self._calculate_quality_score(dataset, row_count, col_count)

        # Build deterministic prompt & compute cache key
        prompt = build_dataset_analysis_prompt(dataset, stats, preview_rows, score, label)
        p_hash = compute_prompt_hash(prompt)

        # Check PostgreSQL cache layer first
        cached = self._analysis_repo.get_by_dataset_and_hash(dataset_id, p_hash, db)
        if cached:
            try:
                data_map = json.loads(cached.analysis_json)
                return self._to_response_schema(cached, data_map, is_cached=True)
            except Exception as exc:
                logger.warning("Cached analysis JSON was malformed for dataset %s: %s. Regenerating.", dataset_id, exc)

        # Generate via Gemini SDK
        try:
            raw_text = self._gemini_service.generate_dataset_analysis(prompt)
            parsed = parse_dataset_analysis_response(raw_text)
        except Exception as exc:
            logger.error("Gemini dataset analysis API call or parsing failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI dataset intelligence analysis failed: {exc}",
            ) from exc

        # Force deterministic quality verification so Gemini never hallucinates arbitrary numbers
        explanation = "Evaluated via missing value ratios, sample sizing, and feature completeness."
        q_field = parsed.get("dataset_quality")
        if isinstance(q_field, dict) and "explanation" in q_field:
            explanation = str(q_field["explanation"])
        elif isinstance(q_field, str) and len(q_field.strip()) > 0:
            explanation = q_field.strip()

        parsed["dataset_quality"] = {
            "score": score,
            "label": label,
            "explanation": explanation,
        }

        # Save verified analysis to database cache
        record = self._analysis_repo.create(
            db=db,
            dataset_id=dataset_id,
            prompt_hash=p_hash,
            model_name=self._gemini_service.model_name,
            analysis_json=json.dumps(parsed),
        )
        logger.info("Created and cached AI dataset intelligence analysis for dataset %s", dataset_id)

        try:
            from app.services.embedding_service import EmbeddingService
            EmbeddingService(gemini_service=self._gemini_service).index_dataset_analysis(db, record, dataset)
        except Exception as exc:
            logger.warning("Embedding indexing failed for Dataset Analysis %s: %s", record.id, exc)

        return self._to_response_schema(record, parsed, is_cached=False)

    def _calculate_quality_score(
        self, dataset: Any, row_count: int, col_count: int
    ) -> tuple[int, str]:
        """
        Calculate deterministic quality score 0-100 based on missing values, size, and dimensions.
        Returns (score, label).
        """
        score = 100

        # Missing value ratio penalty (up to 40 points)
        total_missing = sum(int(v) for v in (dataset.missing_values or {}).values() if str(v).isdigit())
        total_cells = max(1, row_count * col_count)
        missing_ratio = total_missing / total_cells
        missing_penalty = min(40, int(missing_ratio * 100 * 2))
        score -= missing_penalty

        # Dataset volume adequacy penalty (up to 25 points)
        if row_count < 20:
            score -= 25
        elif row_count < 100:
            score -= 15
        elif row_count < 250:
            score -= 5

        # Dimensionality completeness penalty (up to 15 points)
        if col_count < 2:
            score -= 20
        elif col_count < 4:
            score -= 10

        score = max(0, min(100, score))

        if score >= 85:
            label = "Excellent"
        elif score >= 70:
            label = "Good"
        elif score >= 50:
            label = "Fair"
        else:
            label = "Poor"

        return score, label

    def _to_response_schema(
        self, record: Any, parsed: dict[str, Any], is_cached: bool
    ) -> DatasetAIAnalysisResponse:
        return DatasetAIAnalysisResponse(
            id=record.id,
            dataset_id=record.dataset_id,
            overall_summary=str(parsed.get("overall_summary", "")),
            recommended_target=str(parsed.get("recommended_target", "")),
            dataset_quality=parsed.get("dataset_quality", {}),
            strengths=parsed.get("strengths", []),
            potential_issues=parsed.get("potential_issues", []),
            recommended_preprocessing=parsed.get("recommended_preprocessing", []),
            recommended_models=parsed.get("recommended_models", []),
            feature_observations=parsed.get("feature_observations", []),
            risk_assessment=str(parsed.get("risk_assessment", "")),
            next_steps=parsed.get("next_steps", []),
            model_name=record.model_name,
            generated_at=record.created_at,
            cached=is_cached,
        )
