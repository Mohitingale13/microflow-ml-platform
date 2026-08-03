"""
test_metrics.py — Comprehensive tests for Milestone 5 Metrics Dashboard backend.

Tests:
  - MetricsRepository: SQL aggregates, empty state, group-bys, filters
  - MetricsService: Business logic, empty state handling, run_ids parsing
  - Metrics Router: HTTP endpoints (/overview, /models, /experiments, /datasets, /runs/compare)
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models.artifact import RunResult
from app.models.dataset import Dataset
from app.models.experiment import Experiment, Run, RunStatus
from app.repositories.metrics_repository import MetricsRepository
from app.services.metrics_service import MetricsService


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
def populated_db(db_session):
    """Seed database with 2 datasets, 3 experiments, 5 runs with various statuses."""
    # Dataset 1
    ds1 = Dataset(
        id="ds-1",
        name="Iris Dataset",
        storage_path="/tmp/iris.csv",
        original_filename="iris.csv",
        file_hash="hash1",
        file_size_bytes=4000,
        row_count=150,
        column_count=5,
        column_names=["sepal_length", "sepal_width", "petal_length", "petal_width", "target"],
    )
    # Dataset 2
    ds2 = Dataset(
        id="ds-2",
        name="Wine Dataset",
        storage_path="/tmp/wine.csv",
        original_filename="wine.csv",
        file_hash="hash2",
        file_size_bytes=8000,
        row_count=178,
        column_count=13,
        column_names=["alcohol", "malic_acid", "target"],
    )
    db_session.add_all([ds1, ds2])

    # Experiments
    exp1 = Experiment(
        id="exp-1",
        name="Iris Classification",
        dataset_id="ds-1",
        default_configuration={"test_split": 0.2},
    )
    exp2 = Experiment(
        id="exp-2",
        name="Iris Random Forest Study",
        dataset_id="ds-1",
        default_configuration={"test_split": 0.3},
    )
    exp3 = Experiment(
        id="exp-3",
        name="Wine Quality Experiment",
        dataset_id="ds-2",
        default_configuration={"test_split": 0.2},
    )
    db_session.add_all([exp1, exp2, exp3])

    # Runs
    # Run 1: Completed Random Forest on Exp 1
    r1 = Run(
        id="run-1",
        experiment_id="exp-1",
        run_number=1,
        status=RunStatus.completed,
        model_type="random_forest",
        training_configuration={"n_estimators": 100},
    )
    res1 = RunResult(
        id="res-1",
        run_id="run-1",
        accuracy=0.95,
        precision=0.94,
        recall=0.93,
        f1_score=0.935,
        roc_auc=0.98,
        confusion_matrix=[[10, 1], [0, 9]],
        execution_time_seconds=1.25,
        completed_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        model_type="random_forest",
        dataset_id="ds-1",
    )

    # Run 2: Completed Logistic Regression on Exp 1
    r2 = Run(
        id="run-2",
        experiment_id="exp-1",
        run_number=2,
        status=RunStatus.completed,
        model_type="logistic_regression",
        training_configuration={"C": 1.0},
    )
    res2 = RunResult(
        id="res-2",
        run_id="run-2",
        accuracy=0.85,
        precision=0.84,
        recall=0.83,
        f1_score=0.835,
        roc_auc=0.88,
        confusion_matrix=[[8, 2], [1, 9]],
        execution_time_seconds=0.75,
        completed_at=datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        model_type="logistic_regression",
        dataset_id="ds-1",
    )

    # Run 3: Completed Random Forest on Exp 3 (Wine)
    r3 = Run(
        id="run-3",
        experiment_id="exp-3",
        run_number=1,
        status=RunStatus.completed,
        model_type="random_forest",
        training_configuration={"n_estimators": 200},
    )
    res3 = RunResult(
        id="res-3",
        run_id="run-3",
        accuracy=0.90,
        precision=0.89,
        recall=0.91,
        f1_score=0.90,
        roc_auc=0.94,
        confusion_matrix=[[15, 2], [1, 18]],
        execution_time_seconds=2.0,
        completed_at=datetime(2026, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
        model_type="random_forest",
        dataset_id="ds-2",
    )

    # Run 4: Failed Run on Exp 2 (Should not count in metric averages)
    r4 = Run(
        id="run-4",
        experiment_id="exp-2",
        run_number=1,
        status=RunStatus.failed,
        model_type="xgboost",
        training_configuration={},
    )

    # Run 5: Queued Run on Exp 2 (Should not count in metric averages)
    r5 = Run(
        id="run-5",
        experiment_id="exp-2",
        run_number=2,
        status=RunStatus.queued,
        model_type="xgboost",
        training_configuration={},
    )

    db_session.add_all([r1, res1, r2, res2, r3, res3, r4, r5])
    db_session.commit()
    return db_session


# ── Repository Tests ──────────────────────────────────────────────────────────

def test_metrics_repo_empty_database(db_session):
    repo = MetricsRepository()
    overview = repo.get_overview(db_session)
    assert overview["total_runs"] == 0
    assert overview["completed_runs"] == 0
    assert overview["failed_runs"] == 0
    assert overview["success_rate"] == 0.0
    assert overview["average_accuracy"] is None

    models = repo.get_model_metrics(db_session)
    assert models == []

    exps = repo.get_experiment_metrics(db_session)
    assert exps == []

    datasets = repo.get_dataset_metrics(db_session)
    assert datasets == []

    comp = repo.compare_runs(["non-existent"], db_session)
    assert comp == []


def test_metrics_repo_populated_overview(populated_db):
    repo = MetricsRepository()
    overview = repo.get_overview(populated_db)
    assert overview["total_runs"] == 5
    assert overview["completed_runs"] == 3
    assert overview["failed_runs"] == 1
    assert overview["success_rate"] == 0.6  # 3/5
    # Average accuracy across run-1 (0.95), run-2 (0.85), run-3 (0.90) = 0.90
    assert overview["average_accuracy"] == 0.90
    assert overview["average_precision"] == 0.89
    assert overview["average_f1"] == 0.89
    assert overview["average_training_duration"] == 1.33  # (1.25 + 0.75 + 2.0) / 3


def test_metrics_repo_model_metrics(populated_db):
    repo = MetricsRepository()
    models = repo.get_model_metrics(populated_db)
    assert len(models) == 2  # random_forest and logistic_regression

    rf = next(m for m in models if m["model_type"] == "random_forest")
    assert rf["number_of_runs"] == 2
    assert rf["best_accuracy"] == 0.95
    assert rf["average_accuracy"] == 0.925
    assert rf["best_f1"] == 0.935

    lr = next(m for m in models if m["model_type"] == "logistic_regression")
    assert lr["number_of_runs"] == 1
    assert lr["best_accuracy"] == 0.85
    assert lr["average_accuracy"] == 0.85


def test_metrics_repo_experiment_metrics(populated_db):
    repo = MetricsRepository()
    exps = repo.get_experiment_metrics(populated_db)
    assert len(exps) == 3

    exp1_stat = next(e for e in exps if e["experiment_id"] == "exp-1")
    assert exp1_stat["total_runs"] == 2
    assert exp1_stat["best_accuracy"] == 0.95
    assert exp1_stat["average_accuracy"] == 0.90
    assert exp1_stat["dataset_name"] == "Iris Dataset"

    exp2_stat = next(e for e in exps if e["experiment_id"] == "exp-2")
    assert exp2_stat["total_runs"] == 2
    assert exp2_stat["best_accuracy"] is None  # No completed runs


def test_metrics_repo_dataset_metrics(populated_db):
    repo = MetricsRepository()
    datasets = repo.get_dataset_metrics(populated_db)
    assert len(datasets) == 2

    iris = next(d for d in datasets if d["dataset_id"] == "ds-1")
    assert iris["number_of_experiments"] == 2
    assert iris["number_of_runs"] == 4  # exp1 (2 runs) + exp2 (2 runs)
    assert iris["best_model"] == "random_forest"
    assert iris["best_accuracy"] == 0.95


def test_metrics_repo_compare_runs(populated_db):
    repo = MetricsRepository()
    comp = repo.compare_runs(["run-1", "run-2", "run-4"], populated_db)
    assert len(comp) == 3

    r1_comp = comp[0]
    assert r1_comp["run_id"] == "run-1"
    assert r1_comp["accuracy"] == 0.95
    assert r1_comp["experiment_name"] == "Iris Classification"
    assert r1_comp["dataset_name"] == "Iris Dataset"

    r4_comp = comp[2]
    assert r4_comp["run_id"] == "run-4"
    assert r4_comp["accuracy"] is None  # Failed run has no RunResult


# ── Service Tests ─────────────────────────────────────────────────────────────

def test_metrics_service_compare_runs_parsing(populated_db):
    service = MetricsService()
    # Comma-separated string with whitespace and duplicates
    res = service.compare_runs("run-1, run-2 , run-1", populated_db)
    assert len(res) == 2
    assert res[0]["run_id"] == "run-1"
    assert res[1]["run_id"] == "run-2"


def test_metrics_service_empty_compare_runs(populated_db):
    service = MetricsService()
    assert service.compare_runs("", populated_db) == []
    assert service.compare_runs([], populated_db) == []


# ── Router HTTP Tests ─────────────────────────────────────────────────────────

def test_router_get_overview(test_client, populated_db):
    resp = test_client.get("/api/v1/metrics/overview")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_runs"] == 5
    assert data["completed_runs"] == 3
    assert data["success_rate"] == 0.6
    assert data["average_accuracy"] == 0.90


def test_router_get_models(test_client, populated_db):
    resp = test_client.get("/api/v1/metrics/models")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2
    assert data[0]["best_accuracy"] >= data[1]["best_accuracy"]


def test_router_get_models_with_filter(test_client, populated_db):
    resp = test_client.get("/api/v1/metrics/models?dataset_id=ds-2")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["model_type"] == "random_forest"
    assert data[0]["best_accuracy"] == 0.90


def test_router_get_experiments(test_client, populated_db):
    resp = test_client.get("/api/v1/metrics/experiments")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 3


def test_router_get_datasets(test_client, populated_db):
    resp = test_client.get("/api/v1/metrics/datasets")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2


def test_router_compare_runs(test_client, populated_db):
    resp = test_client.get("/api/v1/metrics/runs/compare?run_ids=run-1,run-3")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2
    assert data[0]["run_id"] == "run-1"
    assert data[1]["run_id"] == "run-3"
