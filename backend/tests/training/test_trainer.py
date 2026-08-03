"""
test_trainer.py — Unit tests for app/training/trainer.py
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from app.training.trainer import TrainerError, train_model


# ── Helpers ────────────────────────────────────────────────────────────────────


def make_binary_data(n: int = 80):
    rng = np.random.default_rng(0)
    X = pd.DataFrame({"a": rng.uniform(0, 1, n), "b": rng.uniform(0, 1, n)})
    y = pd.Series(rng.integers(0, 2, n), name="target")
    return X, y


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestTrainModel:
    def test_returns_fitted_estimator(self) -> None:
        X, y = make_binary_data()
        est = RandomForestClassifier(n_estimators=10, random_state=0)
        fitted = train_model(est, X, y)
        # sklearn sets estimators_ after fitting
        assert hasattr(fitted, "estimators_")

    def test_fitted_estimator_can_predict(self) -> None:
        X, y = make_binary_data()
        est = train_model(RandomForestClassifier(n_estimators=10, random_state=0), X, y)
        preds = est.predict(X)
        assert len(preds) == len(X)

    def test_logistic_regression_fits(self) -> None:
        X, y = make_binary_data()
        est = train_model(LogisticRegression(max_iter=500), X, y)
        assert hasattr(est, "coef_")

    def test_raises_on_empty_X(self) -> None:
        X = pd.DataFrame({"a": [], "b": []})
        y = pd.Series([], dtype=int, name="target")
        with pytest.raises(TrainerError, match="empty"):
            train_model(RandomForestClassifier(), X, y)

    def test_returns_same_estimator_instance(self) -> None:
        X, y = make_binary_data()
        est = RandomForestClassifier(n_estimators=10, random_state=0)
        result = train_model(est, X, y)
        assert result is est
