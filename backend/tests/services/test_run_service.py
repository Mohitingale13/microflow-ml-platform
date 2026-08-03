"""
Unit tests for RunService.

All database and repository calls are fully mocked — no DB connection needed.
"""

from unittest.mock import MagicMock
import pytest

from fastapi import HTTPException

from app.models.experiment import Experiment, ExperimentStatus, Run, RunStatus
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.run_repository import RunRepository
from app.services.run_service import RunService


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_run(**kwargs) -> Run:
    defaults = dict(
        id="run-001",
        experiment_id="exp-001",
        run_number=1,
        model_type=None,
        training_configuration=None,
        notes=None,
        status=RunStatus.draft,
    )
    defaults.update(kwargs)
    run = MagicMock(spec=Run)
    for k, v in defaults.items():
        setattr(run, k, v)
    return run


def make_experiment(**kwargs) -> Experiment:
    defaults = dict(
        id="exp-001",
        name="My Experiment",
        dataset_id="ds-001",
        status=ExperimentStatus.active,
        default_configuration=None,
    )
    defaults.update(kwargs)
    exp = MagicMock(spec=Experiment)
    for k, v in defaults.items():
        setattr(exp, k, v)
    return exp


def make_service(
    experiment: Experiment | None = None,
    runs: list | None = None,
    next_run_number: int = 1,
) -> tuple[RunService, MagicMock, MagicMock]:
    run_repo = MagicMock(spec=RunRepository)
    exp_repo = MagicMock(spec=ExperimentRepository)

    exp_repo.get_by_id.return_value = experiment
    run_repo.list_by_experiment.return_value = runs or []
    run_repo.get_next_run_number.return_value = next_run_number

    service = RunService(run_repo=run_repo, experiment_repo=exp_repo)
    return service, run_repo, exp_repo


DB = MagicMock()


# ── Creation ───────────────────────────────────────────────────────────────────

class TestRunServiceCreate:
    def test_create_assigns_sequential_run_number(self):
        experiment = make_experiment()
        run = make_run(run_number=3)
        service, run_repo, _ = make_service(experiment=experiment, next_run_number=3)
        run_repo.create.return_value = run

        result = service.create(
            experiment_id="exp-001",
            model_type=None,
            training_configuration=None,
            notes=None,
            db=DB,
        )

        run_repo.get_next_run_number.assert_called_once_with("exp-001", DB)
        run_repo.create.assert_called_once()
        call_kwargs = run_repo.create.call_args[1]
        assert call_kwargs["run_number"] == 3

    def test_create_fails_when_experiment_not_found(self):
        service, _, _ = make_service(experiment=None)

        with pytest.raises(HTTPException) as exc_info:
            service.create(
                experiment_id="missing",
                model_type=None,
                training_configuration=None,
                notes=None,
                db=DB,
            )

        assert exc_info.value.status_code == 404

    def test_create_inherits_experiment_default_configuration(self):
        experiment = make_experiment(
            default_configuration={"model": "random_forest", "n_estimators": 100}
        )
        run = make_run(
            training_configuration={"model": "random_forest", "n_estimators": 100}
        )
        service, run_repo, _ = make_service(experiment=experiment)
        run_repo.create.return_value = run

        service.create(
            experiment_id="exp-001",
            model_type=None,
            training_configuration=None,
            notes=None,
            db=DB,
        )

        call_kwargs = run_repo.create.call_args[1]
        assert call_kwargs["training_configuration"] == {
            "model": "random_forest",
            "n_estimators": 100,
        }

    def test_create_run_overrides_merge_on_top_of_defaults(self):
        experiment = make_experiment(
            default_configuration={"model": "logistic_regression", "C": 1.0, "max_iter": 100}
        )
        run = make_run()
        service, run_repo, _ = make_service(experiment=experiment)
        run_repo.create.return_value = run

        service.create(
            experiment_id="exp-001",
            model_type=None,
            training_configuration={"C": 0.5},  # override one field
            notes=None,
            db=DB,
        )

        call_kwargs = run_repo.create.call_args[1]
        merged = call_kwargs["training_configuration"]
        # Base values present
        assert merged["model"] == "logistic_regression"
        assert merged["max_iter"] == 100
        # Override applied
        assert merged["C"] == 0.5

    def test_create_run_configuration_merge_seed_and_test_split(self):
        experiment = make_experiment(
            default_configuration={"seed": 42, "test_split": 0.2}
        )
        run = make_run()
        service, run_repo, _ = make_service(experiment=experiment)
        run_repo.create.return_value = run

        service.create(
            experiment_id="exp-001",
            model_type=None,
            training_configuration={"test_split": 0.3},
            notes=None,
            db=DB,
        )

        call_kwargs = run_repo.create.call_args[1]
        merged = call_kwargs["training_configuration"]
        assert merged == {"seed": 42, "test_split": 0.3}

    def test_create_does_not_mutate_experiment_defaults(self):
        original_config = {"model": "xgboost", "n_estimators": 50}
        experiment = make_experiment(default_configuration=original_config.copy())
        run = make_run()
        service, run_repo, _ = make_service(experiment=experiment)
        run_repo.create.return_value = run

        service.create(
            experiment_id="exp-001",
            model_type=None,
            training_configuration={"n_estimators": 200},
            notes=None,
            db=DB,
        )

        # Original config on experiment should be unchanged
        assert experiment.default_configuration is not None
        assert experiment.default_configuration["n_estimators"] == 50


# ── State Machine ──────────────────────────────────────────────────────────────

class TestRunStateMachine:
    def test_queue_from_draft(self):
        run = make_run(status=RunStatus.draft)
        service, run_repo, _ = make_service()
        run_repo.get_by_id.return_value = run
        run_repo.update.return_value = run

        service.queue("run-001", db=DB)

        run_repo.update.assert_called_once_with(DB, run, status=RunStatus.queued)

    def test_cancel_from_draft(self):
        run = make_run(status=RunStatus.draft)
        service, run_repo, _ = make_service()
        run_repo.get_by_id.return_value = run
        run_repo.update.return_value = run

        service.cancel("run-001", db=DB)

        run_repo.update.assert_called_once_with(DB, run, status=RunStatus.cancelled)

    def test_cancel_from_queued(self):
        run = make_run(status=RunStatus.queued)
        service, run_repo, _ = make_service()
        run_repo.get_by_id.return_value = run
        run_repo.update.return_value = run

        service.cancel("run-001", db=DB)

        run_repo.update.assert_called_once_with(DB, run, status=RunStatus.cancelled)

    @pytest.mark.parametrize("invalid_current", [
        RunStatus.completed,
        RunStatus.failed,
        RunStatus.cancelled,
    ])
    def test_cannot_queue_from_terminal_status(self, invalid_current):
        run = make_run(status=invalid_current)
        service, run_repo, _ = make_service()
        run_repo.get_by_id.return_value = run

        with pytest.raises(HTTPException) as exc_info:
            service.queue("run-001", db=DB)

        assert exc_info.value.status_code == 422

    def test_cannot_transition_from_completed(self):
        run = make_run(status=RunStatus.completed)
        service, run_repo, _ = make_service()
        run_repo.get_by_id.return_value = run

        with pytest.raises(HTTPException) as exc_info:
            service.cancel("run-001", db=DB)

        assert exc_info.value.status_code == 422

    def test_cannot_transition_from_failed(self):
        run = make_run(status=RunStatus.failed)
        service, run_repo, _ = make_service()
        run_repo.get_by_id.return_value = run

        with pytest.raises(HTTPException) as exc_info:
            service.cancel("run-001", db=DB)

        assert exc_info.value.status_code == 422

    def test_running_can_complete(self):
        run = make_run(status=RunStatus.running)
        service, run_repo, exp_repo = make_service()
        run_repo.get_by_id.return_value = run
        run_repo.update.return_value = run

        # Simulate Training Engine calling update with completed status
        service.update(
            "run-001",
            updates={"status": RunStatus.completed},
            db=DB,
        )

        run_repo.update.assert_called()

    def test_running_can_fail(self):
        run = make_run(status=RunStatus.running)
        service, run_repo, exp_repo = make_service()
        run_repo.get_by_id.return_value = run
        run_repo.update.return_value = run

        service.update(
            "run-001",
            updates={"status": RunStatus.failed},
            db=DB,
        )

        run_repo.update.assert_called()


# ── Configuration Merge ────────────────────────────────────────────────────────

class TestRunServiceMergeConfiguration:
    def test_none_plus_none_returns_none(self):
        result = RunService._merge_configuration(None, None)
        assert result is None

    def test_base_only(self):
        result = RunService._merge_configuration({"a": 1}, None)
        assert result == {"a": 1}

    def test_override_only(self):
        result = RunService._merge_configuration(None, {"b": 2})
        assert result == {"b": 2}

    def test_override_wins_on_conflict(self):
        result = RunService._merge_configuration({"a": 1, "b": 2}, {"b": 99, "c": 3})
        assert result == {"a": 1, "b": 99, "c": 3}

    def test_returns_new_dict(self):
        base = {"a": 1}
        override = {"b": 2}
        result = RunService._merge_configuration(base, override)
        assert result is not base
        assert result is not override


# ── Delete guard ───────────────────────────────────────────────────────────────

class TestRunServiceDelete:
    def test_delete_completed_run_succeeds(self):
        run = make_run(status=RunStatus.completed)
        service, run_repo, _ = make_service()
        run_repo.get_by_id.return_value = run

        service.delete("run-001", db=DB)

        run_repo.delete.assert_called_once_with("run-001", DB)

    @pytest.mark.parametrize("blocked_status", [RunStatus.running, RunStatus.queued])
    def test_delete_active_run_raises_409(self, blocked_status):
        run = make_run(status=blocked_status)
        service, run_repo, _ = make_service()
        run_repo.get_by_id.return_value = run

        with pytest.raises(HTTPException) as exc_info:
            service.delete("run-001", db=DB)

        assert exc_info.value.status_code == 409


# ── Run numbering ──────────────────────────────────────────────────────────────

class TestRunNumbering:
    def test_first_run_gets_number_one(self):
        experiment = make_experiment()
        service, run_repo, _ = make_service(experiment=experiment, next_run_number=1)
        run = make_run(run_number=1)
        run_repo.create.return_value = run

        service.create(
            experiment_id="exp-001",
            model_type=None,
            training_configuration=None,
            notes=None,
            db=DB,
        )

        call_kwargs = run_repo.create.call_args[1]
        assert call_kwargs["run_number"] == 1

    def test_subsequent_run_increments(self):
        experiment = make_experiment()
        service, run_repo, _ = make_service(experiment=experiment, next_run_number=5)
        run = make_run(run_number=5)
        run_repo.create.return_value = run

        service.create(
            experiment_id="exp-001",
            model_type=None,
            training_configuration=None,
            notes=None,
            db=DB,
        )

        call_kwargs = run_repo.create.call_args[1]
        assert call_kwargs["run_number"] == 5
