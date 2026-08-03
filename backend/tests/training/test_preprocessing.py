"""
test_preprocessing.py — Unit tests for app/training/preprocessing.py
"""

import pandas as pd
import pytest

from app.training.preprocessing import (
    PreprocessingError,
    PreprocessedData,
    preprocess_dataframe,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def make_df(n: int = 100, binary: bool = True) -> pd.DataFrame:
    """Return a simple synthetic DataFrame for testing."""
    import numpy as np

    rng = np.random.default_rng(42)
    df = pd.DataFrame(
        {
            "num_a": rng.uniform(0, 10, n),
            "num_b": rng.integers(0, 100, n).astype(float),
            "cat_a": rng.choice(["x", "y", "z"], n),
            "target": rng.integers(0, 2 if binary else 3, n),
        }
    )
    return df


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestPreprocessDataframe:
    def test_returns_preprocessed_data(self) -> None:
        df = make_df()
        result = preprocess_dataframe(df, target_column="target")
        assert isinstance(result, PreprocessedData)

    def test_split_sizes(self) -> None:
        df = make_df(n=100)
        result = preprocess_dataframe(df, target_column="target", test_size=0.2)
        assert len(result.X_test) == pytest.approx(20, abs=2)
        assert len(result.X_train) == pytest.approx(80, abs=2)

    def test_no_target_column_in_features(self) -> None:
        df = make_df()
        result = preprocess_dataframe(df, target_column="target")
        assert "target" not in result.X_train.columns
        assert "target" not in result.X_test.columns

    def test_categorical_columns_encoded(self) -> None:
        df = make_df()
        result = preprocess_dataframe(df, target_column="target")
        # After one-hot encoding, 'cat_a' column should not exist raw
        assert "cat_a" not in result.X_train.columns
        # But one of its dummies should
        assert any(c.startswith("cat_a_") for c in result.X_train.columns)

    def test_feature_names_match_columns(self) -> None:
        df = make_df()
        result = preprocess_dataframe(df, target_column="target")
        assert result.feature_names == list(result.X_train.columns)

    def test_raises_for_missing_target(self) -> None:
        df = make_df()
        with pytest.raises(PreprocessingError, match="not found"):
            preprocess_dataframe(df, target_column="nonexistent")

    def test_handles_missing_numeric_values(self) -> None:
        import numpy as np

        df = make_df(n=100)
        df.loc[df.index[:10], "num_a"] = np.nan
        # Should not raise
        result = preprocess_dataframe(df, target_column="target")
        assert not result.X_train["num_a"].isna().any()
        assert not result.X_test["num_a"].isna().any()

    def test_handles_missing_categorical_values(self) -> None:
        import numpy as np

        df = make_df(n=100)
        df.loc[df.index[:5], "cat_a"] = np.nan
        result = preprocess_dataframe(df, target_column="target")
        assert result.X_train is not None

    def test_string_target_gets_label_encoded(self) -> None:
        df = make_df(n=100)
        df["target"] = df["target"].map({0: "negative", 1: "positive"})
        result = preprocess_dataframe(df, target_column="target")
        assert result.target_encoder is not None
        assert set(result.y_train.unique()).issubset({0, 1})

    def test_integer_target_no_encoder(self) -> None:
        df = make_df(n=100)
        result = preprocess_dataframe(df, target_column="target")
        assert result.target_encoder is None
