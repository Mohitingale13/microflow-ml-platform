"""
ai/cache_service.py — Deterministic prompt hashing for review caching.

Computes a SHA-256 hash of the exact prompt string passed to Gemini.
If the run state has not changed, the hash is identical and the cached
review is returned without an API call.
"""

import hashlib


def compute_prompt_hash(prompt: str) -> str:
    """Return the SHA-256 hex digest of *prompt* (UTF-8 encoded)."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
