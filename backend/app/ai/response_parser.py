"""
ai/response_parser.py — Parses and validates the raw Gemini JSON response.

Gemini is instructed to return a single JSON object with exactly five fields.
This module extracts that object, validates field presence, and returns a
typed AIReviewContent. It raises ValueError on any malformed response.
"""

from __future__ import annotations

import json
import re
from typing import Any

from app.ai.schemas import AIReviewContent

_REQUIRED_FIELDS = {
    "overall_assessment",
    "strengths",
    "weaknesses",
    "comparison",
    "recommendation",
}


def parse_gemini_response(raw: str) -> AIReviewContent:
    """
    Parse the raw string returned by Gemini into an AIReviewContent.

    Parameters
    ----------
    raw : str
        The raw text output from Gemini. May contain surrounding text or
        markdown fences even when the prompt forbids it (Gemini occasionally
        wraps JSON in ```json ... ```). This function handles both cases.

    Raises
    ------
    ValueError
        If the response cannot be parsed as valid JSON, or if any required
        field is missing or empty.
    """
    # Strip markdown code fences if present
    cleaned = raw.strip()
    # Match ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1)
    else:
        # Find the first { and last } as the JSON boundaries
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(
                f"Gemini response does not contain a JSON object. Raw: {raw[:500]}"
            )
        cleaned = cleaned[start : end + 1]

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Gemini response is not valid JSON: {exc}. Raw excerpt: {cleaned[:300]}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object, got {type(data).__name__}.")

    missing = _REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(
            f"Gemini response is missing required fields: {sorted(missing)}"
        )

    # Validate all fields are non-empty strings
    for field in _REQUIRED_FIELDS:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Field '{field}' must be a non-empty string, got: {value!r}"
            )

    return AIReviewContent(
        overall_assessment=data["overall_assessment"].strip(),
        strengths=data["strengths"].strip(),
        weaknesses=data["weaknesses"].strip(),
        comparison=data["comparison"].strip(),
        recommendation=data["recommendation"].strip(),
    )


# ── Comparison response parser ─────────────────────────────────────────────────

from app.ai.schemas import AIComparisonContent  # noqa: E402 — avoids circular at top

_COMPARISON_REQUIRED_FIELDS = {
    "overall_summary",
    "better_run",
    "key_improvements",
    "tradeoffs",
    "configuration_analysis",
    "next_recommendation",
}


def parse_comparison_response(raw: str) -> AIComparisonContent:
    """
    Parse the raw string returned by Gemini into an AIComparisonContent.

    Applies identical fence-stripping and JSON boundary logic as
    parse_gemini_response, but validates the six comparison-specific fields.

    Parameters
    ----------
    raw : str
        Raw text output from Gemini for a run comparison prompt.

    Raises
    ------
    ValueError
        If the response cannot be parsed as valid JSON, or if any required
        comparison field is missing or empty.
    """
    cleaned = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1)
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(
                f"Gemini comparison response does not contain a JSON object. Raw: {raw[:500]}"
            )
        cleaned = cleaned[start : end + 1]

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Gemini comparison response is not valid JSON: {exc}. Raw excerpt: {cleaned[:300]}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object, got {type(data).__name__}.")

    missing = _COMPARISON_REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(
            f"Gemini comparison response is missing required fields: {sorted(missing)}"
        )

    for field in _COMPARISON_REQUIRED_FIELDS:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Comparison field '{field}' must be a non-empty string, got: {value!r}"
            )

    return AIComparisonContent(
        overall_summary=data["overall_summary"].strip(),
        better_run=data["better_run"].strip(),
        key_improvements=data["key_improvements"].strip(),
        tradeoffs=data["tradeoffs"].strip(),
        configuration_analysis=data["configuration_analysis"].strip(),
        next_recommendation=data["next_recommendation"].strip(),
    )


# ── Ask MicroFlow Response Parsers ─────────────────────────────────────────────

from app.ai.schemas import IntentExtractionResult  # noqa: E402

_ASSISTANT_REQUIRED_FIELDS = {"answer", "reasoning", "supporting_data"}


def _extract_json_dict(raw: str, label: str) -> dict:
    cleaned = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1)
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"Gemini {label} response does not contain a JSON object. Raw: {raw[:500]}")
        cleaned = cleaned[start : end + 1]

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini {label} response is not valid JSON: {exc}. Raw excerpt: {cleaned[:300]}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object for {label}, got {type(data).__name__}.")
    return data


def parse_intent_response(raw: str) -> IntentExtractionResult:
    """
    Parse the raw JSON string returned by Gemini during intent extraction.

    Returns an IntentExtractionResult with validated intent string and filters dict.
    """
    data = _extract_json_dict(raw, "intent extraction")
    if "intent" not in data or not str(data["intent"]).strip():
        raise ValueError("Intent extraction response is missing a valid 'intent' field.")

    intent_val = str(data["intent"]).strip().lower()
    filters_val = data.get("filters", {})
    if not isinstance(filters_val, dict):
        filters_val = {}

    reasoning_val = bool(data.get("reasoning_required", True))
    return IntentExtractionResult(intent=intent_val, filters=filters_val, reasoning_required=reasoning_val)


def parse_assistant_response(raw: str) -> dict[str, str]:
    """
    Parse the raw JSON string returned by Gemini for the main assistant answer.

    Validates presence of answer, reasoning, and supporting_data.
    """
    data = _extract_json_dict(raw, "assistant answer")
    missing = _ASSISTANT_REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"Gemini assistant response is missing required fields: {sorted(missing)}")

    for field in _ASSISTANT_REQUIRED_FIELDS:
        val = data[field]
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"Assistant field '{field}' must be a non-empty string, got: {val!r}")

    recommendation = data.get("recommendation", "No further action required.")
    if not isinstance(recommendation, str):
        recommendation = str(recommendation)

    return {
        "answer": data["answer"].strip(),
        "reasoning": data["reasoning"].strip(),
        "supporting_data": data["supporting_data"].strip(),
        "recommendation": recommendation.strip(),
    }


_DATASET_REQUIRED_FIELDS = {
    "overall_summary",
    "recommended_target",
    "dataset_quality",
    "strengths",
    "potential_issues",
    "recommended_preprocessing",
    "recommended_models",
    "feature_observations",
    "risk_assessment",
    "next_steps",
}


def parse_dataset_analysis_response(raw: str) -> dict[str, Any]:
    """
    Parse the raw JSON string returned by Gemini for AI Dataset Intelligence.

    Validates presence of all 10 structured analysis fields.
    """
    data = _extract_json_dict(raw, "dataset intelligence analysis")
    missing = _DATASET_REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"Gemini dataset analysis response is missing required fields: {sorted(missing)}")

    return {field: data[field] for field in _DATASET_REQUIRED_FIELDS}


_STRATEGY_REQUIRED_FIELDS = {
    "overall_assessment",
    "current_experiment_status",
    "observed_trends",
    "strongest_model",
    "most_stable_model",
    "what_has_been_learned",
    "remaining_search_space",
    "recommended_next_experiment",
    "confidence",
    "evidence_used",
    "potential_risks",
}


def parse_experiment_strategy_response(raw: str) -> dict[str, Any]:
    """
    Parse the raw JSON string returned by Gemini for AI Experiment Strategy.

    Validates presence of all 11 structured strategy fields and explicit confidence rating.
    """
    data = _extract_json_dict(raw, "experiment strategy recommendation")
    missing = _STRATEGY_REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"Gemini experiment strategy response is missing required fields: {sorted(missing)}")

    conf = str(data.get("confidence", "Medium")).strip()
    if conf not in {"High", "Medium", "Low"}:
        data["confidence"] = "Medium"  # Fallback if unformatted, but keep validated

    return {field: data[field] for field in _STRATEGY_REQUIRED_FIELDS}

