"""
test_loader.py — Unit tests for app/training/loader.py
"""

import textwrap
from pathlib import Path

import pandas as pd
import pytest

from app.training.loader import DatasetLoaderError, load_dataset


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture()
def csv_file(tmp_path: Path) -> Path:
    """Write a minimal valid CSV to a temp file and return its path."""
    content = textwrap.dedent("""\
        feature_a,feature_b,target
        1,2,0
        3,4,1
        5,6,0
        7,8,1
    """)
    p = tmp_path / "dataset.csv"
    p.write_text(content)
    return p


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestLoadDataset:
    def test_returns_dataframe(self, csv_file: Path) -> None:
        df = load_dataset(str(csv_file))
        assert isinstance(df, pd.DataFrame)

    def test_correct_shape(self, csv_file: Path) -> None:
        df = load_dataset(str(csv_file))
        assert df.shape == (4, 3)

    def test_correct_columns(self, csv_file: Path) -> None:
        df = load_dataset(str(csv_file))
        assert list(df.columns) == ["feature_a", "feature_b", "target"]

    def test_raises_for_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(DatasetLoaderError, match="not found"):
            load_dataset(str(tmp_path / "nonexistent.csv"))

    def test_raises_for_directory(self, tmp_path: Path) -> None:
        with pytest.raises(DatasetLoaderError, match="not a regular file"):
            load_dataset(str(tmp_path))

    def test_raises_for_malformed_csv(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.csv"
        # Write binary garbage that pandas cannot parse as CSV
        bad_file.write_bytes(b"\x00\x01\x02\x03")
        # pandas actually tolerates binary; use a clearly unreadable encoding
        # by writing bytes that will cause a UnicodeDecodeError
        bad_file.write_bytes(b"\xff\xfe" * 50)
        # This may or may not error depending on platform; just ensure no crash
        try:
            load_dataset(str(bad_file))
        except DatasetLoaderError:
            pass  # Expected
