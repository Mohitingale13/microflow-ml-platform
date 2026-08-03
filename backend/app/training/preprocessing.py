"""
preprocessing.py — Data Preprocessing for the Training Engine.

Responsibility:
  - Validate the target column exists in the DataFrame.
  - Separate features (X) from the target (y).
  - Handle missing values (median for numeric, mode for categorical).
  - Encode categorical features via one-hot encoding.
  - Perform a stratified train/test split.
  - Return processed training and testing datasets.

This module uses scikit-learn utilities throughout and has no ORM or HTTP
dependencies.
"""

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

# ── Public data-classes ────────────────────────────────────────────────────────


@dataclass
class PreprocessedData:
    """Container returned by preprocess_dataframe."""

    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    feature_names: list[str]
    target_encoder: LabelEncoder | None  # populated only for string targets


# ── Errors ─────────────────────────────────────────────────────────────────────


class PreprocessingError(Exception):
    """Raised when preprocessing cannot be completed."""


# ── Public API ─────────────────────────────────────────────────────────────────


def preprocess_dataframe(
    df: pd.DataFrame,
    target_column: str,
    *,
    test_size: float = 0.2,
    random_state: int = 42,
) -> PreprocessedData:
    """
    Preprocess *df* ready for model training.

    Steps
    -----
    1. Validate target column.
    2. Drop rows where the target is NaN.
    3. Fill missing numeric values with column median.
    4. Fill missing categorical values with column mode.
    5. One-hot encode categorical feature columns.
    6. Label-encode string target values (binary or multi-class).
    7. Stratified train/test split.

    Parameters
    ----------
    df:
        Raw DataFrame as loaded by loader.py.
    target_column:
        Name of the label / output column.
    test_size:
        Fraction of data reserved for evaluation (default 0.2).
    random_state:
        Reproducibility seed for the split (default 42).

    Returns
    -------
    PreprocessedData
        Named tuple of (X_train, X_test, y_train, y_test, feature_names, target_encoder).
    """
    if target_column not in df.columns:
        raise PreprocessingError(
            f"Target column '{target_column}' not found in dataset. "
            f"Available columns: {list(df.columns)}"
        )

    # ── 1. Separate X and y ────────────────────────────────────────────────────
    y_raw: pd.Series = df[target_column].copy()
    X: pd.DataFrame = df.drop(columns=[target_column]).copy()

    # ── 2. Drop rows with null target ─────────────────────────────────────────
    null_mask = y_raw.isna()
    if null_mask.any():
        n_dropped = int(null_mask.sum())
        logger.warning("Dropping %d rows with null target value.", n_dropped)
        X = X[~null_mask].reset_index(drop=True)
        y_raw = y_raw[~null_mask].reset_index(drop=True)

    if len(X) == 0:
        raise PreprocessingError("No rows remain after dropping null target values.")

    # ── 3. Missing value imputation ────────────────────────────────────────────
    numeric_cols = X.select_dtypes(include="number").columns.tolist()
    categorical_cols = X.select_dtypes(exclude="number").columns.tolist()

    for col in numeric_cols:
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].median())

    for col in categorical_cols:
        if X[col].isna().any():
            mode_val = X[col].mode()
            fill_val = mode_val.iloc[0] if not mode_val.empty else "MISSING"
            X[col] = X[col].fillna(fill_val)

    # ── 4. One-hot encode categorical features ─────────────────────────────────
    if categorical_cols:
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=False)

    feature_names: list[str] = X.columns.tolist()

    # ── 5. Encode target ───────────────────────────────────────────────────────
    target_encoder: LabelEncoder | None = None
    if y_raw.dtype == object or str(y_raw.dtype) == "category":
        target_encoder = LabelEncoder()
        y: pd.Series = pd.Series(
            target_encoder.fit_transform(y_raw), name=target_column
        )
    else:
        y = y_raw.astype(int)

    # ── 6. Train/test split ────────────────────────────────────────────────────
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=y,
        )
    except ValueError:
        # Fall back to non-stratified split for very small datasets
        logger.warning(
            "Stratified split failed (too few samples per class); "
            "falling back to random split."
        )
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
        )

    logger.info(
        "Preprocessing complete: train=%d test=%d features=%d",
        len(X_train),
        len(X_test),
        len(feature_names),
    )

    return PreprocessedData(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        feature_names=feature_names,
        target_encoder=target_encoder,
    )
