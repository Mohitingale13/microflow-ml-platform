"""
dataset_ai_analysis_repository.py — Data access for DatasetAIAnalysis records.

Follows existing repository pattern:
  - Session-based
  - No business logic
  - Clean query and create methods
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.dataset_ai_analysis import DatasetAIAnalysis


class DatasetAIAnalysisRepository:

    def get_by_dataset_and_hash(
        self, dataset_id: str, prompt_hash: str, db: Session
    ) -> DatasetAIAnalysis | None:
        """Return a cached analysis for this exact (dataset_id, prompt_hash) pair."""
        return (
            db.query(DatasetAIAnalysis)
            .filter(
                DatasetAIAnalysis.dataset_id == dataset_id,
                DatasetAIAnalysis.prompt_hash == prompt_hash,
            )
            .first()
        )

    def get_latest_by_dataset(self, dataset_id: str, db: Session) -> DatasetAIAnalysis | None:
        """Return the most recent AI analysis for a dataset regardless of hash."""
        return (
            db.query(DatasetAIAnalysis)
            .filter(DatasetAIAnalysis.dataset_id == dataset_id)
            .order_by(DatasetAIAnalysis.created_at.desc())
            .first()
        )

    def create(
        self,
        db: Session,
        *,
        dataset_id: str,
        prompt_hash: str,
        model_name: str,
        analysis_json: str,
    ) -> DatasetAIAnalysis:
        record = DatasetAIAnalysis(
            dataset_id=dataset_id,
            prompt_hash=prompt_hash,
            model_name=model_name,
            analysis_json=analysis_json,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
