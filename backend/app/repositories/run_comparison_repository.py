"""
run_comparison_repository.py — Data access for RunAIComparison records.

Follows the exact same pattern as ai_review_repository.py:
  - Session-based
  - No business logic
  - Methods are narrowly scoped
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.run_comparison import RunAIComparison


class RunComparisonRepository:

    def get_by_pair_and_hash(
        self,
        run_a_id: str,
        run_b_id: str,
        prompt_hash: str,
        db: Session,
    ) -> RunAIComparison | None:
        """Return a cached comparison for this exact (run_a, run_b, prompt_hash) triple."""
        return (
            db.query(RunAIComparison)
            .filter(
                RunAIComparison.run_a_id == run_a_id,
                RunAIComparison.run_b_id == run_b_id,
                RunAIComparison.prompt_hash == prompt_hash,
            )
            .first()
        )

    def get_latest_by_pair(
        self,
        run_a_id: str,
        run_b_id: str,
        db: Session,
    ) -> RunAIComparison | None:
        """Return the most recent comparison for a run pair regardless of prompt hash."""
        return (
            db.query(RunAIComparison)
            .filter(
                RunAIComparison.run_a_id == run_a_id,
                RunAIComparison.run_b_id == run_b_id,
            )
            .order_by(RunAIComparison.created_at.desc())
            .first()
        )

    def create(
        self,
        db: Session,
        *,
        run_a_id: str,
        run_b_id: str,
        prompt_hash: str,
        model_name: str,
        overall_summary: str,
        better_run: str,
        key_improvements: str,
        tradeoffs: str,
        configuration_analysis: str,
        next_recommendation: str,
    ) -> RunAIComparison:
        record = RunAIComparison(
            run_a_id=run_a_id,
            run_b_id=run_b_id,
            prompt_hash=prompt_hash,
            model_name=model_name,
            overall_summary=overall_summary,
            better_run=better_run,
            key_improvements=key_improvements,
            tradeoffs=tradeoffs,
            configuration_analysis=configuration_analysis,
            next_recommendation=next_recommendation,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
