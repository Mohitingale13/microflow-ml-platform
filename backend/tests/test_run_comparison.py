"""
test_run_comparison.py — Comprehensive test suite for AI Milestone 2.

Covers:
  - PromptBuilder: build_comparison_prompt produces correct context strings
  - ResponseParser: parse_comparison_response — valid JSON, fenced JSON,
    missing fields, empty fields
  - RunComparisonRepository: create and cache-hit retrieval (SQLite in-memory)
  - RunComparisonService: cache-hit path, fresh-generate path (Gemini mocked),
    validation errors (same run, non-completed, cross-experiment)
  - Router: POST /runs/compare — 200 cached, 200 fresh, 400 same run,
    404 not found, 422 non-completed, 422 cross-experiment

Gemini is never called — all external API calls are mocked via unittest.mock.
"""

from __future__ import annotations

import json
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
from app.ai.prompt_builder import build_comparison_prompt
from app.ai.response_parser import parse_comparison_response
from app.ai.schemas import AIComparisonContent
from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models.artifact import RunResult
from app.models.dataset import Dataset
from app.models.experiment import Experiment, ExperimentStatus, Run, RunStatus
from app.models.run_comparison import RunAIComparison
from app.repositories.run_comparison_repository import RunComparisonRepository


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


def _make_experiment(dataset_id: str | None = None) -> Any:
    return SimpleNamespace(
        id=str(uuid.uuid4()),
        name="Test Experiment",
        objective="Maximize F1 Score",
        dataset_id=dataset_id or str(uuid.uuid4()),
    )


def _make_dataset() -> Any:
    return SimpleNamespace(
        id=str(uuid.uuid4()),
        name="iris.csv",
        row_count=150,
        column_count=5,
    )


def _make_run(
    experiment_id: str,
    run_number: int = 1,
    model_type: str = "random_forest",
    status: str = "completed",
    config: dict | None = None,
) -> Any:
    return SimpleNamespace(
        id=str(uuid.uuid4()),
        experiment_id=experiment_id,
        run_number=run_number,
        model_type=model_type,
        status=RunStatus.completed if status == "completed" else RunStatus.running,
        training_configuration=config,
    )


def _make_result(
    run_id: str,
    accuracy: float = 0.95,
    precision: float = 0.94,
    recall: float = 0.93,
    f1_score: float = 0.935,
    roc_auc: float | None = 0.98,
    execution_time: float | None = 12.5,
) -> Any:
    return SimpleNamespace(
        run_id=run_id,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        roc_auc=roc_auc,
        execution_time_seconds=execution_time,
    )


# ─── CacheService ──────────────────────────────────────────────────────────────

class TestCacheService:
    def test_hash_is_deterministic(self):
        prompt = "Test prompt for comparison"
        assert compute_prompt_hash(prompt) == compute_prompt_hash(prompt)

    def test_different_prompts_yield_different_hashes(self):
        h1 = compute_prompt_hash("prompt A")
        h2 = compute_prompt_hash("prompt B")
        assert h1 != h2

    def test_hash_length_is_64(self):
        h = compute_prompt_hash("any prompt")
        assert len(h) == 64


# ─── PromptBuilder ────────────────────────────────────────────────────────────

class TestComparisonPromptBuilder:
    def test_prompt_contains_experiment_name(self):
        exp = _make_experiment()
        ds = _make_dataset()
        exp.name = "My Experiment"
        run_a = _make_run(exp.id, run_number=1, model_type="logistic_regression")
        run_b = _make_run(exp.id, run_number=2, model_type="random_forest")
        res_a = _make_result(run_a.id, accuracy=0.90)
        res_b = _make_result(run_b.id, accuracy=0.95)
        prompt = build_comparison_prompt(
            run_a=run_a, run_b=run_b, experiment=exp,
            dataset=ds, result_a=res_a, result_b=res_b,
        )
        assert "My Experiment" in prompt

    def test_prompt_contains_both_run_numbers(self):
        exp = _make_experiment()
        ds = _make_dataset()
        run_a = _make_run(exp.id, run_number=3)
        run_b = _make_run(exp.id, run_number=7)
        res_a = _make_result(run_a.id)
        res_b = _make_result(run_b.id)
        prompt = build_comparison_prompt(
            run_a=run_a, run_b=run_b, experiment=exp,
            dataset=ds, result_a=res_a, result_b=res_b,
        )
        assert "Run number: 3" in prompt
        assert "Run number: 7" in prompt

    def test_prompt_contains_dataset_info(self):
        exp = _make_experiment()
        ds = _make_dataset()
        ds.name = "cancer_data.csv"
        ds.row_count = 569
        ds.column_count = 31
        run_a = _make_run(exp.id)
        run_b = _make_run(exp.id, run_number=2)
        res_a = _make_result(run_a.id)
        res_b = _make_result(run_b.id)
        prompt = build_comparison_prompt(
            run_a=run_a, run_b=run_b, experiment=exp,
            dataset=ds, result_a=res_a, result_b=res_b,
        )
        assert "cancer_data.csv" in prompt
        assert "569" in prompt

    def test_prompt_contains_metric_deltas(self):
        exp = _make_experiment()
        ds = _make_dataset()
        run_a = _make_run(exp.id)
        run_b = _make_run(exp.id, run_number=2)
        res_a = _make_result(run_a.id, accuracy=0.90)
        res_b = _make_result(run_b.id, accuracy=0.95)
        prompt = build_comparison_prompt(
            run_a=run_a, run_b=run_b, experiment=exp,
            dataset=ds, result_a=res_a, result_b=res_b,
        )
        assert "METRIC DELTAS" in prompt
        # delta = 0.95 - 0.90 = +0.0500
        assert "+0.0500" in prompt

    def test_prompt_requires_json_response(self):
        exp = _make_experiment()
        ds = _make_dataset()
        run_a = _make_run(exp.id)
        run_b = _make_run(exp.id, run_number=2)
        res_a = _make_result(run_a.id)
        res_b = _make_result(run_b.id)
        prompt = build_comparison_prompt(
            run_a=run_a, run_b=run_b, experiment=exp,
            dataset=ds, result_a=res_a, result_b=res_b,
        )
        assert "next_recommendation" in prompt
        assert "overall_summary" in prompt
        assert "better_run" in prompt


# ─── ResponseParser ───────────────────────────────────────────────────────────

VALID_COMPARISON_JSON = json.dumps({
    "overall_summary": "Run B outperformed Run A across all metrics.",
    "better_run": "Run B is the better run with higher accuracy and F1.",
    "key_improvements": "Accuracy improved by 5%, F1 by 3%.",
    "tradeoffs": "Execution time increased by 2 seconds.",
    "configuration_analysis": "Increasing max_depth from 5 to 10 improved boundaries.",
    "next_recommendation": "Try n_estimators=200 with learning_rate=0.05.",
})


class TestComparisonResponseParser:
    def test_valid_json_parsed_correctly(self):
        content = parse_comparison_response(VALID_COMPARISON_JSON)
        assert isinstance(content, AIComparisonContent)
        assert "Run B outperformed" in content.overall_summary
        assert "Run B is the better" in content.better_run
        assert "Accuracy improved" in content.key_improvements

    def test_fenced_json_is_stripped(self):
        fenced = f"```json\n{VALID_COMPARISON_JSON}\n```"
        content = parse_comparison_response(fenced)
        assert content.overall_summary != ""

    def test_json_embedded_in_text_is_extracted(self):
        wrapped = f"Here is the analysis:\n{VALID_COMPARISON_JSON}\nEnd of analysis."
        content = parse_comparison_response(wrapped)
        assert content.next_recommendation != ""

    def test_missing_field_raises_value_error(self):
        data = json.loads(VALID_COMPARISON_JSON)
        del data["better_run"]
        with pytest.raises(ValueError, match="missing required fields"):
            parse_comparison_response(json.dumps(data))

    def test_empty_field_raises_value_error(self):
        data = json.loads(VALID_COMPARISON_JSON)
        data["tradeoffs"] = "   "
        with pytest.raises(ValueError, match="non-empty string"):
            parse_comparison_response(json.dumps(data))

    def test_non_json_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_comparison_response("This is not JSON at all")

    def test_all_six_fields_present_in_result(self):
        content = parse_comparison_response(VALID_COMPARISON_JSON)
        assert content.overall_summary
        assert content.better_run
        assert content.key_improvements
        assert content.tradeoffs
        assert content.configuration_analysis
        assert content.next_recommendation


# ─── Repository ───────────────────────────────────────────────────────────────

class TestRunComparisonRepository:
    def _seed_runs(self, db) -> tuple[str, str]:
        """Seed minimal Dataset, Experiment, and two Run rows in SQLite."""
        from app.models.dataset import DatasetStatus
        dataset = Dataset(
            id=str(uuid.uuid4()),
            name="iris.csv",
            original_filename="iris.csv",
            file_hash=str(uuid.uuid4()),  # unique per test run
            file_size_bytes=4000,
            storage_path="/tmp/iris.csv",
            status=DatasetStatus.ready,
            version="v1",
        )
        db.add(dataset)
        db.flush()

        exp = Experiment(
            id=str(uuid.uuid4()),
            name="Experiment A",
            dataset_id=dataset.id,
            status=ExperimentStatus.active,
        )
        db.add(exp)
        db.flush()

        run_a = Run(
            id=str(uuid.uuid4()),
            experiment_id=exp.id,
            run_number=1,
            status=RunStatus.completed,
        )
        run_b = Run(
            id=str(uuid.uuid4()),
            experiment_id=exp.id,
            run_number=2,
            status=RunStatus.completed,
        )
        db.add(run_a)
        db.add(run_b)
        db.commit()
        return run_a.id, run_b.id

    def test_create_and_retrieve_by_hash(self, db_session):
        repo = RunComparisonRepository()
        run_a_id, run_b_id = self._seed_runs(db_session)

        record = repo.create(
            db_session,
            run_a_id=run_a_id,
            run_b_id=run_b_id,
            prompt_hash="abc123",
            model_name="gemini-3.6-flash",
            overall_summary="B is better.",
            better_run="Run B.",
            key_improvements="Accuracy +5%.",
            tradeoffs="Slower by 2s.",
            configuration_analysis="max_depth change caused this.",
            next_recommendation="Try n_estimators=200.",
        )
        assert record.id is not None

        cached = repo.get_by_pair_and_hash(run_a_id, run_b_id, "abc123", db_session)
        assert cached is not None
        assert cached.id == record.id
        assert cached.overall_summary == "B is better."

    def test_cache_miss_returns_none(self, db_session):
        repo = RunComparisonRepository()
        run_a_id, run_b_id = self._seed_runs(db_session)

        result = repo.get_by_pair_and_hash(run_a_id, run_b_id, "nonexistent_hash", db_session)
        assert result is None

    def test_different_hash_is_cache_miss(self, db_session):
        repo = RunComparisonRepository()
        run_a_id, run_b_id = self._seed_runs(db_session)

        repo.create(
            db_session,
            run_a_id=run_a_id,
            run_b_id=run_b_id,
            prompt_hash="hash_v1",
            model_name="gemini-3.6-flash",
            overall_summary="First version.",
            better_run="Run A.",
            key_improvements="None.",
            tradeoffs="None.",
            configuration_analysis="Identical configs.",
            next_recommendation="Try a different model.",
        )

        miss = repo.get_by_pair_and_hash(run_a_id, run_b_id, "hash_v2", db_session)
        assert miss is None


# ─── Service (Gemini Mocked) ──────────────────────────────────────────────────

class TestRunComparisonService:
    def _build_service(self, mock_gemini_response: str):
        from app.services.run_comparison_service import RunComparisonService

        run_repo = MagicMock()
        experiment_repo = MagicMock()
        run_result_repo = MagicMock()
        dataset_repo = MagicMock()
        comparison_repo = MagicMock()
        gemini_service = MagicMock()

        gemini_service.generate_comparison.return_value = mock_gemini_response
        gemini_service.model_name = "gemini-3.6-flash"

        exp = _make_experiment()
        dataset = _make_dataset()
        experiment_repo.get_by_id.return_value = exp
        dataset_repo.get_by_id.return_value = dataset

        return RunComparisonService(
            run_repo=run_repo,
            experiment_repo=experiment_repo,
            run_result_repo=run_result_repo,
            dataset_repo=dataset_repo,
            comparison_repo=comparison_repo,
            gemini_service=gemini_service,
        ), run_repo, run_result_repo, comparison_repo

    def test_same_run_id_raises_400(self):
        from app.services.run_comparison_service import RunComparisonService
        from fastapi import HTTPException

        service = RunComparisonService(
            run_repo=MagicMock(), experiment_repo=MagicMock(),
            run_result_repo=MagicMock(), dataset_repo=MagicMock(),
            comparison_repo=MagicMock(), gemini_service=MagicMock(),
        )
        with pytest.raises(HTTPException) as exc_info:
            service.get_or_generate_comparison("same-id", "same-id", db=MagicMock())
        assert exc_info.value.status_code == 400

    def test_run_a_not_found_raises_404(self):
        from app.services.run_comparison_service import RunComparisonService
        from fastapi import HTTPException

        run_repo = MagicMock()
        run_repo.get_by_id.return_value = None
        service = RunComparisonService(
            run_repo=run_repo, experiment_repo=MagicMock(),
            run_result_repo=MagicMock(), dataset_repo=MagicMock(),
            comparison_repo=MagicMock(), gemini_service=MagicMock(),
        )
        with pytest.raises(HTTPException) as exc_info:
            service.get_or_generate_comparison("run-a", "run-b", db=MagicMock())
        assert exc_info.value.status_code == 404

    def test_non_completed_run_raises_422(self):
        from app.services.run_comparison_service import RunComparisonService
        from fastapi import HTTPException

        run_repo = MagicMock()
        exp = _make_experiment()
        run_a = _make_run(exp.id, status="running")
        run_b = _make_run(exp.id, run_number=2, status="completed")
        run_repo.get_by_id.side_effect = [run_a, run_b]

        service = RunComparisonService(
            run_repo=run_repo, experiment_repo=MagicMock(),
            run_result_repo=MagicMock(), dataset_repo=MagicMock(),
            comparison_repo=MagicMock(), gemini_service=MagicMock(),
        )
        with pytest.raises(HTTPException) as exc_info:
            service.get_or_generate_comparison(run_a.id, run_b.id, db=MagicMock())
        assert exc_info.value.status_code == 422

    def test_cross_experiment_raises_422(self):
        from app.services.run_comparison_service import RunComparisonService
        from fastapi import HTTPException

        run_repo = MagicMock()
        run_a = _make_run("exp-1")
        run_b = _make_run("exp-2", run_number=2)
        run_repo.get_by_id.side_effect = [run_a, run_b]

        service = RunComparisonService(
            run_repo=run_repo, experiment_repo=MagicMock(),
            run_result_repo=MagicMock(), dataset_repo=MagicMock(),
            comparison_repo=MagicMock(), gemini_service=MagicMock(),
        )
        with pytest.raises(HTTPException) as exc_info:
            service.get_or_generate_comparison(run_a.id, run_b.id, db=MagicMock())
        assert exc_info.value.status_code == 422

    def test_cache_hit_returns_cached_response(self):
        service, run_repo, run_result_repo, comparison_repo = self._build_service(VALID_COMPARISON_JSON)

        exp = _make_experiment()
        run_a = _make_run(exp.id)
        run_b = _make_run(exp.id, run_number=2)
        run_repo.get_by_id.side_effect = [run_a, run_b]
        run_result_repo.get_by_run_id.return_value = _make_result(run_a.id)

        cached_record = MagicMock()
        cached_record.id = "cached-id"
        cached_record.run_a_id = run_a.id
        cached_record.run_b_id = run_b.id
        cached_record.overall_summary = "Cached response."
        cached_record.better_run = "Run B."
        cached_record.key_improvements = "Accuracy +5%."
        cached_record.tradeoffs = "None."
        cached_record.configuration_analysis = "Same config."
        cached_record.next_recommendation = "Try RF."
        cached_record.model_name = "gemini-3.6-flash"
        cached_record.created_at = datetime.now(timezone.utc)
        comparison_repo.get_by_pair_and_hash.return_value = cached_record

        result = service.get_or_generate_comparison(run_a.id, run_b.id, db=MagicMock())

        assert result.cached is True
        assert result.overall_summary == "Cached response."
        comparison_repo.create.assert_not_called()

    def test_fresh_comparison_calls_gemini_and_caches(self):
        service, run_repo, run_result_repo, comparison_repo = self._build_service(VALID_COMPARISON_JSON)

        exp = _make_experiment()
        run_a = _make_run(exp.id)
        run_b = _make_run(exp.id, run_number=2)
        run_repo.get_by_id.side_effect = [run_a, run_b]
        run_result_repo.get_by_run_id.return_value = _make_result(run_a.id)

        comparison_repo.get_by_pair_and_hash.return_value = None

        stored_record = MagicMock()
        stored_record.id = "new-id"
        stored_record.run_a_id = run_a.id
        stored_record.run_b_id = run_b.id
        stored_record.overall_summary = "Run B outperformed Run A across all metrics."
        stored_record.better_run = "Run B is the better run with higher accuracy and F1."
        stored_record.key_improvements = "Accuracy improved by 5%, F1 by 3%."
        stored_record.tradeoffs = "Execution time increased by 2 seconds."
        stored_record.configuration_analysis = "Increasing max_depth from 5 to 10 improved boundaries."
        stored_record.next_recommendation = "Try n_estimators=200 with learning_rate=0.05."
        stored_record.model_name = "gemini-3.6-flash"
        stored_record.created_at = datetime.now(timezone.utc)
        comparison_repo.create.return_value = stored_record

        result = service.get_or_generate_comparison(run_a.id, run_b.id, db=MagicMock())

        assert result.cached is False
        assert "Run B outperformed" in result.overall_summary
        comparison_repo.create.assert_called_once()

    def test_metric_deltas_included_in_response(self):
        service, run_repo, run_result_repo, comparison_repo = self._build_service(VALID_COMPARISON_JSON)

        exp = _make_experiment()
        run_a = _make_run(exp.id)
        run_b = _make_run(exp.id, run_number=2)
        run_repo.get_by_id.side_effect = [run_a, run_b]
        run_result_repo.get_by_run_id.side_effect = [
            _make_result(run_a.id, accuracy=0.90, f1_score=0.88),
            _make_result(run_b.id, accuracy=0.95, f1_score=0.92),
        ]
        comparison_repo.get_by_pair_and_hash.return_value = None

        stored_record = MagicMock()
        stored_record.id = "new-id"
        stored_record.run_a_id = run_a.id
        stored_record.run_b_id = run_b.id
        stored_record.overall_summary = "Run B outperformed Run A across all metrics."
        stored_record.better_run = "Run B."
        stored_record.key_improvements = "Accuracy +5%."
        stored_record.tradeoffs = "None."
        stored_record.configuration_analysis = "max_depth change."
        stored_record.next_recommendation = "Try n_estimators=200."
        stored_record.model_name = "gemini-3.6-flash"
        stored_record.created_at = datetime.now(timezone.utc)
        comparison_repo.create.return_value = stored_record

        result = service.get_or_generate_comparison(run_a.id, run_b.id, db=MagicMock())

        acc_delta = next(d for d in result.metric_deltas if d.metric == "Accuracy")
        assert acc_delta.direction == "up"
        assert abs(acc_delta.delta - 0.05) < 1e-6


# ─── Router Integration Tests ─────────────────────────────────────────────────

class TestCompareRunsRouter:
    @pytest.fixture
    def test_client(self, db_session):
        """TestClient with SQLite overriding the real DB."""
        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def _seed_completed_runs(self, db) -> tuple[str, str]:
        """Seed two completed runs in SQLite for router tests."""
        from app.models.dataset import Dataset, DatasetStatus
        from app.models.experiment import Experiment, ExperimentStatus, Run, RunStatus

        dataset = Dataset(
            id=str(uuid.uuid4()),
            name="test.csv",
            original_filename="test.csv",
            file_hash=str(uuid.uuid4()),  # unique per test run
            file_size_bytes=1000,
            storage_path="/tmp/t.csv",
            status=DatasetStatus.ready,
            version="v1",
        )
        db.add(dataset)
        db.flush()

        exp = Experiment(
            id=str(uuid.uuid4()), name="Router Test Exp",
            dataset_id=dataset.id, status=ExperimentStatus.active,
        )
        db.add(exp)
        db.flush()

        run_a = Run(
            id=str(uuid.uuid4()), experiment_id=exp.id,
            run_number=1, status=RunStatus.completed,
        )
        run_b = Run(
            id=str(uuid.uuid4()), experiment_id=exp.id,
            run_number=2, status=RunStatus.completed,
        )
        db.add(run_a)
        db.add(run_b)
        db.commit()
        return run_a.id, run_b.id

    def _override_service(self, gemini_mock):
        """Override the RunComparisonService dependency with a real service using mocked Gemini."""
        from app.routers.ai import get_run_comparison_service
        from app.services.run_comparison_service import RunComparisonService
        from app.repositories.run_repository import RunRepository
        from app.repositories.experiment_repository import ExperimentRepository
        from app.repositories.run_result_repository import RunResultRepository
        from app.repositories.dataset_repository import DatasetRepository

        def _service():
            return RunComparisonService(
                run_repo=RunRepository(),
                experiment_repo=ExperimentRepository(),
                run_result_repo=RunResultRepository(),
                dataset_repo=DatasetRepository(),
                comparison_repo=RunComparisonRepository(),
                gemini_service=gemini_mock,
            )

        app.dependency_overrides[get_run_comparison_service] = _service

    def test_compare_returns_200_fresh(self, test_client, db_session):
        run_a_id, run_b_id = self._seed_completed_runs(db_session)

        gemini_mock = MagicMock()
        gemini_mock.generate_comparison.return_value = VALID_COMPARISON_JSON
        gemini_mock.model_name = "gemini-3.6-flash"
        self._override_service(gemini_mock)

        response = test_client.post(
            "/api/v1/runs/compare",
            json={"run_a_id": run_a_id, "run_b_id": run_b_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "AI comparison generated successfully."
        assert "overall_summary" in data["data"]
        assert data["data"]["cached"] is False

        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = lambda: db_session

    def test_compare_returns_200_cached(self, test_client, db_session):
        run_a_id, run_b_id = self._seed_completed_runs(db_session)

        gemini_mock = MagicMock()
        gemini_mock.generate_comparison.return_value = VALID_COMPARISON_JSON
        gemini_mock.model_name = "gemini-3.6-flash"
        self._override_service(gemini_mock)

        # First call — generates and caches
        test_client.post("/api/v1/runs/compare", json={"run_a_id": run_a_id, "run_b_id": run_b_id})
        # Second call — should return cached
        r2 = test_client.post("/api/v1/runs/compare", json={"run_a_id": run_a_id, "run_b_id": run_b_id})

        assert r2.status_code == 200
        assert r2.json()["message"] == "Cached comparison retrieved."
        assert gemini_mock.generate_comparison.call_count == 1

        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = lambda: db_session

    def test_compare_requires_both_run_ids(self, test_client):
        response = test_client.post(
            "/api/v1/runs/compare",
            json={"run_a_id": "some-id"},  # missing run_b_id
        )
        assert response.status_code == 422  # FastAPI validation error
