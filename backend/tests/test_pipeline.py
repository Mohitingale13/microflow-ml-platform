"""
test_pipeline.py — Integration tests for the Pipeline Visualization module.

Tests cover:
  - PipelineRepository: empty database, populated database
  - PipelineService: graph transformation, timeline generation, lineage building
  - PipelineRouter: overview, runs list, single run graph, lineage

All tests use in-memory SQLite with pre-seeded data.
"""

import uuid
from datetime import datetime, timezone

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
from app.repositories.pipeline_repository import PipelineRepository
from app.services.pipeline_service import PipelineService


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
    """Seed a complete pipeline: Dataset → Experiment → Run (completed) → RunResult → Artifact."""
    now = datetime.now(timezone.utc)
    ds_id = "ds-pipeline-1"
    exp_id = "exp-pipeline-1"
    run_id = "run-pipeline-1"
    result_id = "result-pipeline-1"
    artifact_id = "artifact-pipeline-1"

    dataset = Dataset(
        id=ds_id,
        name="Iris Dataset",
        original_filename="iris.csv",
        storage_path="/data/iris.csv",
        file_hash="pipeline_hash_abc",
        file_size_bytes=5000,
        row_count=150,
        column_count=5,
        column_names=["sepal_length", "sepal_width", "petal_length", "petal_width", "variety"],
    )
    db_session.add(dataset)
    db_session.flush()

    experiment = Experiment(
        id=exp_id,
        name="Iris Classification",
        description="Test experiment",
        dataset_id=ds_id,
        status=ExperimentStatus.active,
        created_at=now,
        updated_at=now,
    )
    db_session.add(experiment)
    db_session.flush()

    run = Run(
        id=run_id,
        experiment_id=exp_id,
        run_number=1,
        model_type="random_forest",
        status=RunStatus.completed,
        created_at=now,
        updated_at=now,
    )
    db_session.add(run)
    db_session.flush()

    result = RunResult(
        id=result_id,
        run_id=run_id,
        accuracy=0.9333,
        precision=0.9350,
        recall=0.9333,
        f1_score=0.9330,
        roc_auc=0.98,
        confusion_matrix=[[10, 0, 0], [0, 9, 1], [0, 0, 10]],
        execution_time_seconds=2.54,
        model_type="random_forest",
        dataset_id=ds_id,
        started_at=now,
        completed_at=now,
        created_at=now,
    )
    db_session.add(result)

    artifact = Artifact(
        id=artifact_id,
        run_id=run_id,
        experiment_id=exp_id,
        dataset_id=ds_id,
        artifact_type=ArtifactType.metrics_json,
        filename="metrics.json",
        mime_type="application/json",
        storage_path="/artifacts/metrics.json",
        file_size_bytes=512,
        sha256_checksum="def456",
        created_at=now,
    )
    db_session.add(artifact)
    db_session.commit()

    return {
        "dataset_id": ds_id,
        "experiment_id": exp_id,
        "run_id": run_id,
        "result_id": result_id,
        "artifact_id": artifact_id,
    }


# ─── PipelineRepository Tests ─────────────────────────────────────────────────

class TestPipelineRepositoryEmpty:
    def test_get_overview_empty_database(self, db_session):
        repo = PipelineRepository()
        overview = repo.get_overview(db_session)
        assert overview["total_pipelines"] == 0
        assert overview["completed"] == 0
        assert overview["running"] == 0
        assert overview["failed"] == 0
        assert overview["total_artifacts_produced"] == 0
        assert overview["success_rate"] == 0.0
        assert overview["average_duration_seconds"] is None

    def test_get_runs_empty_database(self, db_session):
        repo = PipelineRepository()
        runs = repo.get_runs_with_context(db_session)
        assert runs == []

    def test_get_lineage_empty_database(self, db_session):
        repo = PipelineRepository()
        lineage = repo.get_lineage_data(db_session)
        assert lineage == []

    def test_get_run_graph_nonexistent(self, db_session):
        repo = PipelineRepository()
        result = repo.get_run_graph_data(str(uuid.uuid4()), db_session)
        assert result is None


class TestPipelineRepositoryPopulated:
    def test_get_overview_populated(self, db_session, seeded_db):
        repo = PipelineRepository()
        overview = repo.get_overview(db_session)
        assert overview["completed"] == 1
        assert overview["total_artifacts_produced"] == 1
        assert overview["average_duration_seconds"] == 2.54

    def test_get_runs_returns_data(self, db_session, seeded_db):
        repo = PipelineRepository()
        runs = repo.get_runs_with_context(db_session)
        assert len(runs) == 1
        run = runs[0]
        assert run["run_id"] == seeded_db["run_id"]
        assert run["experiment_name"] == "Iris Classification"
        assert run["dataset_name"] == "Iris Dataset"
        assert run["model"] == "random_forest"
        assert run["status"] == "completed"
        assert run["artifact_count"] == 1
        assert run["accuracy"] == 0.9333

    def test_get_runs_filter_by_status_completed(self, db_session, seeded_db):
        repo = PipelineRepository()
        runs = repo.get_runs_with_context(db_session, status="completed")
        assert len(runs) == 1

    def test_get_runs_filter_by_status_failed_returns_empty(self, db_session, seeded_db):
        repo = PipelineRepository()
        runs = repo.get_runs_with_context(db_session, status="failed")
        assert len(runs) == 0

    def test_get_runs_filter_by_dataset(self, db_session, seeded_db):
        repo = PipelineRepository()
        runs = repo.get_runs_with_context(db_session, dataset_id=seeded_db["dataset_id"])
        assert len(runs) == 1

    def test_get_runs_filter_by_experiment(self, db_session, seeded_db):
        repo = PipelineRepository()
        runs = repo.get_runs_with_context(db_session, experiment_id=seeded_db["experiment_id"])
        assert len(runs) == 1

    def test_get_run_graph_data(self, db_session, seeded_db):
        repo = PipelineRepository()
        raw = repo.get_run_graph_data(seeded_db["run_id"], db_session)
        assert raw is not None
        assert raw["run"].id == seeded_db["run_id"]
        assert raw["experiment"].id == seeded_db["experiment_id"]
        assert raw["dataset"].id == seeded_db["dataset_id"]
        assert raw["result"].run_id == seeded_db["run_id"]
        assert len(raw["artifacts"]) == 1

    def test_get_lineage_structure(self, db_session, seeded_db):
        repo = PipelineRepository()
        lineage = repo.get_lineage_data(db_session)
        assert len(lineage) == 1
        ds = lineage[0]
        assert ds["dataset"].name == "Iris Dataset"
        assert ds["total_experiments"] == 1
        assert ds["total_runs"] == 1
        assert len(ds["experiments"]) == 1
        exp = ds["experiments"][0]
        assert exp["experiment"].name == "Iris Classification"
        assert len(exp["runs"]) == 1
        run = exp["runs"][0]
        assert len(run["artifacts"]) == 1


# ─── PipelineService Tests ────────────────────────────────────────────────────

class TestPipelineService:
    def test_get_overview(self, db_session, seeded_db):
        service = PipelineService()
        overview = service.get_overview(db_session)
        assert overview["completed"] == 1
        assert isinstance(overview["success_rate"], float)

    def test_get_runs(self, db_session, seeded_db):
        service = PipelineService()
        runs = service.get_runs(db_session)
        assert len(runs) == 1
        assert runs[0]["status"] == "completed"

    def test_pipeline_graph_returns_correct_structure(self, db_session, seeded_db):
        service = PipelineService()
        result = service.get_pipeline_graph(seeded_db["run_id"], db_session)
        assert result is not None
        graph = result["graph"]
        assert graph["run_id"] == seeded_db["run_id"]
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) == 8   # 8 stages
        assert len(graph["edges"]) == 7   # 7 connections

    def test_pipeline_graph_completed_run_all_nodes_completed(self, db_session, seeded_db):
        service = PipelineService()
        result = service.get_pipeline_graph(seeded_db["run_id"], db_session)
        graph = result["graph"]
        node_statuses = {n["id"]: n["status"] for n in graph["nodes"]}
        assert node_statuses["dataset"] == "completed"
        assert node_statuses["experiment"] == "completed"
        assert node_statuses["run"] == "completed"
        assert node_statuses["training"] == "completed"
        assert node_statuses["evaluation"] == "completed"
        assert node_statuses["completed"] == "completed"

    def test_pipeline_graph_nodes_have_required_fields(self, db_session, seeded_db):
        service = PipelineService()
        result = service.get_pipeline_graph(seeded_db["run_id"], db_session)
        for node in result["graph"]["nodes"]:
            assert "id" in node
            assert "label" in node
            assert "status" in node
            assert "icon" in node
            assert "stage_type" in node

    def test_pipeline_graph_edges_connect_adjacent_stages(self, db_session, seeded_db):
        service = PipelineService()
        result = service.get_pipeline_graph(seeded_db["run_id"], db_session)
        edges = result["graph"]["edges"]
        stage_ids = [s["id"] for s in PipelineService.STAGES]
        for i, edge in enumerate(edges):
            assert edge["source"] == stage_ids[i]
            assert edge["target"] == stage_ids[i + 1]

    def test_timeline_has_events(self, db_session, seeded_db):
        service = PipelineService()
        result = service.get_pipeline_graph(seeded_db["run_id"], db_session)
        timeline = result["timeline"]
        assert "events" in timeline
        assert len(timeline["events"]) > 0
        for event in timeline["events"]:
            assert "order" in event
            assert "event" in event
            assert "status" in event
            assert "stage_type" in event

    def test_timeline_has_duration_for_completed_run(self, db_session, seeded_db):
        service = PipelineService()
        result = service.get_pipeline_graph(seeded_db["run_id"], db_session)
        assert result["timeline"]["total_duration_seconds"] == 2.54

    def test_nonexistent_run_returns_none(self, db_session):
        service = PipelineService()
        result = service.get_pipeline_graph(str(uuid.uuid4()), db_session)
        assert result is None

    def test_get_lineage_returns_list(self, db_session, seeded_db):
        service = PipelineService()
        lineage = service.get_lineage(db_session)
        assert isinstance(lineage, list)
        assert len(lineage) == 1
        assert "dataset_id" in lineage[0]
        assert "experiments" in lineage[0]


# ─── PipelineRouter Tests ─────────────────────────────────────────────────────

class TestPipelineRouter:
    def test_overview_endpoint_empty(self, test_client):
        response = test_client.get("/api/v1/pipeline/overview")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert body["data"]["total_pipelines"] == 0

    def test_runs_endpoint_empty(self, test_client):
        response = test_client.get("/api/v1/pipeline/runs")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert body["data"] == []

    def test_lineage_endpoint_empty(self, test_client):
        response = test_client.get("/api/v1/pipeline/lineage")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert body["data"] == []

    def test_graph_endpoint_not_found(self, test_client):
        response = test_client.get(f"/api/v1/pipeline/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_overview_populated(self, test_client, seeded_db):
        response = test_client.get("/api/v1/pipeline/overview")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["completed"] == 1
        assert data["total_artifacts_produced"] == 1

    def test_runs_populated(self, test_client, seeded_db):
        response = test_client.get("/api/v1/pipeline/runs")
        assert response.status_code == 200
        runs = response.json()["data"]
        assert len(runs) == 1
        assert runs[0]["status"] == "completed"
        assert runs[0]["model"] == "random_forest"

    def test_runs_filter_by_status_completed(self, test_client, seeded_db):
        response = test_client.get("/api/v1/pipeline/runs?status=completed")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1

    def test_runs_filter_by_status_failed_empty(self, test_client, seeded_db):
        response = test_client.get("/api/v1/pipeline/runs?status=failed")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 0

    def test_graph_populated(self, test_client, seeded_db):
        run_id = seeded_db["run_id"]
        response = test_client.get(f"/api/v1/pipeline/{run_id}")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "timeline" in body
        assert body["data"]["run_id"] == run_id
        assert len(body["data"]["nodes"]) == 8
        assert len(body["data"]["edges"]) == 7
        assert len(body["timeline"]["events"]) > 0

    def test_lineage_populated(self, test_client, seeded_db):
        response = test_client.get("/api/v1/pipeline/lineage")
        assert response.status_code == 200
        lineage = response.json()["data"]
        assert len(lineage) == 1
        assert lineage[0]["dataset_name"] == "Iris Dataset"
        assert lineage[0]["total_experiments"] == 1
        assert len(lineage[0]["experiments"]) == 1
