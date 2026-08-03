"""
test_artifacts_router.py — Integration-style tests for the Artifact Registry router.

Mocks all service calls — no DB or file system required.
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import pytest

from app.models.artifact import ArtifactType
from app.schemas.artifact import ArtifactRegistryStats


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_artifact(**kwargs):
    defaults = dict(
        id="art-001",
        run_id="run-001",
        experiment_id="exp-001",
        dataset_id="ds-001",
        artifact_type=ArtifactType.metrics_json,
        filename="metrics.json",
        mime_type="application/json",
        storage_path="/storage/artifacts/run-001/metrics.json",
        file_size_bytes=512,
        sha256_checksum="a" * 64,
        created_at=datetime(2026, 8, 3, 10, 0, 0, tzinfo=timezone.utc),
    )
    defaults.update(kwargs)
    art = MagicMock()
    for k, v in defaults.items():
        setattr(art, k, v)
    return art


def make_run_result(**kwargs):
    defaults = dict(
        id="rr-001",
        run_id="run-001",
        accuracy=0.95,
        precision=0.93,
        recall=0.91,
        f1_score=0.92,
        roc_auc=0.97,
        confusion_matrix=[[10, 1], [2, 12]],
        execution_time_seconds=1.42,
        started_at=datetime(2026, 8, 3, 10, 0, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 8, 3, 10, 0, 1, tzinfo=timezone.utc),
        model_type="random_forest",
        dataset_id="ds-001",
        training_config_snapshot=None,
        preprocessing_summary=None,
        created_at=datetime(2026, 8, 3, 10, 0, 1, tzinfo=timezone.utc),
    )
    defaults.update(kwargs)
    rr = MagicMock()
    for k, v in defaults.items():
        setattr(rr, k, v)
    return rr


# ── list_artifacts ─────────────────────────────────────────────────────────────

def test_list_artifacts_returns_items():
    from app.services.artifact_service import ArtifactService
    from app.repositories.artifact_repository import ArtifactRepository

    artifact_repo = MagicMock(spec=ArtifactRepository)
    artifact_repo.list_all.return_value = [make_artifact(), make_artifact(id="art-002")]

    service = ArtifactService(artifact_repo=artifact_repo)
    db = MagicMock()

    artifacts = service.list_all(db)
    assert len(artifacts) == 2


# ── get_artifact ───────────────────────────────────────────────────────────────

def test_get_artifact_returns_existing():
    from app.services.artifact_service import ArtifactService
    from app.repositories.artifact_repository import ArtifactRepository

    artifact_repo = MagicMock(spec=ArtifactRepository)
    artifact_repo.get_by_id.return_value = make_artifact()

    service = ArtifactService(artifact_repo=artifact_repo)
    db = MagicMock()

    artifact = service.get_by_id("art-001", db)
    assert artifact.id == "art-001"


def test_get_artifact_raises_404_for_missing():
    from fastapi import HTTPException
    from app.services.artifact_service import ArtifactService
    from app.repositories.artifact_repository import ArtifactRepository

    artifact_repo = MagicMock(spec=ArtifactRepository)
    artifact_repo.get_by_id.return_value = None

    service = ArtifactService(artifact_repo=artifact_repo)
    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        service.get_by_id("non-existent", db)
    assert exc_info.value.status_code == 404


# ── get_download_path ──────────────────────────────────────────────────────────

def test_get_download_path_raises_404_for_missing_file(tmp_path):
    from fastapi import HTTPException
    from app.services.artifact_service import ArtifactService
    from app.repositories.artifact_repository import ArtifactRepository

    artifact_repo = MagicMock(spec=ArtifactRepository)
    artifact = make_artifact(storage_path=str(tmp_path / "does_not_exist.json"))
    artifact_repo.get_by_id.return_value = artifact

    service = ArtifactService(artifact_repo=artifact_repo)
    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        service.get_download_path("art-001", db)
    assert exc_info.value.status_code == 404


def test_get_download_path_returns_valid_path(tmp_path):
    from pathlib import Path
    from app.services.artifact_service import ArtifactService
    from app.repositories.artifact_repository import ArtifactRepository

    # Create an actual file
    test_file = tmp_path / "metrics.json"
    test_file.write_text("{}", encoding="utf-8")

    artifact_repo = MagicMock(spec=ArtifactRepository)
    artifact_repo.get_by_id.return_value = make_artifact(storage_path=str(test_file))

    service = ArtifactService(artifact_repo=artifact_repo)
    db = MagicMock()

    artifact, path = service.get_download_path("art-001", db)
    assert path == test_file
    assert path.exists()


# ── registry stats ─────────────────────────────────────────────────────────────

def test_registry_stats_counts_correctly():
    from app.services.artifact_service import ArtifactService
    from app.repositories.artifact_repository import ArtifactRepository

    artifact_repo = MagicMock(spec=ArtifactRepository)
    artifact_repo.list_all.return_value = [
        make_artifact(artifact_type=ArtifactType.trained_model, file_size_bytes=1024),
        make_artifact(artifact_type=ArtifactType.metrics_json, file_size_bytes=256),
        make_artifact(artifact_type=ArtifactType.evaluation_json, file_size_bytes=512),
    ]
    artifact_repo.total_size_bytes.return_value = 1792

    service = ArtifactService(artifact_repo=artifact_repo)
    db = MagicMock()

    stats = service.get_registry_stats(db)
    assert stats.total_artifacts == 3
    assert stats.models_stored == 1
    assert stats.json_reports == 2
    assert stats.total_size_bytes == 1792


# ── run result service ─────────────────────────────────────────────────────────

def test_run_result_service_returns_none_if_not_found():
    from app.services.run_result_service import RunResultService
    from app.repositories.run_result_repository import RunResultRepository

    repo = MagicMock(spec=RunResultRepository)
    repo.get_by_run_id.return_value = None

    service = RunResultService(run_result_repo=repo)
    db = MagicMock()

    result = service.get_by_run_id("run-001", db)
    assert result is None


def test_run_result_service_returns_result():
    from app.services.run_result_service import RunResultService
    from app.repositories.run_result_repository import RunResultRepository

    repo = MagicMock(spec=RunResultRepository)
    repo.get_by_run_id.return_value = make_run_result()

    service = RunResultService(run_result_repo=repo)
    db = MagicMock()

    result = service.get_by_run_id("run-001", db)
    assert result.accuracy == 0.95
    assert result.f1_score == 0.92
