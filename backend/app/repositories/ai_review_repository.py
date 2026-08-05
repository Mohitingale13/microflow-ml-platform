"""
ai_review_repository.py — Data access for RunAIReview records.

Follows the same pattern as run_result_repository.py:
  - Session-based
  - No business logic
  - Methods are narrowly scoped
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.ai_review import RunAIReview


class AIReviewRepository:

    def get_by_run_and_hash(
        self, run_id: str, prompt_hash: str, db: Session
    ) -> RunAIReview | None:
        """Return a cached review for this exact (run, prompt_hash) pair."""
        return (
            db.query(RunAIReview)
            .filter(
                RunAIReview.run_id == run_id,
                RunAIReview.prompt_hash == prompt_hash,
            )
            .first()
        )

    def get_latest_by_run(self, run_id: str, db: Session) -> RunAIReview | None:
        """Return the most recent review for a run regardless of prompt hash."""
        return (
            db.query(RunAIReview)
            .filter(RunAIReview.run_id == run_id)
            .order_by(RunAIReview.created_at.desc())
            .first()
        )

    def create(
        self,
        db: Session,
        *,
        run_id: str,
        prompt_hash: str,
        model_name: str,
        review_text: str,
        overall_assessment: str,
        strengths: str,
        weaknesses: str,
        comparison: str,
        recommendation: str,
    ) -> RunAIReview:
        record = RunAIReview(
            run_id=run_id,
            prompt_hash=prompt_hash,
            model_name=model_name,
            review_text=review_text,
            overall_assessment=overall_assessment,
            strengths=strengths,
            weaknesses=weaknesses,
            comparison=comparison,
            recommendation=recommendation,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
