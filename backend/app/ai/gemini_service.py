"""
ai/gemini_service.py — Thin wrapper around the Google Generative AI SDK with resilience.

All Gemini API calls must go through this module.
No other file in this codebase may import google.generativeai or genai directly.
Includes automatic exponential backoff and retries to silently heal 503 High Demand spikes.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from google import genai  # type: ignore
from google.genai import types  # type: ignore

from app.core.config import settings

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"
FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.0-flash",
    "gemini-3.6-flash",
]


class GeminiService:
    """
    Wraps the Google Generative AI SDK with automatic retries and model fallback.

    The API key is read from settings on first use. If GEMINI_API_KEY is not
    configured, a RuntimeError is raised with a clear message.
    """

    def __init__(self) -> None:
        self._client: Optional[genai.Client] = None
        self._model_cooldowns: dict[str, float] = {}

    def _get_client(self) -> genai.Client:
        """Lazily initialize and return the genai.Client."""
        if self._client is not None:
            return self._client

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Please set it in your environment or .env file."
            )

        self._client = genai.Client(api_key=api_key)
        logger.info("Initialized Gemini Client with model: %s", MODEL_NAME)
        return self._client

    def _generate_with_retry(self, prompt: str, operation_name: str) -> str:
        """
        Execute generate_content with progressive exponential backoff and fallback models.
        """
        response = self.generate_chat_turn(
            contents=prompt,
            operation_name=operation_name,
        )
        return response.text or ""

    def generate_chat_turn(
        self,
        contents: list[Any] | str,
        tools: list[Any] | None = None,
        system_instruction: str | None = None,
        operation_name: str = "agent_turn",
    ) -> Any:
        """
        Send contents and optional tools/system instruction to Gemini with full retry and failover resilience.
        Returns the raw generate_content response object.
        """
        client = self._get_client()
        max_attempts = 3
        all_models = [MODEL_NAME] + FALLBACK_MODELS

        now = time.time()
        models_to_try = [m for m in all_models if now >= self._model_cooldowns.get(m, 0)]
        if not models_to_try:
            models_to_try = all_models

        last_exc: Optional[Exception] = None

        config_kwargs: dict[str, Any] = {}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if tools:
            config_kwargs["tools"] = tools

        config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

        for model in models_to_try:
            for attempt in range(1, max_attempts + 1):
                try:
                    kwargs: dict[str, Any] = {"model": model, "contents": contents}
                    if config:
                        kwargs["config"] = config

                    response = client.models.generate_content(**kwargs)
                    logger.info(
                        "Gemini [%s] turn completed via model %s (attempt %d)",
                        operation_name,
                        model,
                        attempt,
                    )
                    return response
                except Exception as exc:
                    last_exc = exc
                    exc_str = str(exc).lower()

                    is_quota = (
                        "429" in exc_str
                        or "resource exhausted" in exc_str
                        or "quota" in exc_str
                        or "rate limit" in exc_str
                        or ("limit" in exc_str and "0" in exc_str)
                    )

                    if is_quota:
                        is_daily = "perday" in exc_str or "day" in exc_str or "daily" in exc_str
                        cooldown_secs = 21600.0 if is_daily else 60.0
                        self._model_cooldowns[model] = time.time() + cooldown_secs
                        logger.warning(
                            "Model %s hit quota/rate limit during [%s]. Placing on cooldown for %ds and failing over...",
                            model,
                            operation_name,
                            int(cooldown_secs),
                        )
                        break

                    is_transient = (
                        "503" in exc_str
                        or "unavailable" in exc_str
                        or "high demand" in exc_str
                        or "timeout" in exc_str
                    )

                    if is_transient and attempt < max_attempts:
                        backoff_seconds = 1.5 * (2 ** (attempt - 1))
                        logger.warning(
                            "Transient Gemini server spike (%s) on [%s] (model %s, attempt %d/%d). Retrying in %.1f seconds...",
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
                        logger.warning(
                            "Model %s remains congested for [%s]. Switching to fallback model...",
                            model,
                            operation_name,
                        )
                        break
                    else:
                        logger.error("Gemini API call failed for [%s]: %s", operation_name, exc)
                        break

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

    def generate_evaluation(self, prompt: str) -> str:
        """Send prompt to Gemini to evaluate RAG answer strictly (RAGAS)."""
        return self._generate_with_retry(prompt, "generate_evaluation")

    def generate_embedding(self, text: str) -> list[float]:
        """Generate 768-dimensional embedding vector using Google's text-embedding-004 model."""
        if not text or not text.strip():
            return [0.0] * 768
        client = self._get_client()
        try:
            res = client.models.embed_content(
                model="text-embedding-004",
                contents=text.strip(),
            )
            if hasattr(res, "embedding") and hasattr(res.embedding, "values"):
                return list(res.embedding.values)
            elif isinstance(res, dict) and "embedding" in res:
                return list(res["embedding"]["values"])
            elif hasattr(res, "embeddings") and len(res.embeddings) > 0:
                return list(res.embeddings[0].values)
            raise ValueError(f"Unexpected embed_content response structure: {res}")
        except Exception as exc:
            logger.error("Failed to generate embedding via text-embedding-004: %s", exc)
            return [0.0] * 768

    @property
    def model_name(self) -> str:
        return MODEL_NAME
