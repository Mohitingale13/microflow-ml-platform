"""
model_factory.py — Model Factory for the Training Engine.

Responsibility:
  - Map a model_type string to the correct scikit-learn / XGBoost estimator.
  - Apply hyperparameters from the training_configuration dict.
  - Use sensible defaults when parameters are omitted.
  - Raise a clear error for unsupported model types.

The Factory Pattern keeps estimator creation in one place — no other module
ever calls a model constructor directly.
"""

import logging
from typing import Any

from sklearn.base import ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)

# ── Supported model identifiers ────────────────────────────────────────────────

MODEL_RANDOM_FOREST = "random_forest"
MODEL_LOGISTIC_REGRESSION = "logistic_regression"
MODEL_XGBOOST = "xgboost"

SUPPORTED_MODELS: set[str] = {
    MODEL_RANDOM_FOREST,
    MODEL_LOGISTIC_REGRESSION,
    MODEL_XGBOOST,
}

DEFAULT_MODEL = MODEL_RANDOM_FOREST


# ── Errors ─────────────────────────────────────────────────────────────────────


class ModelFactoryError(Exception):
    """Raised when the factory cannot create an estimator."""


# ── Factory ────────────────────────────────────────────────────────────────────


def build_estimator(
    model_type: str | None,
    training_configuration: dict[str, Any] | None,
) -> ClassifierMixin:
    """
    Construct and return a configured classifier estimator.

    Parameters
    ----------
    model_type:
        One of ``"random_forest"``, ``"logistic_regression"``, ``"xgboost"``.
        If *None* or unknown, defaults to ``"random_forest"`` with a warning.
    training_configuration:
        Dict of hyperparameter overrides sourced from the Run record.
        Unknown keys for a given model are silently ignored.

    Returns
    -------
    ClassifierMixin
        An un-fitted scikit-learn compatible classifier.
    """
    config: dict[str, Any] = training_configuration or {}
    resolved_type = _resolve_model_type(model_type)

    if resolved_type == MODEL_LOGISTIC_REGRESSION:
        estimator = _build_logistic_regression(config)
    elif resolved_type == MODEL_RANDOM_FOREST:
        estimator = _build_random_forest(config)
    elif resolved_type == MODEL_XGBOOST:
        estimator = _build_xgboost(config)
    else:
        # Should not be reachable after _resolve_model_type, but kept for safety.
        raise ModelFactoryError(f"Unhandled model type: {resolved_type!r}")

    logger.info("Estimator built: type=%r config_keys=%s", resolved_type, list(config))
    return estimator


# ── Private builders ───────────────────────────────────────────────────────────


def _resolve_model_type(model_type: str | None) -> str:
    if not model_type:
        logger.warning(
            "model_type is None — falling back to default: %r", DEFAULT_MODEL
        )
        return DEFAULT_MODEL

    normalized = model_type.strip().lower()
    if normalized not in SUPPORTED_MODELS:
        logger.warning(
            "Unsupported model_type %r — falling back to default: %r",
            model_type,
            DEFAULT_MODEL,
        )
        return DEFAULT_MODEL

    return normalized


def _build_logistic_regression(config: dict[str, Any]) -> LogisticRegression:
    return LogisticRegression(
        C=float(config.get("C", 1.0)),
        max_iter=int(config.get("max_iter", 1000)),
        solver=str(config.get("solver", "lbfgs")),
        random_state=int(config.get("random_state", config.get("seed", 42))),
        n_jobs=-1,
    )


def _build_random_forest(config: dict[str, Any]) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=int(config.get("n_estimators", 100)),
        max_depth=config.get("max_depth"),  # None = unlimited
        random_state=int(config.get("random_state", config.get("seed", 42))),
        n_jobs=-1,
    )


def _build_xgboost(config: dict[str, Any]):
    # Import here to avoid hard dependency at module load if XGBoost is missing.
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:
        raise ModelFactoryError(
            "xgboost package is not installed. "
            "Add 'xgboost' to requirements.txt."
        ) from exc

    return XGBClassifier(
        n_estimators=int(config.get("n_estimators", 100)),
        max_depth=int(config.get("max_depth", 6)),
        learning_rate=float(config.get("learning_rate", 0.1)),
        random_state=int(config.get("random_state", config.get("seed", 42))),
        eval_metric="logloss",
        verbosity=0,
        use_label_encoder=False,
    )
