"""
ai/gemini_service.py — Thin wrapper around the Google Generative AI SDK.

All Gemini API calls must go through this module.
No other file in this codebase may import google.generativeai directly.

Model: gemini-1.5-flash
"""

from __future__ import annotations

import logging

from google import genai  # type: ignore

from app.core.config import settings

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-3.6-flash"


class GeminiService:
    """
    Wraps the Google Generative AI SDK.

    The API key is read from settings on first use. If GEMINI_API_KEY is not
    configured, a RuntimeError is raised with a clear message.
    """

    def __init__(self) -> None:
        self._client = None

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

    def generate_review(self, prompt: str) -> str:
        """
        Send *prompt* to Gemini and return the raw text response (run review).

        Parameters
        ----------
        prompt : str
            The fully constructed prompt from prompt_builder.

        Returns
        -------
        str
            Raw text response from Gemini. May include markdown fences —
            response_parser handles stripping.

        Raises
        ------
        RuntimeError
            If GEMINI_API_KEY is missing or the API call fails.
        """
        client = self._get_client()
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            raw_text: str = response.text
            logger.info(
                "Gemini review generated successfully (model=%s, chars=%d)",
                MODEL_NAME,
                len(raw_text) if raw_text else 0,
            )
            return raw_text or ""
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc

    def generate_comparison(self, prompt: str) -> str:
        """
        Send *prompt* to Gemini and return the raw text response (run comparison).

        Reuses the same client, model, and error-handling pattern as
        generate_review. Separated for clarity and testability.

        Parameters
        ----------
        prompt : str
            The fully constructed comparison prompt from prompt_builder.

        Returns
        -------
        str
            Raw text response from Gemini.

        Raises
        ------
        RuntimeError
            If GEMINI_API_KEY is missing or the API call fails.
        """
        client = self._get_client()
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            raw_text: str = response.text
            logger.info(
                "Gemini comparison generated successfully (model=%s, chars=%d)",
                MODEL_NAME,
                len(raw_text) if raw_text else 0,
            )
            return raw_text or ""
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc

    def extract_intent(self, prompt: str) -> str:
        """
        Send *prompt* to Gemini to extract intent and filters (Ask MicroFlow).

        Returns raw text response (expected to be strict JSON).
        """
        client = self._get_client()
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            raw_text: str = response.text
            logger.info(
                "Gemini intent extraction generated successfully (model=%s, chars=%d)",
                MODEL_NAME,
                len(raw_text) if raw_text else 0,
            )
            return raw_text or ""
        except Exception as exc:
            logger.error("Gemini intent extraction failed: %s", exc)
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc

    def generate_answer(self, prompt: str) -> str:
        """
        Send *prompt* to Gemini to generate professional engineering answer (Ask MicroFlow).

        Returns raw text response (expected to be strict JSON with answer, reasoning, etc.).
        """
        client = self._get_client()
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            raw_text: str = response.text
            logger.info(
                "Gemini assistant answer generated successfully (model=%s, chars=%d)",
                MODEL_NAME,
                len(raw_text) if raw_text else 0,
            )
            return raw_text or ""
        except Exception as exc:
            logger.error("Gemini assistant generation failed: %s", exc)
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc

    def generate_dataset_analysis(self, prompt: str) -> str:
        """
        Send *prompt* to Gemini and return the raw JSON text (AI Dataset Intelligence).
        """
        client = self._get_client()
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            raw_text: str = response.text
            logger.info(
                "Gemini dataset analysis generated successfully (model=%s, chars=%d)",
                MODEL_NAME,
                len(raw_text) if raw_text else 0,
            )
            return raw_text or ""
        except Exception as exc:
            logger.error("Gemini dataset analysis failed: %s", exc)
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc

    def generate_experiment_strategy(self, prompt: str) -> str:
        """
        Send *prompt* to Gemini and return the raw JSON text (AI Experiment Strategy).
        """
        client = self._get_client()
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            raw_text: str = response.text
            logger.info(
                "Gemini experiment strategy generated successfully (model=%s, chars=%d)",
                MODEL_NAME,
                len(raw_text) if raw_text else 0,
            )
            return raw_text or ""
        except Exception as exc:
            logger.error("Gemini experiment strategy failed: %s", exc)
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc

    @property
    def model_name(self) -> str:
        return MODEL_NAME
