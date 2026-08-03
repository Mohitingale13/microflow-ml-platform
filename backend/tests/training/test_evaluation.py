"""
test_evaluation.py — Unit tests for app/training/evaluation.py
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from app.training.evaluation import EvaluationError, evaluate_model


# ── Helpers ────────────────────────────────────────────────────────────────────


def make_fitted_rf(n: int = 200) -> tuple:
    """Return a fitted RandomForestClassifier plus test data."""
    rng = np.random.default_rng(42)
    X = pd.DataFrame({"a": rng.uniform(0, 1, n), "b": rng.uniform(0, 1, n)})
    y = pd.Series((X["a"] > 0.5).astype(int), name="target")

    split = int(n * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    est = RandomForestClassifier(n_estimators=20, random_state=42)
    est.fit(X_train, y_train)
    return est, X_test, y_test


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestEvaluateModel:
    def test_returns_dict(self) -> None:
        est, X_test, y_test = make_fitted_rf()
        metrics = evaluate_model(est, X_test, y_test)
        assert isinstance(metrics, dict)

    def test_contains_required_keys(self) -> None:
        est, X_test, y_test = make_fitted_rf()
        metrics = evaluate_model(est, X_test, y_test)
        required = {"accuracy", "precision", "recall", "f1_score", "confusion_matrix"}
        assert required.issubset(metrics.keys())

    def test_roc_auc_present_for_binary(self) -> None:
        est, X_test, y_test = make_fitted_rf()
        metrics = evaluate_model(est, X_test, y_test)
        assert "roc_auc" in metrics
        assert 0.0 <= metrics["roc_auc"] <= 1.0

    def test_accuracy_range(self) -> None:
        est, X_test, y_test = make_fitted_rf()
        metrics = evaluate_model(est, X_test, y_test)
        assert 0.0 <= metrics["accuracy"] <= 1.0

    def test_confusion_matrix_is_list_of_lists(self) -> None:
        est, X_test, y_test = make_fitted_rf()
        metrics = evaluate_model(est, X_test, y_test)
        cm = metrics["confusion_matrix"]
        assert isinstance(cm, list)
        assert all(isinstance(row, list) for row in cm)

    def test_all_values_are_json_serialisable(self) -> None:
        import json
        est, X_test, y_test = make_fitted_rf()
        metrics = evaluate_model(est, X_test, y_test)
        # Should not raise
        json.dumps(metrics)

    def test_raises_on_empty_test_data(self) -> None:
        est, _, _ = make_fitted_rf()
        X_empty = pd.DataFrame({"a": [], "b": []})
        y_empty = pd.Series([], dtype=int)
        with pytest.raises(EvaluationError, match="empty"):
            evaluate_model(est, X_empty, y_empty)
