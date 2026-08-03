"""
test_dashboard.py — Integration tests for the Dashboard module.

Tests cover:
  - DashboardRepository: empty database, populated database (all 4 methods)
  - DashboardService: delegation and limit clamping
  - DashboardRouter: all 4 endpoints (empty + populated)
  - Activity feed ordering (newest first)
  - Quick stats correctness

All tests use in-memory SQLite with pre-seeded data.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models.artifact import Artifact, ArtifactType, RunResult
from app.models.dataset import Dataset
from app.models.experiment import Experiment, ExperimentStatus, Run, RunStatus
from app.repositories.dashboard_repository import DashboardRepository
from app.services.dashboard_service import DashboardService


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
def seeded_db(db_session):
    """Seed a complete platform state: 2 datasets, 2 experiments, 3 runs, results, artifacts."""
    now = datetime.now(timezone.utc)
    earlier = now - timedelta(hours=2)
    earliest = now - timedelta(hours=4)

    ds1_id = str(uuid.uuid4())
    ds2_id = str(uuid.uuid4())
    exp1_id = str(uuid.uuid4())
    exp2_id = str(uuid.uuid4())
    run1_id = str(uuid.uuid4())
    run2_id = str(uuid.uuid4())
    run3_id = str(uuid.uuid4())
    result1_id = str(uuid.uuid4())
    result2_id = str(uuid.uuid4())

    # Datasets
    ds1 = Dataset(
        id=ds1_id, name="Iris",
        original_filename="iris.csv", file_hash="hash1",
        file_size_bytes=5000, row_count=150, column_count=5,
        storage_path="/data/iris.csv",
        created_at=earliest, updated_at=earliest,
    )
    ds2 = Dataset(
        id=ds2_id, name="Wine Quality",
        original_filename="wine.csv", file_hash="hash2",
        file_size_bytes=12000, row_count=600, column_count=12,
        storage_path="/data/wine.csv",
        created_at=earlier, updated_at=earlier,
    )
    db_session.add_all([ds1, ds2])
    db_session.commit()

    # Experiments (both on ds1 so ds1 is most used)
    exp1 = Experiment(
        id=exp1_id, name="Iris Classification",
        dataset_id=ds1_id, status=ExperimentStatus.active,
        created_at=earliest, updated_at=earliest,
    )
    exp2 = Experiment(
        id=exp2_id, name="Iris RF Experiment",
        dataset_id=ds1_id, status=ExperimentStatus.active,
        created_at=earlier, updated_at=earlier,
    )
    db_session.add_all([exp1, exp2])
    db_session.commit()

    # Runs
    run1 = Run(
        id=run1_id, experiment_id=exp1_id, run_number=1,
        model_type="logistic_regression", status=RunStatus.completed,
        created_at=earliest, updated_at=earlier,
    )
    run2 = Run(
        id=run2_id, experiment_id=exp1_id, run_number=2,
        model_type="random_forest", status=RunStatus.completed,
        created_at=earlier, updated_at=now,
    )
    run3 = Run(
        id=run3_id, experiment_id=exp2_id, run_number=1,
        model_type="xgboost", status=RunStatus.failed,
        created_at=earlier, updated_at=now,
    )
    db_session.add_all([run1, run2, run3])
    db_session.commit()

    # RunResults (for completed runs)
    result1 = RunResult(
        id=result1_id, run_id=run1_id,
        accuracy=0.9200, precision=0.9100, recall=0.9000, f1_score=0.9050,
        roc_auc=0.9500, confusion_matrix=[[45, 5], [3, 47]],
        execution_time_seconds=12.5,
        model_type="logistic_regression", dataset_id=ds1_id,
        started_at=earliest, completed_at=earlier,
        created_at=earlier,
    )
    result2 = RunResult(
        id=result2_id, run_id=run2_id,
        accuracy=0.9600, precision=0.9550, recall=0.9500, f1_score=0.9525,
        roc_auc=0.9800, confusion_matrix=[[48, 2], [1, 49]],
        execution_time_seconds=8.3,
        model_type="random_forest", dataset_id=ds1_id,
        started_at=earlier, completed_at=now,
        created_at=now,
    )
    db_session.add_all([result1, result2])
    db_session.commit()

    # Artifacts
    art1 = Artifact(
        id=str(uuid.uuid4()), run_id=run1_id, experiment_id=exp1_id, dataset_id=ds1_id,
        artifact_type=ArtifactType.trained_model, filename="model.pkl",
        mime_type="application/octet-stream", storage_path="/artifacts/model.pkl",
        file_size_bytes=50000, sha256_checksum="abc123",
        created_at=earlier,
    )
    art2 = Artifact(
        id=str(uuid.uuid4()), run_id=run2_id, experiment_id=exp1_id, dataset_id=ds1_id,
        artifact_type=ArtifactType.metrics_json, filename="metrics.json",
        mime_type="application/json", storage_path="/artifacts/metrics.json",
        file_size_bytes=1200, sha256_checksum="def456",
        created_at=now,
    )
    db_session.add_all([art1, art2])
    db_session.commit()

    return {
        "ds1_id": ds1_id, "ds2_id": ds2_id,
        "exp1_id": exp1_id, "exp2_id": exp2_id,
        "run1_id": run1_id, "run2_id": run2_id, "run3_id": run3_id,
    }


# ─── DashboardRepository: Empty DB ───────────────────────────────────────────

class TestDashboardRepositoryEmpty:
    def test_get_overview_returns_zeros(self, db_session):
        repo = DashboardRepository()
        result = repo.get_overview(db_session)
        assert result["total_datasets"] == 0
        assert result["total_experiments"] == 0
        assert result["total_runs"] == 0
        assert result["completed_runs"] == 0
        assert result["failed_runs"] == 0
        assert result["total_artifacts"] == 0
        assert result["models_stored"] == 0
        assert result["storage_used_bytes"] == 0
        assert result["success_rate"] == 0.0
        assert result["average_accuracy"] is None

    def test_get_activity_empty(self, db_session):
        repo = DashboardRepository()
        result = repo.get_activity(db_session, limit=20)
        assert result == []

    def test_get_recent_runs_empty(self, db_session):
        repo = DashboardRepository()
        result = repo.get_recent_runs(db_session, limit=10)
        assert result == []

    def test_get_quick_stats_empty(self, db_session):
        repo = DashboardRepository()
        result = repo.get_quick_stats(db_session)
        assert result["best_model_type"] is None
        assert result["best_experiment_id"] is None
        assert result["most_used_dataset_id"] is None
        assert result["latest_artifact_id"] is None


# ─── DashboardRepository: Populated DB ───────────────────────────────────────

class TestDashboardRepositoryPopulated:
    def test_get_overview_counts(self, db_session, seeded_db):
        repo = DashboardRepository()
        result = repo.get_overview(db_session)
        assert result["total_datasets"] == 2
        assert result["total_experiments"] == 2
        assert result["total_runs"] == 3
        assert result["completed_runs"] == 2
        assert result["failed_runs"] == 1
        assert result["total_artifacts"] == 2
        assert result["models_stored"] == 1
        assert result["storage_used_bytes"] == 51200

    def test_get_overview_accuracy(self, db_session, seeded_db):
        repo = DashboardRepository()
        result = repo.get_overview(db_session)
        # Average of 0.92 and 0.96
        assert result["average_accuracy"] is not None
        assert abs(result["average_accuracy"] - 0.94) < 0.01

    def test_get_overview_success_rate(self, db_session, seeded_db):
        repo = DashboardRepository()
        result = repo.get_overview(db_session)
        # 2 completed out of 3 total
        assert abs(result["success_rate"] - 2 / 3) < 0.01

    def test_get_activity_returns_events(self, db_session, seeded_db):
        repo = DashboardRepository()
        events = repo.get_activity(db_session, limit=50)
        assert len(events) > 0
        event_types = {e["event_type"] for e in events}
        assert "dataset_uploaded" in event_types
        assert "experiment_created" in event_types
        assert "run_completed" in event_types
        assert "artifact_generated" in event_types
        assert "metrics_persisted" in event_types

    def test_get_activity_ordered_newest_first(self, db_session, seeded_db):
        repo = DashboardRepository()
        events = repo.get_activity(db_session, limit=50)
        timestamps = [e["occurred_at"] for e in events]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_activity_limit_respected(self, db_session, seeded_db):
        repo = DashboardRepository()
        events = repo.get_activity(db_session, limit=3)
        assert len(events) <= 3

    def test_get_recent_runs_returns_data(self, db_session, seeded_db):
        repo = DashboardRepository()
        runs = repo.get_recent_runs(db_session, limit=10)
        assert len(runs) == 3

    def test_get_recent_runs_limit(self, db_session, seeded_db):
        repo = DashboardRepository()
        runs = repo.get_recent_runs(db_session, limit=2)
        assert len(runs) <= 2

    def test_get_recent_runs_have_required_fields(self, db_session, seeded_db):
        repo = DashboardRepository()
        runs = repo.get_recent_runs(db_session, limit=10)
        for run in runs:
            assert "run_id" in run
            assert "run_number" in run
            assert "experiment_name" in run
            assert "status" in run

    def test_get_quick_stats_best_model(self, db_session, seeded_db):
        repo = DashboardRepository()
        stats = repo.get_quick_stats(db_session)
        # random_forest has accuracy 0.96 vs logistic_regression 0.92
        assert stats["best_model_type"] == "random_forest"
        assert stats["best_model_accuracy"] is not None
        assert stats["best_model_accuracy"] > 0.9

    def test_get_quick_stats_best_experiment(self, db_session, seeded_db):
        repo = DashboardRepository()
        stats = repo.get_quick_stats(db_session)
        assert stats["best_experiment_id"] is not None
        assert stats["best_experiment_name"] is not None
        assert stats["best_experiment_accuracy"] == 0.9600

    def test_get_quick_stats_most_used_dataset(self, db_session, seeded_db):
        repo = DashboardRepository()
        stats = repo.get_quick_stats(db_session)
        # ds1 has 2 experiments, ds2 has 0
        assert stats["most_used_dataset_name"] == "Iris"
        assert stats["most_used_dataset_experiment_count"] == 2

    def test_get_quick_stats_latest_artifact(self, db_session, seeded_db):
        repo = DashboardRepository()
        stats = repo.get_quick_stats(db_session)
        assert stats["latest_artifact_id"] is not None
        # metrics.json was created at "now" (most recent)
        assert stats["latest_artifact_filename"] == "metrics.json"


# ─── DashboardService ─────────────────────────────────────────────────────────

class TestDashboardService:
    def test_get_overview_delegates(self, db_session, seeded_db):
        service = DashboardService()
        result = service.get_overview(db_session)
        assert "total_datasets" in result
        assert "total_runs" in result

    def test_get_activity_clamps_limit_high(self, db_session, seeded_db):
        """Limit above 100 should be clamped to 100."""
        service = DashboardService()
        events = service.get_activity(db_session, limit=999)
        assert len(events) <= 100

    def test_get_activity_clamps_limit_low(self, db_session, seeded_db):
        """Limit below 1 should be clamped to 1."""
        service = DashboardService()
        events = service.get_activity(db_session, limit=0)
        assert len(events) <= 1

    def test_get_recent_runs_clamps_limit(self, db_session, seeded_db):
        service = DashboardService()
        runs = service.get_recent_runs(db_session, limit=200)
        assert len(runs) <= 50

    def test_get_quick_stats_returns_dict(self, db_session, seeded_db):
        service = DashboardService()
        stats = service.get_quick_stats(db_session)
        assert isinstance(stats, dict)
        assert "best_model_type" in stats


# ─── DashboardRouter ──────────────────────────────────────────────────────────

class TestDashboardRouterEmpty:
    def test_overview_endpoint_empty(self, test_client):
        response = test_client.get("/api/v1/dashboard/overview")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert body["data"]["total_runs"] == 0
        assert body["data"]["total_datasets"] == 0

    def test_activity_endpoint_empty(self, test_client):
        response = test_client.get("/api/v1/dashboard/activity")
        assert response.status_code == 200
        body = response.json()
        assert body["data"] == []

    def test_recent_runs_endpoint_empty(self, test_client):
        response = test_client.get("/api/v1/dashboard/recent-runs")
        assert response.status_code == 200
        body = response.json()
        assert body["data"] == []

    def test_quick_stats_endpoint_empty(self, test_client):
        response = test_client.get("/api/v1/dashboard/quick-stats")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["best_model_type"] is None


class TestDashboardRouterPopulated:
    def test_overview_populated(self, test_client, seeded_db):
        response = test_client.get("/api/v1/dashboard/overview")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_datasets"] == 2
        assert data["total_experiments"] == 2
        assert data["total_runs"] == 3
        assert data["completed_runs"] == 2
        assert data["total_artifacts"] == 2
        assert data["average_accuracy"] is not None

    def test_activity_populated(self, test_client, seeded_db):
        response = test_client.get("/api/v1/dashboard/activity?limit=50")
        assert response.status_code == 200
        events = response.json()["data"]
        assert len(events) > 0
        # Verify ordering — first event should be most recent
        if len(events) >= 2:
            t0 = events[0]["occurred_at"]
            t1 = events[1]["occurred_at"]
            assert t0 >= t1

    def test_activity_limit_query_param(self, test_client, seeded_db):
        response = test_client.get("/api/v1/dashboard/activity?limit=2")
        assert response.status_code == 200
        events = response.json()["data"]
        assert len(events) <= 2

    def test_activity_invalid_limit(self, test_client, seeded_db):
        response = test_client.get("/api/v1/dashboard/activity?limit=0")
        assert response.status_code == 422  # FastAPI Query(ge=1) validation

    def test_recent_runs_populated(self, test_client, seeded_db):
        response = test_client.get("/api/v1/dashboard/recent-runs")
        assert response.status_code == 200
        runs = response.json()["data"]
        assert len(runs) == 3

    def test_recent_runs_limit_param(self, test_client, seeded_db):
        response = test_client.get("/api/v1/dashboard/recent-runs?limit=1")
        assert response.status_code == 200
        runs = response.json()["data"]
        assert len(runs) == 1

    def test_recent_runs_have_experiment_name(self, test_client, seeded_db):
        response = test_client.get("/api/v1/dashboard/recent-runs")
        runs = response.json()["data"]
        for run in runs:
            assert run["experiment_name"] is not None

    def test_quick_stats_populated(self, test_client, seeded_db):
        response = test_client.get("/api/v1/dashboard/quick-stats")
        assert response.status_code == 200
        stats = response.json()["data"]
        assert stats["best_model_type"] == "random_forest"
        assert stats["most_used_dataset_name"] == "Iris"
        assert stats["latest_artifact_filename"] == "metrics.json"

    def test_quick_stats_best_experiment_accuracy(self, test_client, seeded_db):
        response = test_client.get("/api/v1/dashboard/quick-stats")
        stats = response.json()["data"]
        assert stats["best_experiment_accuracy"] == 0.9600
