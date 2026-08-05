"""
test_ai_review.py — Comprehensive test suite for Milestone AI-1.

Covers:
  - CacheService: hash determinism and consistency
  - ResponseParser: valid JSON, fenced JSON, missing fields, empty fields
  - PromptBuilder: output contains expected context strings
  - AIReviewRepository: create and cache-hit retrieval (SQLite in-memory)
  - AIReviewService: cache-hit path, fresh-generate path (Gemini mocked)
  - Router: 200 (cached), 200 (fresh), 404 (unknown run), 422 (non-completed run)

Gemini is never called — all external API calls are mocked via unittest.mock.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.cache_service import compute_prompt_hash
from app.ai.response_parser import parse_gemini_response
from app.ai.schemas import AIReviewContent
from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models.ai_review import RunAIReview
from app.models.artifact import ArtifactType, RunResult
from app.models.dataset import Dataset
from app.models.experiment import Experiment, ExperimentStatus, Run, RunStatus
from app.repositories.ai_review_repository import AIReviewRepository


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
def test_client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _make_dataset(db) -> Dataset:
    d = Dataset(
        id=str(uuid.uuid4()),
        name="test-dataset",
        original_filename="test.csv",
        file_hash=str(uuid.uuid4()),
        file_size_bytes=1024,
        storage_path="/tmp/test.csv",
        row_count=500,
        column_count=12,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def _make_experiment(db, dataset_id: str) -> Experiment:
    e = Experiment(
        id=str(uuid.uuid4()),
        name="Test Experiment",
        dataset_id=dataset_id,
        objective="Predict disease outcome",
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


def _make_run(db, experiment_id: str, status: RunStatus = RunStatus.completed) -> Run:
    r = Run(
        id=str(uuid.uuid4()),
        experiment_id=experiment_id,
        run_number=1,
        model_type="random_forest",
        training_configuration={"n_estimators": 100, "max_depth": 5},
        status=status,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _make_run_result(db, run_id: str) -> RunResult:
    rr = RunResult(
        id=str(uuid.uuid4()),
        run_id=run_id,
        accuracy=0.91,
        precision=0.89,
        recall=0.90,
        f1_score=0.895,
        roc_auc=0.95,
        confusion_matrix=[[45, 5], [4, 46]],
        execution_time_seconds=3.2,
        model_type="random_forest",
    )
    db.add(rr)
    db.commit()
    db.refresh(rr)
    return rr


# ─── CacheService Tests ────────────────────────────────────────────────────────

class TestCacheService:
    def test_hash_is_deterministic(self):
        prompt = "This is a test prompt for AI review."
        assert compute_prompt_hash(prompt) == compute_prompt_hash(prompt)

    def test_different_prompts_produce_different_hashes(self):
        h1 = compute_prompt_hash("prompt A")
        h2 = compute_prompt_hash("prompt B")
        assert h1 != h2

    def test_hash_is_64_chars(self):
        h = compute_prompt_hash("any prompt")
        assert len(h) == 64

    def test_hash_is_hex(self):
        h = compute_prompt_hash("any prompt")
        int(h, 16)  # raises ValueError if not valid hex


# ─── ResponseParser Tests ─────────────────────────────────────────────────────

VALID_JSON_RESPONSE = """{
  "overall_assessment": "The run achieved 91% accuracy, representing strong performance.",
  "strengths": "ROC AUC of 0.95 indicates excellent class discrimination.",
  "weaknesses": "Precision-recall balance is slightly skewed. Recall could be improved.",
  "comparison": "This is the best run in the experiment by accuracy margin.",
  "recommendation": "Increase max_depth to 7 and re-run to test depth sensitivity."
}"""

FENCED_JSON_RESPONSE = f"```json\n{VALID_JSON_RESPONSE}\n```"

FENCED_NO_LANG_RESPONSE = f"```\n{VALID_JSON_RESPONSE}\n```"


class TestResponseParser:
    def test_valid_json_parsed_correctly(self):
        result = parse_gemini_response(VALID_JSON_RESPONSE)
        assert isinstance(result, AIReviewContent)
        assert "91%" in result.overall_assessment

    def test_fenced_json_is_stripped_and_parsed(self):
        result = parse_gemini_response(FENCED_JSON_RESPONSE)
        assert isinstance(result, AIReviewContent)

    def test_fenced_no_lang_json_is_parsed(self):
        result = parse_gemini_response(FENCED_NO_LANG_RESPONSE)
        assert isinstance(result, AIReviewContent)

    def test_missing_field_raises_value_error(self):
        broken = '{"overall_assessment": "ok", "strengths": "good"}'
        with pytest.raises(ValueError, match="missing required fields"):
            parse_gemini_response(broken)

    def test_empty_field_raises_value_error(self):
        bad = """{
          "overall_assessment": "",
          "strengths": "good",
          "weaknesses": "some",
          "comparison": "better",
          "recommendation": "try x"
        }"""
        with pytest.raises(ValueError, match="non-empty string"):
            parse_gemini_response(bad)

    def test_non_json_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_gemini_response("This is not JSON at all.")

    def test_all_five_fields_present(self):
        result = parse_gemini_response(VALID_JSON_RESPONSE)
        assert result.overall_assessment
        assert result.strengths
        assert result.weaknesses
        assert result.comparison
        assert result.recommendation


# ─── PromptBuilder Tests ──────────────────────────────────────────────────────

class TestPromptBuilder:
    def test_prompt_contains_experiment_name(self):
        from app.ai.prompt_builder import build_review_prompt

        run = SimpleNamespace(
            run_number=1,
            model_type="random_forest",
            training_configuration={"n_estimators": 100},
            id="run-1",
        )
        experiment = SimpleNamespace(
            name="My Experiment",
            objective="Predict something",
            dataset_id="ds-1",
        )
        dataset = SimpleNamespace(
            name="mydata",
            row_count=500,
            column_count=10,
        )
        run_result = SimpleNamespace(
            accuracy=0.91,
            precision=0.89,
            recall=0.90,
            f1_score=0.895,
            roc_auc=0.95,
            execution_time_seconds=3.2,
        )

        prompt = build_review_prompt(
            run=run,
            experiment=experiment,
            dataset=dataset,
            run_result=run_result,
            best_run=None,
            best_result=None,
        )

        assert "My Experiment" in prompt
        assert "random_forest" in prompt
        assert "0.9100" in prompt
        assert "JSON" in prompt

    def test_prompt_handles_missing_dataset(self):
        from app.ai.prompt_builder import build_review_prompt

        run = SimpleNamespace(
            run_number=1, model_type="xgboost",
            training_configuration=None, id="r1",
        )
        experiment = SimpleNamespace(
            name="X", objective=None, dataset_id=None,
        )
        run_result = SimpleNamespace(
            accuracy=0.8, precision=0.78, recall=0.79, f1_score=0.785,
            roc_auc=None, execution_time_seconds=None,
        )

        prompt = build_review_prompt(
            run=run, experiment=experiment, dataset=None,
            run_result=run_result, best_run=None, best_result=None,
        )
        assert "N/A" in prompt


# ─── AIReviewRepository Tests ─────────────────────────────────────────────────

class TestAIReviewRepository:
    def test_create_and_retrieve_by_hash(self, db_session):
        dataset = _make_dataset(db_session)
        experiment = _make_experiment(db_session, dataset.id)
        run = _make_run(db_session, experiment.id)

        repo = AIReviewRepository()
        record = repo.create(
            db_session,
            run_id=run.id,
            prompt_hash="abc123",
            model_name="gemini-2.5-flash",
            review_text='{"overall_assessment": "test"}',
            overall_assessment="The run performed well.",
            strengths="High accuracy.",
            weaknesses="Low recall.",
            comparison="Best in experiment.",
            recommendation="Try deeper trees.",
        )

        assert record.id is not None
        assert record.run_id == run.id

        cached = repo.get_by_run_and_hash(run.id, "abc123", db_session)
        assert cached is not None
        assert cached.id == record.id

    def test_cache_miss_returns_none(self, db_session):
        repo = AIReviewRepository()
        result = repo.get_by_run_and_hash("nonexistent", "fakehash", db_session)
        assert result is None

    def test_get_latest_by_run(self, db_session):
        dataset = _make_dataset(db_session)
        experiment = _make_experiment(db_session, dataset.id)
        run = _make_run(db_session, experiment.id)

        repo = AIReviewRepository()
        repo.create(
            db_session, run_id=run.id, prompt_hash="hash1",
            model_name="gemini-2.5-flash", review_text="{}",
            overall_assessment="ok", strengths="ok",
            weaknesses="ok", comparison="ok", recommendation="ok",
        )

        latest = repo.get_latest_by_run(run.id, db_session)
        assert latest is not None
        assert latest.run_id == run.id


# ─── AIReviewService Tests (Gemini mocked) ───────────────────────────────────

class TestAIReviewService:
    def _make_service(self, db, gemini_mock=None):
        from app.services.ai_review_service import AIReviewService
        from app.repositories.run_repository import RunRepository
        from app.repositories.experiment_repository import ExperimentRepository
        from app.repositories.run_result_repository import RunResultRepository
        from app.repositories.dataset_repository import DatasetRepository

        if gemini_mock is None:
            gemini_mock = MagicMock()
            gemini_mock.generate_review.return_value = VALID_JSON_RESPONSE
            gemini_mock.model_name = "gemini-2.5-flash"

        return AIReviewService(
            run_repo=RunRepository(),
            experiment_repo=ExperimentRepository(),
            run_result_repo=RunResultRepository(),
            dataset_repo=DatasetRepository(),
            ai_review_repo=AIReviewRepository(),
            gemini_service=gemini_mock,
        )

    def test_generates_review_for_completed_run(self, db_session):
        dataset = _make_dataset(db_session)
        experiment = _make_experiment(db_session, dataset.id)
        run = _make_run(db_session, experiment.id, RunStatus.completed)
        _make_run_result(db_session, run.id)

        service = self._make_service(db_session)
        response = service.get_or_generate_review(run.id, db_session)

        assert response.run_id == run.id
        assert response.cached is False
        assert response.overall_assessment

    def test_returns_cached_on_second_call(self, db_session):
        dataset = _make_dataset(db_session)
        experiment = _make_experiment(db_session, dataset.id)
        run = _make_run(db_session, experiment.id, RunStatus.completed)
        _make_run_result(db_session, run.id)

        gemini_mock = MagicMock()
        gemini_mock.generate_review.return_value = VALID_JSON_RESPONSE
        gemini_mock.model_name = "gemini-2.5-flash"
        service = self._make_service(db_session, gemini_mock)

        service.get_or_generate_review(run.id, db_session)
        response2 = service.get_or_generate_review(run.id, db_session)

        assert response2.cached is True
        # Gemini should only be called once
        assert gemini_mock.generate_review.call_count == 1

    def test_raises_404_for_unknown_run(self, db_session):
        from fastapi import HTTPException
        service = self._make_service(db_session)
        with pytest.raises(HTTPException) as exc_info:
            service.get_or_generate_review("nonexistent-run-id", db_session)
        assert exc_info.value.status_code == 404

    def test_raises_422_for_non_completed_run(self, db_session):
        from fastapi import HTTPException
        dataset = _make_dataset(db_session)
        experiment = _make_experiment(db_session, dataset.id)
        run = _make_run(db_session, experiment.id, RunStatus.draft)

        service = self._make_service(db_session)
        with pytest.raises(HTTPException) as exc_info:
            service.get_or_generate_review(run.id, db_session)
        assert exc_info.value.status_code == 422


# ─── Router Integration Tests ─────────────────────────────────────────────────

class TestAIReviewRouter:
    def _seed(self, db_session):
        dataset = _make_dataset(db_session)
        experiment = _make_experiment(db_session, dataset.id)
        run = _make_run(db_session, experiment.id, RunStatus.completed)
        _make_run_result(db_session, run.id)
        return run

    def _override_service(self, test_client, db_session, gemini_mock):
        from app.routers.ai import get_ai_review_service
        from app.services.ai_review_service import AIReviewService
        from app.repositories.run_repository import RunRepository
        from app.repositories.experiment_repository import ExperimentRepository
        from app.repositories.run_result_repository import RunResultRepository
        from app.repositories.dataset_repository import DatasetRepository

        def _service():
            return AIReviewService(
                run_repo=RunRepository(),
                experiment_repo=ExperimentRepository(),
                run_result_repo=RunResultRepository(),
                dataset_repo=DatasetRepository(),
                ai_review_repo=AIReviewRepository(),
                gemini_service=gemini_mock,
            )

        app.dependency_overrides[get_ai_review_service] = _service

    def test_review_endpoint_returns_200(self, test_client, db_session):
        run = self._seed(db_session)

        gemini_mock = MagicMock()
        gemini_mock.generate_review.return_value = VALID_JSON_RESPONSE
        gemini_mock.model_name = "gemini-2.5-flash"
        self._override_service(test_client, db_session, gemini_mock)

        response = test_client.post(f"/api/v1/runs/{run.id}/review")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "overall_assessment" in body["data"]
        assert body["data"]["cached"] is False

        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = lambda: db_session  # restore db override

    def test_review_endpoint_cached_on_second_call(self, test_client, db_session):
        run = self._seed(db_session)

        gemini_mock = MagicMock()
        gemini_mock.generate_review.return_value = VALID_JSON_RESPONSE
        gemini_mock.model_name = "gemini-2.5-flash"
        self._override_service(test_client, db_session, gemini_mock)

        test_client.post(f"/api/v1/runs/{run.id}/review")
        r2 = test_client.post(f"/api/v1/runs/{run.id}/review")
        assert r2.json()["data"]["cached"] is True
        assert gemini_mock.generate_review.call_count == 1

        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = lambda: db_session

    def test_404_for_unknown_run(self, test_client, db_session):
        gemini_mock = MagicMock()
        gemini_mock.model_name = "gemini-2.5-flash"
        self._override_service(test_client, db_session, gemini_mock)

        response = test_client.post("/api/v1/runs/does-not-exist/review")
        assert response.status_code == 404

        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = lambda: db_session

    def test_422_for_non_completed_run(self, test_client, db_session):
        dataset = _make_dataset(db_session)
        experiment = _make_experiment(db_session, dataset.id)
        queued_run = _make_run(db_session, experiment.id, RunStatus.queued)

        gemini_mock = MagicMock()
        gemini_mock.model_name = "gemini-2.5-flash"
        self._override_service(test_client, db_session, gemini_mock)

        response = test_client.post(f"/api/v1/runs/{queued_run.id}/review")
        assert response.status_code == 422

        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = lambda: db_session
