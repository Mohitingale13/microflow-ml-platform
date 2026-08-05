"""
test_dataset_ai.py — Test suite for AI Dataset Intelligence (Milestone 4).

Covers:
  - PromptBuilder: build_dataset_analysis_prompt
  - ResponseParser: parse_dataset_analysis_response
  - DatasetAIAnalysisRepository: SQLite in-memory CRUD & cache lookups
  - DatasetAIService: deterministic quality scoring, readiness validation, and caching logic
  - API Router: POST /api/v1/datasets/{id}/analyze endpoint
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.prompt_builder import build_dataset_analysis_prompt
from app.ai.response_parser import parse_dataset_analysis_response
from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models.dataset import Dataset, DatasetStatus
from app.models.dataset_ai_analysis import DatasetAIAnalysis
from app.repositories.dataset_ai_analysis_repository import DatasetAIAnalysisRepository
from app.repositories.dataset_repository import DatasetRepository
from app.routers.datasets import get_dataset_ai_service
from app.services.dataset_ai_service import DatasetAIService


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


@pytest.fixture
def sample_dataset(db_session):
    repo = DatasetRepository()
    ds = repo.create(
        db_session,
        name="Credit Default Prep",
        description="Historical customer financial features",
        original_filename="credit_data.csv",
        file_hash=str(uuid.uuid4())[:16],
        file_size_bytes=1048576,
        storage_path="/tmp/mock_credit.csv",
    )
    repo.update(
        db_session,
        ds,
        status=DatasetStatus.ready,
        row_count=1500,
        column_count=12,
        column_names=["age", "income", "loan_amount", "default_flag"],
        dtypes={"age": "int64", "income": "float64", "loan_amount": "float64", "default_flag": "int64"},
        missing_values={"age": 0, "income": 5, "loan_amount": 0, "default_flag": 0},
    )
    return ds


# ─── Unit Tests: Prompt Builder ───────────────────────────────────────────────

class TestDatasetPromptBuilder:
    def test_build_dataset_analysis_prompt(self, sample_dataset):
        stats = {
            "age": {"mean": 35.5, "min": 18, "max": 75},
            "default_flag": {"unique_values": 2, "most_frequent": "0"},
        }
        rows = [
            {"age": 25, "income": 45000.0, "loan_amount": 10000.0, "default_flag": 0},
            {"age": 42, "income": 82000.0, "loan_amount": 35000.0, "default_flag": 1},
        ]
        prompt = build_dataset_analysis_prompt(sample_dataset, stats, rows, 90, "Excellent")

        assert "Credit Default Prep" in prompt
        assert "90/100 (Excellent)" in prompt
        assert "age=25" in prompt
        assert "overall_summary" in prompt
        assert "recommended_target" in prompt
        assert "feature_observations" in prompt


# ─── Unit Tests: Response Parser ──────────────────────────────────────────────

class TestDatasetResponseParser:
    def test_parse_valid_json(self):
        valid_json = json.dumps({
            "overall_summary": "Dataset is well-populated with clean financial predictors.",
            "recommended_target": "default_flag — clean binary target for risk classification.",
            "dataset_quality": {"score": 90, "label": "Excellent", "explanation": "Minimal missing values."},
            "strengths": ["Adequate row sample", "Clear feature types"],
            "potential_issues": ["Small percentage of missing income records"],
            "recommended_preprocessing": ["Impute missing income values with median"],
            "recommended_models": [{"model": "XGBoost", "suitability": "High", "reasoning": "Handles tabular financial metrics well."}],
            "feature_observations": [{"feature": "income", "observation": "Positive skew expected."}],
            "risk_assessment": "Low operational risk.",
            "next_steps": ["1. Impute missing income", "2. Configure XGBoost baseline"]
        })
        parsed = parse_dataset_analysis_response(valid_json)
        assert parsed["overall_summary"].startswith("Dataset is well-populated")
        assert len(parsed["strengths"]) == 2
        assert parsed["dataset_quality"]["score"] == 90

    def test_parse_missing_key_raises(self):
        invalid_json = json.dumps({"overall_summary": "Missing other keys"})
        with pytest.raises(ValueError, match="missing required fields"):
            parse_dataset_analysis_response(invalid_json)


# ─── Unit Tests: Repository ───────────────────────────────────────────────────

class TestDatasetAIRepository:
    def test_repository_crud(self, db_session, sample_dataset):
        repo = DatasetAIAnalysisRepository()
        hash_str = "abcdef1234567890"
        
        # Initial lookup is None
        assert repo.get_by_dataset_and_hash(sample_dataset.id, hash_str, db_session) is None
        
        # Create
        record = repo.create(
            db=db_session,
            dataset_id=sample_dataset.id,
            prompt_hash=hash_str,
            model_name="test-model",
            analysis_json='{"mock": "data"}',
        )
        assert record.id is not None
        assert record.dataset_id == sample_dataset.id
        
        # Retrieve by hash
        hit = repo.get_by_dataset_and_hash(sample_dataset.id, hash_str, db_session)
        assert hit is not None
        assert hit.id == record.id

        # Retrieve latest
        latest = repo.get_latest_by_dataset(sample_dataset.id, db_session)
        assert latest is not None
        assert latest.id == record.id


# ─── Unit Tests: Service & Quality Score ──────────────────────────────────────

class TestDatasetAIService:
    def test_quality_score_calculation(self):
        service = DatasetAIService(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        
        # Perfect dataset
        mock_ds = MagicMock()
        mock_ds.missing_values = {"col1": 0, "col2": 0}
        score, label = service._calculate_quality_score(mock_ds, 1000, 10)
        assert score == 100
        assert label == "Excellent"

        # Tiny dataset penalty (<20 rows) + few columns (<2)
        mock_ds.missing_values = {"col1": 0}
        score_tiny, label_tiny = service._calculate_quality_score(mock_ds, 15, 1)
        assert score_tiny < 70
        assert label_tiny in ["Good", "Fair", "Poor"]

    def test_get_or_generate_not_ready_raises(self, db_session, sample_dataset):
        repo = DatasetRepository()
        repo.update(db_session, sample_dataset, status=DatasetStatus.analysing)
        
        service = DatasetAIService(repo, DatasetAIAnalysisRepository(), MagicMock(), MagicMock())
        with pytest.raises(Exception) as exc_info:
            service.get_or_generate_analysis(sample_dataset.id, db_session)
        assert "status 'ready'" in str(exc_info.value)


# ─── Integration Tests: API Endpoint ──────────────────────────────────────────

def test_analyze_dataset_endpoint(test_client, db_session, sample_dataset):
    mock_gemini = MagicMock()
    mock_gemini.model_name = "claude-sonnet-4.6"
    mock_gemini.generate_dataset_analysis.return_value = json.dumps({
        "overall_summary": "High-quality tabular classification dataset.",
        "recommended_target": "default_flag",
        "dataset_quality": {"score": 95, "label": "Excellent", "explanation": "Clean dataset."},
        "strengths": ["Clean categorical targets"],
        "potential_issues": ["Minor income nulls"],
        "recommended_preprocessing": ["Impute income with median"],
        "recommended_models": [{"model": "Random Forest", "suitability": "High", "reasoning": "Robust to outliers."}],
        "feature_observations": [{"feature": "default_flag", "observation": "Balanced binary target."}],
        "risk_assessment": "Minimal risks.",
        "next_steps": ["Configure baseline Random Forest experiment."]
    })

    mock_ds_service = MagicMock()
    mock_ds_service.get_statistics.return_value = {"age": {"mean": 35.0}}
    mock_ds_service.get_preview.return_value = {"rows": [{"age": 35, "default_flag": 0}]}

    test_service = DatasetAIService(
        dataset_repo=DatasetRepository(),
        analysis_repo=DatasetAIAnalysisRepository(),
        gemini_service=mock_gemini,
        dataset_service=mock_ds_service,
    )

    def override_service():
        return test_service

    app.dependency_overrides[get_dataset_ai_service] = override_service
    
    response = test_client.post(f"/api/v1/datasets/{sample_dataset.id}/analyze")
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["dataset_id"] == sample_dataset.id
    assert data["cached"] is False
    assert data["overall_summary"] == "High-quality tabular classification dataset."
    assert data["dataset_quality"]["score"] > 80
    assert data["model_name"] == "claude-sonnet-4.6"

    # Second request should return from cache
    response2 = test_client.post(f"/api/v1/datasets/{sample_dataset.id}/analyze")
    assert response2.status_code == 200
    data2 = response2.json()["data"]
    assert data2["cached"] is True
    assert mock_gemini.generate_dataset_analysis.call_count == 1  # Not called again!
