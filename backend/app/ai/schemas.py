"""
ai/schemas.py — Pydantic models for the AI layer (Run Review + Run Comparison).

These schemas define the contract between the AI layer, the service, and the
public API. They are not SQLAlchemy models.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel


class AIReviewContent(BaseModel):
    """Five structured fields parsed from a Gemini JSON response (review)."""

    overall_assessment: str
    strengths: str
    weaknesses: str
    comparison: str
    recommendation: str


class AIReviewResponse(BaseModel):
    """Public API response shape for a completed AI review."""

    id: str
    run_id: str
    overall_assessment: str
    strengths: str
    weaknesses: str
    comparison: str
    recommendation: str
    model_name: str
    generated_at: datetime
    cached: bool

    model_config = {"from_attributes": True}


# ── Run Comparison Schemas ─────────────────────────────────────────────────────


class MetricDelta(BaseModel):
    """Numeric delta for a single metric between two runs."""

    metric: str
    run_a_value: float | None
    run_b_value: float | None
    delta: float | None           # run_b - run_a (positive = B improved)
    direction: str                # 'up', 'down', 'equal', or 'unavailable'


class AIComparisonContent(BaseModel):
    """Six structured fields parsed from a Gemini comparison response."""

    overall_summary: str
    better_run: str
    key_improvements: str
    tradeoffs: str
    configuration_analysis: str
    next_recommendation: str


class AIComparisonResponse(BaseModel):
    """Public API response shape for a completed AI run comparison."""

    id: str
    run_a_id: str
    run_b_id: str
    overall_summary: str
    better_run: str
    key_improvements: str
    tradeoffs: str
    configuration_analysis: str
    next_recommendation: str
    metric_deltas: list[MetricDelta]
    model_name: str
    generated_at: datetime
    cached: bool

    model_config = {"from_attributes": True}


# ── Ask MicroFlow (Natural Language Assistant) Schemas ─────────────────────────


class IntentExtractionResult(BaseModel):
    """Structured intent and filters extracted from user query by Gemini."""

    intent: str
    filters: dict[str, Any] = {}
    reasoning_required: bool = True


class ConversationMessage(BaseModel):
    """A single lightweight chat message in the session history."""

    role: str      # 'user' or 'assistant'
    content: str


class AIQueryRequest(BaseModel):
    """Request payload from frontend for natural language assistance."""

    question: str
    context: list[ConversationMessage] | None = None


class RetrievedSource(BaseModel):
    """Retrieved semantic document source for RAG attribution."""

    document_type: str
    document_id: str
    title: str
    snippet: str
    score: float | None = None


class AIQueryResponse(BaseModel):
    """Public API response shape for a completed assistant query."""

    id: str
    question: str
    intent: str
    answer: str
    reasoning: str
    supporting_data: str
    recommendation: str | None = None
    model_name: str
    generated_at: datetime
    cached: bool
    sources: list[RetrievedSource] = []

    # Evaluation Metrics
    context_relevance_score: float | None = None
    faithfulness_score: float | None = None
    answer_relevance_score: float | None = None
    evaluation_reasoning: str | None = None

    model_config = {"from_attributes": True}


# ── AI Dataset Intelligence Schemas ─────────────────────────────────────────────


class DatasetAIAnalysisResponse(BaseModel):
    """Public API response shape for an AI Dataset Intelligence analysis."""

    id: str
    dataset_id: str
    overall_summary: str
    recommended_target: str
    dataset_quality: Any
    strengths: Any
    potential_issues: Any
    recommended_preprocessing: Any
    recommended_models: Any
    feature_observations: Any
    risk_assessment: str
    next_steps: Any
    model_name: str
    generated_at: datetime
    cached: bool

    model_config = {"from_attributes": True}


# ── AI Experiment Strategy Schemas ──────────────────────────────────────────────


class ExperimentStrategyResponse(BaseModel):
    """Public API response shape for AI Experiment Strategy recommendations."""

    id: str
    experiment_id: str
    overall_assessment: str
    current_experiment_status: str
    observed_trends: Any
    strongest_model: str
    most_stable_model: str
    what_has_been_learned: Any
    remaining_search_space: Any
    recommended_next_experiment: Any
    confidence: str
    evidence_used: Any
    potential_risks: Any
    model_name: str
    generated_at: datetime
    cached: bool
    evidence_summary: dict[str, Any] | None = None

    model_config = {"from_attributes": True}

