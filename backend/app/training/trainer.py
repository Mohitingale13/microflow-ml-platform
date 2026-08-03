"""
trainer.py — Model Training for the Training Engine.

Responsibility:
  - Receive a pre-configured estimator and preprocessed training data.
  - Fit the estimator.
  - Return the trained estimator.

No evaluation logic belongs here.
No persistence logic belongs here.
"""

import logging

import pandas as pd
from sklearn.base import ClassifierMixin

logger = logging.getLogger(__name__)


class TrainerError(Exception):
    """Raised when model training fails."""


def train_model(
    estimator: ClassifierMixin,
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> ClassifierMixin:
    """
    Fit *estimator* on the provided training data.

    Parameters
    ----------
    estimator:
        An un-fitted scikit-learn compatible classifier (from model_factory).
    X_train:
        Feature matrix for training.
    y_train:
        Target labels for training.

    Returns
    -------
    ClassifierMixin
        The same estimator, now fitted.

    Raises
    ------
    TrainerError
        If fitting raises any exception.
    """
    if X_train.empty or len(y_train) == 0:
        raise TrainerError("Training data is empty — cannot fit model.")

    estimator_name = type(estimator).__name__
    logger.info(
        "Training started: estimator=%s samples=%d features=%d",
        estimator_name,
        len(X_train),
        X_train.shape[1],
    )

    try:
        estimator.fit(X_train, y_train)
    except Exception as exc:
        raise TrainerError(
            f"Fitting {estimator_name} failed: {exc}"
        ) from exc

    logger.info("Training complete: estimator=%s", estimator_name)
    return estimator
