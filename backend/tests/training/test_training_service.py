"""
test_training_service.py — Unit tests for TrainingService.

Uses mocks for all repositories so no database is required.
"""

import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.experiment import Experiment, ExperimentStatus, Run, RunStatus
from app.services.training_service import TrainingService


# ── Factory helpers ────────────────────────────────────────────────────────────

DB = MagicMock()  # dummy session


def make_run(
    *,
    status: RunStatus = RunStatus.queued,
    model_type: str | None = "random_forest",
    training_configuration: dict[str, Any] | None = None,
) -> Run:
    run = MagicMock(spec=Run)
    run.id = "run-001"
    run.experiment_id = "exp-001"
    run.status = status
    run.model_type = model_type
    run.training_configuration = training_configuration or {}
    return run


def make_experiment(dataset_id: str = "ds-001") -> Experiment:
    exp = MagicMock(spec=Experiment)
    exp.id = "exp-001"
    exp.dataset_id = dataset_id
    return exp


def make_dataset(storage_path: str) -> Any:
    ds = MagicMock()
    ds.id = "ds-001"
    ds.storage_path = storage_path
    return ds


def make_service(
    run: Run | None = None,
    experiment: Experiment | None = None,
    dataset: Any = None,
) -> TrainingService:
    run_repo = MagicMock()
    experiment_repo = MagicMock()
    dataset_repo = MagicMock()

    run_repo.get_by_id.return_value = run
    run_repo.update.side_effect = lambda db, r, **kwargs: (
        setattr(r, list(kwargs.keys())[0], list(kwargs.values())[0]) or r
    )
    experiment_repo.get_by_id.return_value = experiment
    dataset_repo.get_by_id.return_value = dataset

    return TrainingService(
        run_repo=run_repo,
        experiment_repo=experiment_repo,
        dataset_repo=dataset_repo,
    )


@pytest.fixture()
def csv_path(tmp_path: Path) -> str:
    """Write a valid binary-class CSV and return its path."""
    content = textwrap.dedent("""\
        num_a,num_b,target
        1.0,2.0,0
        3.0,4.0,1
        5.0,6.0,0
        7.0,8.0,1
        9.0,10.0,0
        11.0,12.0,1
        13.0,14.0,0
        15.0,16.0,1
        17.0,18.0,0
        19.0,20.0,1
    """)
    p = tmp_path / "data.csv"
    p.write_text(content)
    return str(p)


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestTrainingServiceExecute:
    def test_raises_404_when_run_not_found(self) -> None:
        svc = make_service(run=None)
        with pytest.raises(HTTPException) as exc:
            svc.execute("missing", target_column="target", test_split=None, db=DB)
        assert exc.value.status_code == 404

    def test_raises_422_when_run_not_queued(self) -> None:
        run = make_run(status=RunStatus.completed)
        svc = make_service(run=run)
        with pytest.raises(HTTPException) as exc:
            svc.execute("run-001", target_column="target", test_split=None, db=DB)
        assert exc.value.status_code == 422

    def test_successful_pipeline_returns_metrics(self, csv_path: str) -> None:
        run = make_run()
        experiment = make_experiment()
        dataset = make_dataset(csv_path)
        svc = make_service(run=run, experiment=experiment, dataset=dataset)

        metrics = svc.execute("run-001", target_column="target", test_split=0.3, db=DB)

        assert "accuracy" in metrics
        assert "f1_score" in metrics
        assert 0.0 <= metrics["accuracy"] <= 1.0

    def test_run_marked_completed_on_success(self, csv_path: str) -> None:
        run = make_run()
        experiment = make_experiment()
        dataset = make_dataset(csv_path)
        svc = make_service(run=run, experiment=experiment, dataset=dataset)

        svc.execute("run-001", target_column="target", test_split=0.3, db=DB)

        # The last update call should have status=completed
        svc._run_repo.update.assert_called()
        last_call_kwargs = svc._run_repo.update.call_args_list[-1][1]
        assert last_call_kwargs.get("status") == RunStatus.completed

    def test_run_marked_failed_when_dataset_missing(self) -> None:
        run = make_run()
        experiment = make_experiment()
        svc = make_service(run=run, experiment=experiment, dataset=None)

        with pytest.raises(HTTPException) as exc:
            svc.execute("run-001", target_column="target", test_split=None, db=DB)
        assert exc.value.status_code == 404

        # run should be marked failed
        update_calls = svc._run_repo.update.call_args_list
        statuses = [call[1].get("status") for call in update_calls if "status" in call[1]]
        assert RunStatus.failed in statuses

    def test_run_marked_failed_when_loader_raises(self, tmp_path: Path) -> None:
        run = make_run()
        experiment = make_experiment()
        dataset = make_dataset("/nonexistent/path.csv")
        svc = make_service(run=run, experiment=experiment, dataset=dataset)

        with pytest.raises(HTTPException):
            svc.execute("run-001", target_column="target", test_split=None, db=DB)

        update_calls = svc._run_repo.update.call_args_list
        statuses = [call[1].get("status") for call in update_calls if "status" in call[1]]
        assert RunStatus.failed in statuses

    def test_run_transitions_through_running_before_completed(self, csv_path: str) -> None:
        run = make_run()
        experiment = make_experiment()
        dataset = make_dataset(csv_path)
        svc = make_service(run=run, experiment=experiment, dataset=dataset)

        svc.execute("run-001", target_column="target", test_split=0.3, db=DB)

        statuses = [
            call[1].get("status")
            for call in svc._run_repo.update.call_args_list
            if "status" in call[1]
        ]
        assert RunStatus.running in statuses
        assert RunStatus.completed in statuses
        # running must come before completed
        assert statuses.index(RunStatus.running) < statuses.index(RunStatus.completed)

    def test_test_split_from_config(self, csv_path: str) -> None:
        run = make_run(training_configuration={"test_split": 0.3})
        experiment = make_experiment()
        dataset = make_dataset(csv_path)
        svc = make_service(run=run, experiment=experiment, dataset=dataset)

        # test_split=None → should use config value
        metrics = svc.execute("run-001", target_column="target", test_split=None, db=DB)
        assert "accuracy" in metrics
