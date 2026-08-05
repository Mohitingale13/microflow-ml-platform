"""
test_experiment_strategy.py — Unit, integration, and router tests for AI Experiment Strategy.

Uses mocked Gemini Service to ensure zero external API calls during test execution.
Verifies evidence calculation, plateau detection, caching behavior, and schema compliance.
"""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models.dataset import Dataset, DatasetStatus
from app.models.experiment import Experiment, ExperimentStatus, Run, RunStatus
from app.models.artifact import RunResult
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_strategy_repository import ExperimentStrategyRepository
from app.services.experiment_strategy_service import ExperimentStrategyService

MOCK_STRATEGY_JSON = json.dumps({
    "overall_assessment": "Initial baseline runs have evaluated tree ensembles with robust classification metrics.",
    "current_experiment_status": "Active optimization",
    "observed_trends": ["Random Forest shows 95% accuracy; XGBoost reached 96% with faster convergence."],
    "strongest_model": "Run #2 (XGBoost) - 0.9600 accuracy",
    "most_stable_model": "Run #1 (Random Forest) - zero parameter variance across CV folds",
    "what_has_been_learned": ["Tree depth beyond 6 does not yield statistically significant gains on this dataset size."],
    "remaining_search_space": ["Logistic Regression baseline unprobed; learning rates below 0.05 remain unexplored."],
    "recommended_next_experiment": {
        "action": "Evaluate XGBoost with reduced learning rate and increased estimators",
        "model_type": "XGBoost",
        "hyperparameters": {"learning_rate": 0.03, "n_estimators": 250, "max_depth": 5},
        "rationale": "Empirical evidence indicates tree depth saturates at 5; fine-tuning learning rate may squeeze out remaining precision."
    },
    "confidence": "High",
    "evidence_used": ["Run #1 accuracy (0.9500)", "Run #2 accuracy (0.9600)", "Dataset missing value ratio (0.0%)"],
    "potential_risks": ["Risk of overfitting if n_estimators exceeds 300 without subsample regularization."]
})


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
def sample_experiment_and_runs(db_session: Session):
    repo = DatasetRepository()
    ds = repo.create(
        db_session,
        name="test_genomics.csv",
        description="Genomics clinical trials",
        original_filename="test_genomics.csv",
        file_hash=str(uuid.uuid4())[:16],
        file_size_bytes=1024,
        storage_path="/tmp/test_genomics.csv",
    )
    repo.update(
        db_session,
        ds,
        status=DatasetStatus.ready,
        row_count=500,
        column_count=10,
        column_names=["feature_1", "feature_2", "target"],
        dtypes={"feature_1": "float64", "target": "int64"},
    )

    exp = Experiment(
        name="Genomics Classifier Trial",
        dataset_id=ds.id,
        objective="Maximize F1 score on genomic mutations",
        description="Evaluating classifiers for early pathology detection",
        status=ExperimentStatus.active,
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)

    run1 = Run(
        experiment_id=exp.id,
        run_number=1,
        model_type="RandomForestClassifier",
        training_configuration={"n_estimators": 100, "max_depth": 5},
        status=RunStatus.completed,
    )
    run2 = Run(
        experiment_id=exp.id,
        run_number=2,
        model_type="XGBClassifier",
        training_configuration={"n_estimators": 100, "learning_rate": 0.1, "max_depth": 5},
        status=RunStatus.completed,
    )
    db_session.add_all([run1, run2])
    db_session.commit()
    db_session.refresh(run1)
    db_session.refresh(run2)

    res1 = RunResult(
        run_id=run1.id,
        accuracy=0.9500,
        precision=0.9400,
        recall=0.9500,
        f1_score=0.9450,
        roc_auc=0.9800,
        execution_time_seconds=1.25,
        model_type="RandomForestClassifier",
        confusion_matrix=[[50, 2], [3, 45]],
    )
    res2 = RunResult(
        run_id=run2.id,
        accuracy=0.9600,
        precision=0.9550,
        recall=0.9600,
        f1_score=0.9575,
        roc_auc=0.9850,
        execution_time_seconds=0.85,
        model_type="XGBClassifier",
        confusion_matrix=[[51, 1], [2, 46]],
    )
    db_session.add_all([res1, res2])
    db_session.commit()

    return exp, ds, [run1, run2]


def test_evidence_computation_and_plateau_detection(db_session: Session, sample_experiment_and_runs):
    exp, ds, runs = sample_experiment_and_runs
    service = ExperimentStrategyService()

    # Refresh runs with results
    from app.repositories.run_repository import RunRepository
    runs_loaded = RunRepository().list_by_experiment(exp.id, db_session)
    
    evidence = service._compute_evidence(exp, ds, runs_loaded, db_session)
    assert evidence["run_counts"]["completed"] == 2
    assert evidence["metrics_analysis"]["best_accuracy"] == 0.9600
    assert "XGBoost" in evidence["metrics_analysis"]["fastest_execution"]
    assert "Logistic Regression" in evidence["search_space"]["unexplored_model_families"]
    assert evidence["trend_and_plateau_analysis"]["plateau_detected"] is False


def test_plateau_detection_triggered(db_session: Session, sample_experiment_and_runs):
    exp, ds, _ = sample_experiment_and_runs
    
    # Add a 3rd run that performs almost identical to run 2 (plateauing)
    run3 = Run(
        experiment_id=exp.id,
        run_number=3,
        model_type="XGBClassifier",
        training_configuration={"n_estimators": 150, "learning_rate": 0.08},
        status=RunStatus.completed,
    )
    db_session.add(run3)
    db_session.commit()
    db_session.refresh(run3)
    res3 = RunResult(
        run_id=run3.id,
        accuracy=0.9602,
        precision=0.9551,
        recall=0.9601,
        f1_score=0.9576,
        roc_auc=0.9851,
        execution_time_seconds=0.90,
        model_type="XGBClassifier",
        confusion_matrix=[[51, 1], [2, 46]],
    )
    db_session.add(res3)
    db_session.commit()

    from app.repositories.run_repository import RunRepository
    runs_loaded = RunRepository().list_by_experiment(exp.id, db_session)
    service = ExperimentStrategyService()
    evidence = service._compute_evidence(exp, ds, runs_loaded, db_session)

    # Variance is minimal across recent runs (<0.5%), so plateau should be True
    assert evidence["trend_and_plateau_analysis"]["plateau_detected"] is True
    assert "CRITICAL: Performance plateau detected" in evidence["trend_and_plateau_analysis"]["stopping_guidance"]


@patch("app.ai.gemini_service.GeminiService.generate_experiment_strategy")
def test_router_experiment_strategy_generation_and_caching(mock_generate, test_client, sample_experiment_and_runs):
    exp, ds, _ = sample_experiment_and_runs
    mock_generate.return_value = MOCK_STRATEGY_JSON

    # First request - should generate and cache
    resp1 = test_client.post(f"/api/v1/experiments/{exp.id}/strategy")
    assert resp1.status_code == 200, resp1.text
    body1 = resp1.json()
    assert body1["success"] is True
    data1 = body1["data"]
    assert data1["cached"] is False
    assert data1["confidence"] == "High"
    assert "XGBoost" in data1["strongest_model"]
    assert mock_generate.call_count == 1

    # Second request - should hit database cache without re-invoking Gemini
    resp2 = test_client.post(f"/api/v1/experiments/{exp.id}/strategy")
    assert resp2.status_code == 200
    body2 = resp2.json()
    data2 = body2["data"]
    assert data2["cached"] is True
    assert mock_generate.call_count == 1  # Verified zero additional external API calls!
