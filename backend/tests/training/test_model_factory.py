"""
test_model_factory.py — Unit tests for app/training/model_factory.py
"""

import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from app.training.model_factory import (
    DEFAULT_MODEL,
    SUPPORTED_MODELS,
    build_estimator,
)


class TestBuildEstimator:
    def test_logistic_regression(self) -> None:
        est = build_estimator("logistic_regression", {})
        assert isinstance(est, LogisticRegression)

    def test_random_forest(self) -> None:
        est = build_estimator("random_forest", {})
        assert isinstance(est, RandomForestClassifier)

    def test_xgboost(self) -> None:
        from xgboost import XGBClassifier
        est = build_estimator("xgboost", {})
        assert isinstance(est, XGBClassifier)

    def test_none_model_type_defaults_to_random_forest(self) -> None:
        est = build_estimator(None, {})
        assert isinstance(est, RandomForestClassifier)

    def test_unknown_model_type_defaults_to_random_forest(self) -> None:
        est = build_estimator("neural_net_super_large", {})
        assert isinstance(est, RandomForestClassifier)

    def test_logistic_regression_hyperparams_applied(self) -> None:
        est = build_estimator("logistic_regression", {"C": 0.5, "max_iter": 200})
        assert isinstance(est, LogisticRegression)
        assert est.C == pytest.approx(0.5)
        assert est.max_iter == 200

    def test_random_forest_hyperparams_applied(self) -> None:
        est = build_estimator("random_forest", {"n_estimators": 50, "max_depth": 3})
        assert isinstance(est, RandomForestClassifier)
        assert est.n_estimators == 50
        assert est.max_depth == 3

    def test_xgboost_hyperparams_applied(self) -> None:
        from xgboost import XGBClassifier
        est = build_estimator("xgboost", {"n_estimators": 25, "learning_rate": 0.05})
        assert isinstance(est, XGBClassifier)
        assert est.n_estimators == 25

    def test_seed_alias_used_as_random_state(self) -> None:
        est = build_estimator("random_forest", {"seed": 123})
        assert isinstance(est, RandomForestClassifier)
        assert est.random_state == 123

    def test_supported_models_constant_is_complete(self) -> None:
        assert "random_forest" in SUPPORTED_MODELS
        assert "logistic_regression" in SUPPORTED_MODELS
        assert "xgboost" in SUPPORTED_MODELS
