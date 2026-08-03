"""
test_execute_run.py — Integration tests for POST /api/v1/runs/{run_id}/execute.

Uses FastAPI dependency_overrides to inject mock services so no real DB or files
are needed during testing.
"""

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.models.experiment import Run, RunStatus
from app.routers.training import get_training_service, get_run_service
from app.services.training_service import TrainingService
from app.services.run_service import RunService


# ── Helpers ────────────────────────────────────────────────────────────────────


def make_run(
    *,
    run_id: str = "run-abc",
    status: RunStatus = RunStatus.completed,
    model_type: str = "random_forest",
) -> Run:
    run = MagicMock(spec=Run)
    run.id = run_id
    run.status = status
    run.model_type = model_type
    run.experiment_id = "exp-001"
    run.training_configuration = {}
    run.run_number = 1
    run.notes = None
    run.created_at = "2024-01-01T00:00:00Z"
    run.updated_at = "2024-01-01T00:00:00Z"
    return run


MOCK_METRICS: dict[str, Any] = {
    "accuracy": 0.90,
    "precision": 0.89,
    "recall": 0.91,
    "f1_score": 0.90,
    "roc_auc": 0.95,
    "confusion_matrix": [[45, 5], [4, 46]],
}


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestExecuteRunEndpoint:
    """Tests for POST /api/v1/runs/{run_id}/execute."""

    @pytest.fixture(autouse=True)
    def clear_overrides(self):
        """Ensure dependency overrides are cleaned up after each test."""
        yield
        app.dependency_overrides.clear()

    def _override_services(
        self,
        metrics: dict[str, Any] | None = None,
        execute_side_effect=None,
        run: Run | None = None,
    ) -> None:
        """Install dependency overrides on the FastAPI app."""
        mock_training = MagicMock(spec=TrainingService)
        if execute_side_effect is not None:
            mock_training.execute.side_effect = execute_side_effect
        else:
            mock_training.execute.return_value = metrics or MOCK_METRICS

        mock_run_service = MagicMock(spec=RunService)
        mock_run_service.get_by_id.return_value = run or make_run()

        app.dependency_overrides[get_training_service] = lambda: mock_training
        app.dependency_overrides[get_run_service] = lambda: mock_run_service

    def test_successful_execution_returns_200(self) -> None:
        self._override_services()
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.post(
            "/api/v1/runs/run-abc/execute",
            json={"target_column": "target"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["run_id"] == "run-abc"
        assert body["data"]["status"] == "completed"
        assert "metrics" in body["data"]
        assert body["data"]["metrics"]["accuracy"] == pytest.approx(0.90)

    def test_roc_auc_in_response_for_binary(self) -> None:
        self._override_services()
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.post(
            "/api/v1/runs/run-abc/execute",
            json={"target_column": "target"},
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["metrics"]["roc_auc"] == pytest.approx(0.95)

    def test_missing_target_column_returns_422(self) -> None:
        # No override needed — FastAPI validation rejects before reaching service
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/v1/runs/run-abc/execute", json={})
        assert resp.status_code == 422

    def test_run_not_found_returns_404(self) -> None:
        self._override_services(
            execute_side_effect=HTTPException(status_code=404, detail="Run not found")
        )
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/runs/nonexistent/execute",
            json={"target_column": "target"},
        )
        assert resp.status_code == 404

    def test_not_queued_run_returns_422(self) -> None:
        self._override_services(
            execute_side_effect=HTTPException(status_code=422, detail="Not in queued state")
        )
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/runs/run-abc/execute",
            json={"target_column": "target"},
        )
        assert resp.status_code == 422

    def test_training_error_returns_422(self) -> None:
        self._override_services(
            execute_side_effect=HTTPException(status_code=422, detail="Preprocessing failed")
        )
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/runs/run-abc/execute",
            json={"target_column": "target"},
        )
        assert resp.status_code == 422

    def test_confusion_matrix_is_list_of_lists(self) -> None:
        self._override_services()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/runs/run-abc/execute",
            json={"target_column": "target"},
        )
        cm = resp.json()["data"]["metrics"]["confusion_matrix"]
        assert isinstance(cm, list)
        assert all(isinstance(row, list) for row in cm)
