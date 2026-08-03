"""
Unit tests for ExperimentService.

All database and repository calls are fully mocked — no DB connection needed.
"""

from unittest.mock import MagicMock, patch
import pytest

from fastapi import HTTPException

from app.models.experiment import Experiment, ExperimentStatus
from app.models.dataset import Dataset
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.services.experiment_service import ExperimentService


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_experiment(**kwargs) -> Experiment:
    defaults = dict(
        id="exp-001",
        name="Test Experiment",
        dataset_id="ds-001",
        description=None,
        objective=None,
        default_configuration=None,
        tags=None,
        status=ExperimentStatus.draft,
    )
    defaults.update(kwargs)
    exp = MagicMock(spec=Experiment)
    for k, v in defaults.items():
        setattr(exp, k, v)
    return exp


def make_dataset(dataset_id: str = "ds-001") -> Dataset:
    ds = MagicMock(spec=Dataset)
    ds.id = dataset_id
    return ds


def make_service(
    experiments: list | None = None,
    dataset: Dataset | None = None,
) -> tuple[ExperimentService, MagicMock, MagicMock]:
    exp_repo = MagicMock(spec=ExperimentRepository)
    ds_repo = MagicMock(spec=DatasetRepository)

    exp_repo.list_all.return_value = experiments or []
    exp_repo.list_by_dataset.return_value = experiments or []
    ds_repo.get_by_id.return_value = dataset

    service = ExperimentService(experiment_repo=exp_repo, dataset_repo=ds_repo)
    return service, exp_repo, ds_repo


DB = MagicMock()  # shared fake db session


# ── Creation ───────────────────────────────────────────────────────────────────

class TestExperimentServiceCreate:
    def test_create_success(self):
        dataset = make_dataset()
        experiment = make_experiment()
        service, exp_repo, ds_repo = make_service(dataset=dataset)
        exp_repo.create.return_value = experiment

        result = service.create(
            name="Test Experiment",
            dataset_id="ds-001",
            description=None,
            objective=None,
            default_configuration=None,
            tags=None,
            db=DB,
        )

        ds_repo.get_by_id.assert_called_once_with("ds-001", DB)
        exp_repo.create.assert_called_once()
        assert result is experiment

    def test_create_fails_when_dataset_not_found(self):
        service, _, ds_repo = make_service(dataset=None)
        ds_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            service.create(
                name="X", dataset_id="missing", description=None,
                objective=None, default_configuration=None, tags=None, db=DB,
            )

        assert exc_info.value.status_code == 404

    def test_create_fails_on_duplicate_name_in_dataset(self):
        dataset = make_dataset()
        existing = make_experiment(id="exp-other", name="Same Name")
        service, exp_repo, _ = make_service(experiments=[existing], dataset=dataset)

        with pytest.raises(HTTPException) as exc_info:
            service.create(
                name="Same Name", dataset_id="ds-001", description=None,
                objective=None, default_configuration=None, tags=None, db=DB,
            )

        assert exc_info.value.status_code == 409

    def test_duplicate_name_check_ignores_own_experiment(self):
        """Updating an experiment's name to its current value should not raise."""
        dataset = make_dataset()
        existing = make_experiment(id="exp-001", name="My Name")
        service, exp_repo, _ = make_service(experiments=[existing], dataset=dataset)
        exp_repo.create.return_value = existing

        # Should not raise — same name but exclude_id matches
        service._assert_unique_name_in_dataset("My Name", "ds-001", exclude_id="exp-001", db=DB)


# ── Update ─────────────────────────────────────────────────────────────────────

class TestExperimentServiceUpdate:
    def test_update_description(self):
        experiment = make_experiment()
        service, exp_repo, _ = make_service(dataset=make_dataset())
        exp_repo.get_by_id.return_value = experiment
        exp_repo.update.return_value = experiment

        service.update("exp-001", updates={"description": "new desc"}, db=DB)

        exp_repo.update.assert_called_once_with(DB, experiment, description="new desc")

    def test_update_fails_when_not_found(self):
        service, exp_repo, _ = make_service()
        exp_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            service.update("missing", updates={}, db=DB)

        assert exc_info.value.status_code == 404


# ── Archive ────────────────────────────────────────────────────────────────────

class TestExperimentServiceArchive:
    def test_archive_active_experiment(self):
        experiment = make_experiment(status=ExperimentStatus.active)
        service, exp_repo, _ = make_service()
        exp_repo.get_by_id.return_value = experiment
        exp_repo.update.return_value = experiment

        service.archive("exp-001", db=DB)

        exp_repo.update.assert_called_once_with(DB, experiment, status=ExperimentStatus.archived)

    def test_archive_already_archived_raises_409(self):
        experiment = make_experiment(status=ExperimentStatus.archived)
        service, exp_repo, _ = make_service()
        exp_repo.get_by_id.return_value = experiment

        with pytest.raises(HTTPException) as exc_info:
            service.archive("exp-001", db=DB)

        assert exc_info.value.status_code == 409


# ── Delete ─────────────────────────────────────────────────────────────────────

class TestExperimentServiceDelete:
    def test_delete_draft_experiment(self):
        experiment = make_experiment(status=ExperimentStatus.draft)
        service, exp_repo, _ = make_service()
        exp_repo.get_by_id.return_value = experiment

        service.delete("exp-001", db=DB)

        exp_repo.delete.assert_called_once_with("exp-001", DB)

    def test_delete_active_experiment_raises_409(self):
        experiment = make_experiment(status=ExperimentStatus.active)
        service, exp_repo, _ = make_service()
        exp_repo.get_by_id.return_value = experiment

        with pytest.raises(HTTPException) as exc_info:
            service.delete("exp-001", db=DB)

        assert exc_info.value.status_code == 409
