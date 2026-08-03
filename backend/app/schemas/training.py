"""
training.py — Pydantic schemas for the Training Engine endpoints.
"""

from typing import Any

from pydantic import BaseModel, Field


class ExecuteRunRequest(BaseModel):
    """Request body for POST /api/v1/runs/{run_id}/execute."""

    target_column: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the label column in the dataset CSV.",
    )
    test_split: float | None = Field(
        None,
        ge=0.05,
        le=0.5,
        description=(
            "Fraction of data to reserve for testing. "
            "Defaults to the value in training_configuration['test_split'] or 0.2."
        ),
    )


class EvaluationMetrics(BaseModel):
    """Evaluation results produced after a successful training run."""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float | None = None
    confusion_matrix: list[list[int]]


class ExecuteRunResponse(BaseModel):
    """Data payload returned by a successful execute call."""

    run_id: str
    status: str
    metrics: EvaluationMetrics
    model_type: str | None
