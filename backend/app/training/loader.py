"""
loader.py — Dataset Loader for the Training Engine.

Responsibility:
  - Load a CSV dataset from the storage_path recorded in the Dataset model.
  - Validate the file exists on disk.
  - Return a clean Pandas DataFrame.

This module is intentionally independent of all ORM models and HTTP concerns.
"""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class DatasetLoaderError(Exception):
    """Raised when a dataset cannot be loaded."""


def load_dataset(storage_path: str) -> pd.DataFrame:
    """
    Load a CSV file from *storage_path* and return it as a DataFrame.

    Parameters
    ----------
    storage_path:
        Absolute or relative filesystem path stored on the Dataset record.

    Returns
    -------
    pd.DataFrame
        Raw (un-preprocessed) contents of the CSV file.

    Raises
    ------
    DatasetLoaderError
        If the file does not exist or cannot be parsed as CSV.
    """
    path = Path(storage_path)

    if not path.exists():
        raise DatasetLoaderError(
            f"Dataset file not found at path: {storage_path!r}"
        )

    if not path.is_file():
        raise DatasetLoaderError(
            f"Path exists but is not a regular file: {storage_path!r}"
        )

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise DatasetLoaderError(
            f"Failed to read CSV from {storage_path!r}: {exc}"
        ) from exc

    logger.info(
        "Dataset loaded: path=%r rows=%d columns=%d",
        storage_path,
        len(df),
        len(df.columns),
    )
    return df
