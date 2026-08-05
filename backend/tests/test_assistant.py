"""
test_assistant.py — Comprehensive test suite for Ask MicroFlow (Natural Language Assistant).

Covers:
  - PromptBuilder: Intent and Assistant prompt structure
  - ResponseParser: Intent parsing, assistant parsing, fallback values, validation errors
  - AIQueryRepository: Caching and recent queries (SQLite in-memory)
  - AIQueryService: Unsupported intent refusal, cache hits, repository data execution
  - Assistant Router: /query, /recent, /suggestions endpoints with mocked Gemini
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.prompt_builder import build_intent_prompt, build_assistant_prompt
from app.ai.response_parser import parse_intent_response, parse_assistant_response
from app.ai.schemas import ConversationMessage
from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models.ai_query import AIQueryCache
from app.repositories.ai_query_repository import AIQueryRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.run_repository import RunRepository
from app.repositories.run_result_repository import RunResultRepository
from app.routers.assistant import get_ai_query_service
from app.services.ai_query_service import AIQueryService


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


# ─── Unit Tests: Prompt Builder ───────────────────────────────────────────────

class TestAssistantPromptBuilder:
    def test_build_intent_prompt_includes_whitelist_and_question(self):
        prompt = build_intent_prompt("Which Random Forest run performed best?")
        assert "SUPPORTED INTENTS" in prompt
        assert "Which Random Forest run performed best?" in prompt
        assert "unsupported" in prompt

    def test_build_intent_prompt_formats_context(self):
        context = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "How can I help?"}]
        prompt = build_intent_prompt("Show failed runs.", context=context)
        assert "USER: Hello" in prompt
        assert "ASSISTANT: How can I help?" in prompt

    def test_build_assistant_prompt_includes_authentic_data(self):
        data = "TRAINING RUNS & METRICS:\n- Run #1 (Accuracy: 0.95)"
        prompt = build_assistant_prompt("Which run is best?", "best_performing", data)
        assert "AUTHENTIC DATABASE RESULTS" in prompt
        assert "- Run #1 (Accuracy: 0.95)" in prompt
        assert "Never output markdown tables" in prompt


# ─── Unit Tests: Response Parser ──────────────────────────────────────────────

class TestAssistantResponseParser:
    def test_parse_intent_response_valid_json(self):
        raw = '{"intent": "runs", "filters": {"status": "failed"}, "reasoning_required": true}'
        result = parse_intent_response(raw)
        assert result.intent == "runs"
        assert result.filters["status"] == "failed"
        assert result.reasoning_required is True

    def test_parse_intent_response_fenced_json(self):
        raw = '```json\n{"intent": "unsupported", "filters": {}}\n```'
        result = parse_intent_response(raw)
        assert result.intent == "unsupported"

    def test_parse_assistant_response_valid(self):
        raw = json.dumps({
            "answer": "Run #5 achieved the highest accuracy.",
            "reasoning": "Compared all completed Random Forest models.",
            "supporting_data": "Run #5 Accuracy: 0.9450 vs Run #3 Accuracy: 0.8800.",
            "recommendation": "Deploy Run #5 to production testing."
        })
        result = parse_assistant_response(raw)
        assert "highest accuracy" in result["answer"]
        assert "Deploy Run #5" in result["recommendation"]

    def test_parse_assistant_response_missing_recommendation_defaults(self):
        raw = json.dumps({
            "answer": "There are 3 experiments.",
            "reasoning": "Counted experiments in db.",
            "supporting_data": "Exp 1, Exp 2, Exp 3"
        })
        result = parse_assistant_response(raw)
        assert result["recommendation"] == "No further action required."

    def test_parse_assistant_response_missing_required_field_raises(self):
        raw = '{"answer": "Incomplete answer without reasoning"}'
        with pytest.raises(ValueError, match="missing required fields"):
            parse_assistant_response(raw)


# ─── Unit Tests: Repository ───────────────────────────────────────────────────

class TestAIQueryRepository:
    def test_create_and_get_by_hash(self, db_session):
        repo = AIQueryRepository()
        record = repo.create(
            db_session,
            query_hash="hash_123",
            question="Best experiment?",
            intent="best_performing",
            filters_json='{"metric_sort": "accuracy"}',
            model_name="gemini-3.6-flash",
            answer="Experiment A",
            reasoning="Highest F1",
            supporting_data="F1 = 0.92",
            recommendation="Retrain on more data",
        )
        assert record.id is not None

        retrieved = repo.get_by_hash("hash_123", db_session)
        assert retrieved is not None
        assert retrieved.question == "Best experiment?"
        assert retrieved.answer == "Experiment A"

    def test_get_recent_orders_by_time(self, db_session):
        repo = AIQueryRepository()
        for i in range(3):
            repo.create(
                db_session,
                query_hash=f"hash_{i}",
                question=f"Q{i}",
                intent="runs",
                filters_json="{}",
                model_name="gemini-3.6-flash",
                answer=f"A{i}",
                reasoning="R",
                supporting_data="D",
                recommendation="Rec",
            )
        recent = repo.get_recent(2, db_session)
        assert len(recent) == 2
        # Most recent first
        assert recent[0].question == "Q2"


# ─── Unit Tests: Service Layer ────────────────────────────────────────────────

class TestAIQueryService:
    def _get_service_with_mock(self):
        gemini_mock = MagicMock()
        gemini_mock.model_name = "gemini-test-model"
        service = AIQueryService(
            query_repo=AIQueryRepository(),
            dataset_repo=DatasetRepository(),
            experiment_repo=ExperimentRepository(),
            run_repo=RunRepository(),
            run_result_repo=RunResultRepository(),
            gemini_service=gemini_mock,
        )
        return service, gemini_mock

    def test_unsupported_intent_rejected_without_db_or_answer_generation(self, db_session):
        service, gemini_mock = self._get_service_with_mock()
        gemini_mock.extract_intent.return_value = '{"intent": "unsupported", "filters": {}}'

        res = service.process_query("What is the capital of France?", None, db_session)
        assert res.intent == "unsupported"
        assert "specialized for machine learning experimentation" in res.answer
        # Ensure generate_answer was never called!
        gemini_mock.generate_answer.assert_not_called()

    def test_cache_hit_prevents_gemini_answer_call(self, db_session):
        service, gemini_mock = self._get_service_with_mock()
        # Pre-seed cache
        gemini_mock.extract_intent.return_value = '{"intent": "experiments", "filters": {}}'
        gemini_mock.generate_answer.return_value = json.dumps({
            "answer": "First generated answer",
            "reasoning": "R",
            "supporting_data": "D",
            "recommendation": "Rec"
        })
        res1 = service.process_query("How many experiments?", None, db_session)
        assert res1.cached is False
        assert gemini_mock.generate_answer.call_count == 1

        # Second identical question should hit cache
        res2 = service.process_query("How many experiments?", None, db_session)
        assert res2.cached is True
        assert res2.answer == "First generated answer"
        # call_count remains 1
        assert gemini_mock.generate_answer.call_count == 1


# ─── Router Integration Tests ─────────────────────────────────────────────────

class TestAssistantRouter:
    def _override_service(self, gemini_mock):
        service = AIQueryService(
            query_repo=AIQueryRepository(),
            dataset_repo=DatasetRepository(),
            experiment_repo=ExperimentRepository(),
            run_repo=RunRepository(),
            run_result_repo=RunResultRepository(),
            gemini_service=gemini_mock,
        )
        app.dependency_overrides[get_ai_query_service] = lambda: service

    def test_query_endpoint_returns_200(self, test_client):
        mock_gemini = MagicMock()
        mock_gemini.model_name = "mock-model"
        mock_gemini.extract_intent.return_value = '{"intent": "datasets", "filters": {}}'
        mock_gemini.generate_answer.return_value = json.dumps({
            "answer": "We have 2 datasets.",
            "reasoning": "Queried database summary.",
            "supporting_data": "Dataset A, Dataset B",
            "recommendation": "Run basic baseline model."
        })
        self._override_service(mock_gemini)

        response = test_client.post("/api/v1/assistant/query", json={"question": "List datasets."})
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["answer"] == "We have 2 datasets."
        assert data["cached"] is False

    def test_recent_and_suggestions_endpoints_return_200(self, test_client):
        self._override_service(MagicMock())
        res_rec = test_client.get("/api/v1/assistant/recent")
        assert res_rec.status_code == 200

        res_sug = test_client.get("/api/v1/assistant/suggestions")
        assert res_sug.status_code == 200
        assert len(res_sug.json()["data"]) >= 4
