"""
test_artifact_storage_service.py — Unit tests for ArtifactStorageService.

Tests file I/O, SHA-256 checksums, model serialization, and cleanup.
No network or DB connections required.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import joblib
import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier

from app.services.artifact_storage_service import ArtifactStorageService, ArtifactStorageError


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def storage_service(tmp_path):
    """ArtifactStorageService with STORAGE_BASE_PATH pointing at tmp_path."""
    with patch("app.services.artifact_storage_service.settings") as mock_settings:
        mock_settings.STORAGE_BASE_PATH = str(tmp_path)
        yield ArtifactStorageService()


@pytest.fixture
def trained_model():
    """A minimal fitted RandomForestClassifier."""
    X = np.array([[1, 0], [0, 1], [1, 1], [0, 0]])
    y = np.array([0, 1, 0, 1])
    clf = RandomForestClassifier(n_estimators=2, random_state=42)
    clf.fit(X, y)
    return clf


RUN_ID = "test-run-uuid-1234"


# ── get_artifact_dir ───────────────────────────────────────────────────────────

def test_get_artifact_dir_creates_directory(storage_service, tmp_path):
    artifact_dir = storage_service.get_artifact_dir(RUN_ID)
    assert artifact_dir.exists()
    assert artifact_dir.is_dir()
    assert artifact_dir == tmp_path / "artifacts" / RUN_ID


# ── save_json ──────────────────────────────────────────────────────────────────

def test_save_json_creates_file(storage_service, tmp_path):
    data = {"accuracy": 0.95, "f1_score": 0.93}
    filename, path_str, size, checksum = storage_service.save_json(RUN_ID, "metrics.json", data)

    assert filename == "metrics.json"
    path = Path(path_str)
    assert path.exists()
    assert size > 0
    assert len(checksum) == 64  # SHA-256 hex digest

    loaded = json.loads(path.read_text())
    assert loaded["accuracy"] == 0.95


def test_save_json_checksum_is_deterministic(storage_service):
    data = {"key": "value"}
    _, _, _, checksum1 = storage_service.save_json(RUN_ID, "a.json", data)
    # Same data written again (overwrite same run would produce same hash)
    with patch.object(storage_service, "get_artifact_dir") as mock_dir:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            mock_dir.return_value = Path(td)
            _, _, _, checksum2 = storage_service.save_json("other-run", "a.json", data)
    assert checksum1 == checksum2


# ── save_model ─────────────────────────────────────────────────────────────────

def test_save_model_creates_joblib_file(storage_service, tmp_path, trained_model):
    filename, path_str, size, checksum = storage_service.save_model(RUN_ID, trained_model)

    assert filename == "model.joblib"
    path = Path(path_str)
    assert path.exists()
    assert size > 0
    assert len(checksum) == 64

    # Verify model can be reloaded
    loaded_model = joblib.load(path)
    predictions = loaded_model.predict(np.array([[1, 0]]))
    assert len(predictions) == 1


def test_save_model_raises_on_failure(storage_service):
    bad_estimator = object()  # not serializable with joblib normally
    # patch joblib.dump to fail
    with patch("app.services.artifact_storage_service.joblib.dump") as mock_dump:
        mock_dump.side_effect = Exception("serialization error")
        with pytest.raises(ArtifactStorageError, match="Failed to serialize model"):
            storage_service.save_model(RUN_ID, bad_estimator)


# ── SHA-256 checksum ──────────────────────────────────────────────────────────

def test_compute_sha256_returns_64_char_hex(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(b"hello world")
    checksum = ArtifactStorageService._compute_sha256(test_file)
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)


def test_compute_sha256_is_correct(tmp_path):
    import hashlib
    content = b"microflow artifact content"
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    actual = ArtifactStorageService._compute_sha256(test_file)
    assert actual == expected


# ── cleanup ────────────────────────────────────────────────────────────────────

def test_cleanup_removes_directory(storage_service, tmp_path):
    # Create the directory and a file
    artifact_dir = storage_service.get_artifact_dir(RUN_ID)
    (artifact_dir / "model.joblib").write_bytes(b"data")
    assert artifact_dir.exists()

    storage_service.cleanup_run_directory(RUN_ID)
    assert not artifact_dir.exists()


def test_cleanup_is_safe_if_dir_does_not_exist(storage_service):
    # Should not raise
    storage_service.cleanup_run_directory("non-existent-run-id")
