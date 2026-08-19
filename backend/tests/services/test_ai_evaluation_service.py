"""
test_ai_evaluation_service.py — Unit tests for AIEvaluationService retry and state handling.

Covers:
  1. successful evaluation -> completed
  2. first failure -> retry count increments and remains pending
  3. second failure -> remains pending
  4. third failure -> becomes failed
  5. failed record is excluded from subsequent batches
  6. failure of one record does not prevent other pending records from being evaluated
  7. successful retry after an earlier failure -> completed
  8. existing RAGAS scores remain correct
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.ai_query import AIQueryCache
from app.repositories.ai_query_repository import AIQueryRepository
from app.services.ai_evaluation_service import AIEvaluationService, MAX_EVALUATION_ATTEMPTS


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def query_repo():
    return AIQueryRepository()


@pytest.fixture
def mock_gemini():
    return MagicMock()


@pytest.fixture
def evaluation_service(query_repo, mock_gemini):
    return AIEvaluationService(query_repo=query_repo, gemini_service=mock_gemini)


def create_sample_query(
    db,
    query_repo,
    query_hash="hash_1",
    question="What is the best run?",
    answer="Run #1 achieved 0.95 accuracy.",
    supporting_data="Run 1 metrics: acc 0.95",
    evaluation_status="pending",
    evaluation_retries=0,
    evaluation_error=None,
    context_relevance_score=None,
    faithfulness_score=None,
    answer_relevance_score=None,
    evaluation_reasoning=None,
):
    return query_repo.create(
        db=db,
        query_hash=query_hash,
        question=question,
        intent="best_performing",
        filters_json="{}",
        model_name="gemini-3.6-flash",
        answer=answer,
        reasoning="Based on telemetry.",
        supporting_data=supporting_data,
        recommendation="Deploy model.",
        evaluation_status=evaluation_status,
        evaluation_retries=evaluation_retries,
        evaluation_error=evaluation_error,
    )


VALID_EVAL_JSON = json.dumps({
    "evaluation_reasoning": "Accurate grounding in telemetry.",
    "context_relevance_score": 0.95,
    "faithfulness_score": 0.98,
    "answer_relevance_score": 0.92,
})


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestAIEvaluationRetryAndState:

    def test_1_successful_evaluation_marks_completed(
        self, db_session, query_repo, mock_gemini, evaluation_service
    ):
        """1. successful evaluation -> completed"""
        record = create_sample_query(db_session, query_repo, query_hash="q1")
        mock_gemini.generate_evaluation.return_value = VALID_EVAL_JSON

        evaluated_count = evaluation_service.evaluate_batch(db=db_session, limit=10)

        assert evaluated_count == 1
        db_session.refresh(record)
        assert record.evaluation_status == "completed"
        assert record.evaluation_retries == 0
        assert record.evaluation_error is None
        assert record.context_relevance_score == 0.95
        assert record.faithfulness_score == 0.98
        assert record.answer_relevance_score == 0.92
        assert record.evaluation_reasoning == "Accurate grounding in telemetry."

    def test_2_first_failure_increments_retry_and_remains_pending(
        self, db_session, query_repo, mock_gemini, evaluation_service
    ):
        """2. first failure -> retry count increments and remains pending"""
        record = create_sample_query(db_session, query_repo, query_hash="q2")
        mock_gemini.generate_evaluation.side_effect = RuntimeError("API 503 Unavailable")

        evaluated_count = evaluation_service.evaluate_batch(db=db_session, limit=10)

        assert evaluated_count == 0
        db_session.refresh(record)
        assert record.evaluation_status == "pending"
        assert record.evaluation_retries == 1
        assert "API 503 Unavailable" in record.evaluation_error
        assert record.context_relevance_score is None

    def test_3_second_failure_remains_pending(
        self, db_session, query_repo, mock_gemini, evaluation_service
    ):
        """3. second failure -> remains pending"""
        record = create_sample_query(
            db_session,
            query_repo,
            query_hash="q3",
            evaluation_status="pending",
            evaluation_retries=1,
            evaluation_error="Previous error",
        )
        mock_gemini.generate_evaluation.side_effect = RuntimeError("API 429 Rate Limited")

        evaluated_count = evaluation_service.evaluate_batch(db=db_session, limit=10)

        assert evaluated_count == 0
        db_session.refresh(record)
        assert record.evaluation_status == "pending"
        assert record.evaluation_retries == 2
        assert "API 429 Rate Limited" in record.evaluation_error

    def test_4_third_failure_becomes_failed(
        self, db_session, query_repo, mock_gemini, evaluation_service
    ):
        """4. third failure -> becomes failed"""
        record = create_sample_query(
            db_session,
            query_repo,
            query_hash="q4",
            evaluation_status="pending",
            evaluation_retries=2,
            evaluation_error="Previous error 2",
        )
        mock_gemini.generate_evaluation.side_effect = ValueError("Invalid JSON response")

        evaluated_count = evaluation_service.evaluate_batch(db=db_session, limit=10)

        assert evaluated_count == 0
        db_session.refresh(record)
        assert record.evaluation_status == "failed"
        assert record.evaluation_retries == 3
        assert "Invalid JSON response" in record.evaluation_error

    def test_5_failed_record_excluded_from_subsequent_batches(
        self, db_session, query_repo, mock_gemini, evaluation_service
    ):
        """5. failed record is excluded from subsequent batches"""
        record = create_sample_query(
            db_session,
            query_repo,
            query_hash="q5",
            evaluation_status="failed",
            evaluation_retries=3,
            evaluation_error="Permanent error",
        )
        mock_gemini.generate_evaluation.return_value = VALID_EVAL_JSON

        evaluated_count = evaluation_service.evaluate_batch(db=db_session, limit=10)

        assert evaluated_count == 0
        mock_gemini.generate_evaluation.assert_not_called()
        db_session.refresh(record)
        assert record.evaluation_status == "failed"

    def test_6_failure_of_one_record_does_not_prevent_others(
        self, db_session, query_repo, mock_gemini, evaluation_service
    ):
        """6. failure of one record does not prevent other pending records from being evaluated"""
        rec_fail = create_sample_query(db_session, query_repo, query_hash="q6_fail")
        rec_succ = create_sample_query(db_session, query_repo, query_hash="q6_succ")

        # First call fails, second call succeeds
        mock_gemini.generate_evaluation.side_effect = [
            RuntimeError("Transient error"),
            VALID_EVAL_JSON,
        ]

        evaluated_count = evaluation_service.evaluate_batch(db=db_session, limit=10)

        assert evaluated_count == 1
        db_session.refresh(rec_fail)
        db_session.refresh(rec_succ)

        # Failed record was updated with error & retry count
        assert rec_fail.evaluation_status == "pending"
        assert rec_fail.evaluation_retries == 1
        assert "Transient error" in rec_fail.evaluation_error

        # Successful record was completed
        assert rec_succ.evaluation_status == "completed"
        assert rec_succ.evaluation_retries == 0
        assert rec_succ.evaluation_error is None
        assert rec_succ.context_relevance_score == 0.95

    def test_7_successful_retry_after_earlier_failure_marks_completed(
        self, db_session, query_repo, mock_gemini, evaluation_service
    ):
        """7. successful retry after an earlier failure -> completed"""
        record = create_sample_query(
            db_session,
            query_repo,
            query_hash="q7",
            evaluation_status="pending",
            evaluation_retries=2,
            evaluation_error="Old transient error",
        )
        mock_gemini.generate_evaluation.return_value = VALID_EVAL_JSON

        evaluated_count = evaluation_service.evaluate_batch(db=db_session, limit=10)

        assert evaluated_count == 1
        db_session.refresh(record)
        assert record.evaluation_status == "completed"
        # Error cleared on successful completion
        assert record.evaluation_error is None
        assert record.context_relevance_score == 0.95

    def test_8_existing_ragas_scores_remain_correct(
        self, db_session, query_repo, mock_gemini, evaluation_service
    ):
        """8. existing RAGAS scores remain correct"""
        record = create_sample_query(
            db_session,
            query_repo,
            query_hash="q8",
            evaluation_status="completed",
            evaluation_retries=0,
            context_relevance_score=0.88,
            faithfulness_score=0.91,
            answer_relevance_score=0.85,
            evaluation_reasoning="Prior successful evaluation.",
        )
        # Manually set scores and commit to emulate pre-existing evaluated record
        record.context_relevance_score = 0.88
        record.faithfulness_score = 0.91
        record.answer_relevance_score = 0.85
        record.evaluation_reasoning = "Prior successful evaluation."
        db_session.add(record)
        db_session.commit()

        # Batch run should find 0 unevaluated items
        evaluated_count = evaluation_service.evaluate_batch(db=db_session, limit=10)
        assert evaluated_count == 0
        mock_gemini.generate_evaluation.assert_not_called()

        db_session.refresh(record)
        assert record.context_relevance_score == 0.88
        assert record.faithfulness_score == 0.91
        assert record.answer_relevance_score == 0.85
        assert record.evaluation_reasoning == "Prior successful evaluation."
        assert record.evaluation_status == "completed"
