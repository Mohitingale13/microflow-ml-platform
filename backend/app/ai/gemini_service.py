"""
ai/gemini_service.py — Thin wrapper around the Google Generative AI SDK with resilience.

All Gemini API calls must go through this module.
No other file in this codebase may import google.generativeai or genai directly.
Includes automatic exponential backoff and retries to silently heal 503 High Demand spikes.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from google import genai  # type: ignore

from app.core.config import settings

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-3.6-flash"
FALLBACK_MODELS = ["gemini-3.5-flash"]


class GeminiService:
    """
    Wraps the Google Generative AI SDK with automatic retries and model fallback.

    The API key is read from settings on first use. If GEMINI_API_KEY is not
    configured, a RuntimeError is raised with a clear message.
    """

    def __init__(self) -> None:
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        """Configure the SDK with the API key from settings (once)."""
        if self._client:
            return self._client
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. "
                "Add it to backend/.env or as an environment variable on your hosting platform. "
                "Obtain a key at https://aistudio.google.com/app/apikey"
            )
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def _generate_with_retry(self, prompt: str, operation_name: str) -> str:
        """
        Executes generation against Gemini with automatic retries for 503 / 429
        temporary traffic spikes, plus fallback model support.
        """
        client = self._get_client()
        max_attempts = 3
        models_to_try = [MODEL_NAME] + FALLBACK_MODELS
        last_exc: Optional[Exception] = None

        for model in models_to_try:
            for attempt in range(1, max_attempts + 1):
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                    raw_text: str = response.text or ""
                    logger.info(
                        "Gemini [%s] generated successfully via model %s on attempt %d (chars=%d)",
                        operation_name,
                        model,
                        attempt,
                        len(raw_text),
                    )
                    return raw_text
                except Exception as exc:
                    last_exc = exc
                    exc_str = str(exc).lower()
                    # Check if error is a temporary demand spike or rate limit
                    is_transient = (
                        "503" in exc_str
                        or "unavailable" in exc_str
                        or "high demand" in exc_str
                        or "429" in exc_str
                        or "resource exhausted" in exc_str
                        or "timeout" in exc_str
                    )

                    if is_transient and attempt < max_attempts:
                        backoff_seconds = 1.5 * (2 ** (attempt - 1))
                        logger.warning(
                            "Transient Gemini error (%s) on [%s] (model %s, attempt %d/%d). "
                            "Retrying in %.1f seconds...",
                            type(exc).__name__,
                            operation_name,
                            model,
                            attempt,
                            max_attempts,
                            backoff_seconds,
                        )
                        time.sleep(backoff_seconds)
                        continue
                    elif is_transient and model != models_to_try[-1]:
                        # Move to fallback model if current model stays congested
                        logger.warning(
                            "Model %s remains congested for [%s]. Switching to fallback model...",
                            model,
                            operation_name
                        )
                        break
                    else:
                        # Non-transient error or exhausted all retries and fallbacks
                        logger.error("Gemini API call failed for [%s]: %s", operation_name, exc)
                        break

        # If we get here, all retries and fallbacks failed
        exc_str = str(last_exc).lower() if last_exc else ""
        if "503" in exc_str or "high demand" in exc_str or "unavailable" in exc_str:
            raise RuntimeError(
                "Google AI providers are experiencing extreme global demand spikes right now. "
                "MicroFlow attempted automatic retries and failovers, but AI compute clusters remain busy. "
                "Please wait 30 seconds and try your request again."
            ) from last_exc
        elif "429" in exc_str or "resource exhausted" in exc_str or "quota" in exc_str or "rate limit" in exc_str:
            raise RuntimeError(
                "Google Gemini AI free-tier rate limit or quota has been momentarily reached. "
                "Please wait 30 seconds for your token bucket to replenish before running your query again."
            ) from last_exc

        raise RuntimeError(f"Gemini AI processing failed: {last_exc}") from last_exc

    def generate_review(self, prompt: str) -> str:
        """Send prompt to Gemini to generate ML run review."""
        return self._generate_with_retry(prompt, "generate_review")

    def generate_comparison(self, prompt: str) -> str:
        """Send prompt to Gemini to compare two completed runs."""
        return self._generate_with_retry(prompt, "generate_comparison")

    def extract_intent(self, prompt: str) -> str:
        """Send prompt to Gemini to extract intent and filters (Ask MicroFlow)."""
        return self._generate_with_retry(prompt, "extract_intent")

    def generate_answer(self, prompt: str) -> str:
        """Send prompt to Gemini to generate professional engineering answer (Ask MicroFlow)."""
        return self._generate_with_retry(prompt, "generate_answer")

    def generate_dataset_analysis(self, prompt: str) -> str:
        """Send prompt to Gemini to conduct AI Dataset Intelligence audit."""
        return self._generate_with_retry(prompt, "generate_dataset_analysis")

    def generate_experiment_strategy(self, prompt: str) -> str:
        """Send prompt to Gemini to formulate AI Experiment Strategy."""
        return self._generate_with_retry(prompt, "generate_experiment_strategy")

    @property
    def model_name(self) -> str:
        return MODEL_NAME
