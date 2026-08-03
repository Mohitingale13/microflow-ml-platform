"""
evaluation.py — Model Evaluation for the Training Engine.

Responsibility:
  - Evaluate a trained model on test data.
  - Generate classification metrics: accuracy, precision, recall, F1 score.
  - Generate ROC AUC for binary classification only.
  - Generate confusion matrix.
  - Return results as a plain dict — nothing is persisted here.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

logger = logging.getLogger(__name__)


class EvaluationError(Exception):
    """Raised when evaluation cannot be completed."""


def evaluate_model(
    estimator: ClassifierMixin,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, Any]:
    """
    Evaluate *estimator* on held-out test data.

    Metrics produced
    ----------------
    - accuracy
    - precision  (weighted average)
    - recall     (weighted average)
    - f1_score   (weighted average)
    - roc_auc    (only for binary classification, using predict_proba)
    - confusion_matrix (list of lists)

    Parameters
    ----------
    estimator:
        A fitted scikit-learn compatible classifier.
    X_test:
        Feature matrix for the test set.
    y_test:
        True labels for the test set.

    Returns
    -------
    dict[str, Any]
        Flat dict of metric name → value.  All numeric values are native Python
        floats or ints (JSON-serialisable).

    Raises
    ------
    EvaluationError
        If prediction fails or inputs are empty.
    """
    if X_test.empty or len(y_test) == 0:
        raise EvaluationError("Test data is empty — cannot evaluate model.")

    try:
        y_pred: np.ndarray = estimator.predict(X_test)
    except Exception as exc:
        raise EvaluationError(f"Prediction failed: {exc}") from exc

    classes = np.unique(y_test)
    is_binary = len(classes) == 2

    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(
            precision_score(y_test, y_pred, average="weighted", zero_division=0)
        ),
        "recall": float(
            recall_score(y_test, y_pred, average="weighted", zero_division=0)
        ),
        "f1_score": float(
            f1_score(y_test, y_pred, average="weighted", zero_division=0)
        ),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }

    # ROC AUC — binary only (requires predict_proba)
    if is_binary and hasattr(estimator, "predict_proba"):
        try:
            y_proba: np.ndarray = estimator.predict_proba(X_test)[:, 1]
            metrics["roc_auc"] = float(roc_auc_score(y_test, y_proba))
        except Exception as exc:
            logger.warning("ROC AUC computation skipped: %s", exc)

    logger.info(
        "Evaluation complete: accuracy=%.4f f1=%.4f",
        metrics["accuracy"],
        metrics["f1_score"],
    )
    return metrics
