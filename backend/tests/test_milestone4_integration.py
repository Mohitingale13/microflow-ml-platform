"""
test_milestone4_integration.py — Complete integration test for Milestone 4:
  1. Creates dataset, experiment, run.
  2. Queues and executes run with TrainingService.
  3. Verifies RunResult is persisted in DB with metrics and confusion matrix.
  4. Verifies 6 Artifacts are saved on disk and registered in DB.
  5. Verifies GET /api/v1/runs/{id}/result returns persisted result.
  6. Verifies GET /api/v1/runs/{id}/artifacts returns all 6 artifacts.
  7. Verifies GET /api/v1/artifacts lists all artifacts with stats.
  8. Verifies GET /api/v1/artifacts/{id}/download downloads the actual file with matching checksum.
"""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models.artifact import Artifact, ArtifactType, RunResult
from app.models.dataset import Dataset
from app.models.experiment import Experiment, Run, RunStatus
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.run_repository import RunRepository
from app.repositories.run_result_repository import RunResultRepository
from app.services.artifact_service import ArtifactService
from app.services.artifact_storage_service import ArtifactStorageService
from app.services.run_result_service import RunResultService
from app.services.training_service import TrainingService


from sqlalchemy.pool import StaticPool

@pytest.fixture
def test_env(tmp_path):
    # In-memory SQLite with StaticPool so all connections share the same database
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Create dummy dataset CSV
    df = pd.DataFrame({
        "feature_1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        "feature_2": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
        "target": ["class_a", "class_a", "class_a", "class_a", "class_a", "class_b", "class_b", "class_b", "class_b", "class_b"],
    })
    csv_path = tmp_path / "test_data.csv"
    df.to_csv(csv_path, index=False)

    with patch("app.services.artifact_storage_service.settings") as mock_settings:
        mock_settings.STORAGE_BASE_PATH = str(tmp_path)
        client = TestClient(app)
        yield {
            "db_session": TestingSessionLocal,
            "tmp_path": tmp_path,
            "csv_path": str(csv_path),
            "client": client,
        }

    app.dependency_overrides.clear()


def test_milestone4_complete_lifecycle(test_env):
    Session = test_env["db_session"]
    db = Session()
    client = test_env["client"]
    tmp_path = test_env["tmp_path"]

    # 1. Create dataset
    dataset = Dataset(
        id="ds-test-1",
        name="Test Dataset",
        storage_path=test_env["csv_path"],
        original_filename="test_data.csv",
        file_hash="dummyhash1234",
        file_size_bytes=100,
        row_count=10,
        column_count=3,
        column_names=["feature_1", "feature_2", "target"],
    )
    db.add(dataset)

    # 2. Create experiment
    experiment = Experiment(
        id="exp-test-1",
        name="Test Experiment",
        dataset_id=dataset.id,
        default_configuration={"test_split": 0.2, "random_state": 42},
    )
    db.add(experiment)

    # 3. Create run
    run = Run(
        id="run-test-1",
        experiment_id=experiment.id,
        run_number=1,
        status=RunStatus.queued,
        model_type="random_forest",
        training_configuration={"test_split": 0.2, "random_state": 42, "n_estimators": 5},
    )
    db.add(run)
    db.commit()

    # 4. Execute training pipeline via TrainingService
    training_service = TrainingService(
        run_repo=RunRepository(),
        experiment_repo=ExperimentRepository(),
        dataset_repo=DatasetRepository(),
        run_result_repo=RunResultRepository(),
        artifact_repo=ArtifactRepository(),
        artifact_storage=ArtifactStorageService(),
    )

    metrics = training_service.execute(
        run_id=run.id,
        target_column="target",
        test_split=0.2,
        db=db,
    )

    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "confusion_matrix" in metrics

    # 5. Check run status is now completed
    db.refresh(run)
    assert run.status == RunStatus.completed

    # 6. Check RunResult is persisted in DB
    run_result = RunResultRepository().get_by_run_id(run.id, db)
    assert run_result is not None
    assert run_result.accuracy == metrics["accuracy"]
    assert run_result.f1_score == metrics["f1_score"]
    assert run_result.confusion_matrix == metrics["confusion_matrix"]
    assert run_result.model_type == "random_forest"
    assert run_result.dataset_id == dataset.id
    assert run_result.completed_at is not None

    # 7. Check 6 Artifacts registered in DB and stored on disk
    artifacts = ArtifactRepository().list_by_run(run.id, db)
    assert len(artifacts) >= 6
    artifact_types = {a.artifact_type for a in artifacts}
    assert {
        ArtifactType.trained_model,
        ArtifactType.metrics_json,
        ArtifactType.evaluation_json,
        ArtifactType.confusion_matrix_json,
        ArtifactType.configuration_json,
        ArtifactType.preprocessing_json,
    }.issubset(artifact_types)

    # Verify each artifact exists on disk with exact checksum
    for a in artifacts:
        p = Path(a.storage_path)
        assert p.exists()
        assert p.stat().st_size == a.file_size_bytes
        content = p.read_bytes()
        assert hashlib.sha256(content).hexdigest() == a.sha256_checksum

    # 8. Test API endpoints
    # GET /api/v1/runs/{id}/result
    resp = client.get(f"/api/v1/runs/{run.id}/result")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["run_id"] == run.id
    assert data["accuracy"] == metrics["accuracy"]

    # GET /api/v1/runs/{id}/artifacts
    resp = client.get(f"/api/v1/runs/{run.id}/artifacts")
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) >= 6

    # GET /api/v1/artifacts
    resp = client.get("/api/v1/artifacts")
    assert resp.status_code == 200
    all_items = resp.json()["data"]
    assert len(all_items) >= 6

    # GET /api/v1/artifacts/stats
    resp = client.get("/api/v1/artifacts/stats")
    assert resp.status_code == 200
    stats = resp.json()["data"]
    assert stats["total_artifacts"] >= 6
    assert stats["models_stored"] >= 1
    assert stats["json_reports"] >= 5
    assert stats["total_size_bytes"] > 0

    # GET /api/v1/artifacts/{id}/download
    model_artifact = next(a for a in artifacts if a.artifact_type == ArtifactType.trained_model)
    resp = client.get(f"/api/v1/artifacts/{model_artifact.id}/download")
    assert resp.status_code == 200
    assert len(resp.content) == model_artifact.file_size_bytes
    assert hashlib.sha256(resp.content).hexdigest() == model_artifact.sha256_checksum

    db.close()
