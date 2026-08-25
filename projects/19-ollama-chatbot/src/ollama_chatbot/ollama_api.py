"""Thin Ollama HTTP client over ``httpx`` (basicthon #19).

Only one endpoint is used: ``POST /api/chat``. The client is sync and
non-streaming to stay beginner-readable; real inference is never run
in CI — tests monkeypatch ``httpx.post`` (G-12).
"""

from __future__ import annotations

from typing import Any

import httpx

from ollama_chatbot.chat import get_base_url, get_model


def build_chat_url(base_url: str) -> str:
    """Build the full ``/api/chat`` URL.

    Args:
        base_url: Ollama base URL without trailing slash.

    Returns:
        URL like ``{base_url}/api/chat``.

    Raises:
        ValueError: if base URL empty or not a string.
    """
    if not isinstance(base_url, str):
        raise ValueError("base_url must be a string")
    base = base_url.strip().rstrip("/")
    if not base:
        raise ValueError("base_url must not be empty")
    return f"{base}/api/chat"


class OllamaClient:
    """Minimal sync client for Ollama's ``/api/chat``."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        """Create a client.

        Args:
            base_url: server root; if None, read via env helper.
            model: model name; if None, read via env helper.
        """
        self.base_url = (
            base_url.strip().rstrip("/")
            if isinstance(base_url, str) and base_url.strip()
            else get_base_url()
        )
        self.model = (
            model.strip() if isinstance(model, str) and model.strip() else get_model()
        )

    def chat(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Send a chat request and return parsed JSON response.

        Args:
            messages: payload built by
                :func:`ollama_chatbot.chat.build_messages`.

        Returns:
            Parsed response dict (contains ``message.content``).

        Raises:
            ValueError: if ``messages`` is not a non-empty list.
            RuntimeError: on network errors, timeouts, HTTP errors or
                malformed responses.
        """
        if not isinstance(messages, list) or not messages:
            raise ValueError("messages must be a non-empty list")
        url = build_chat_url(self.base_url)
        payload = {"model": self.model, "messages": messages, "stream": False}
        try:
            resp = httpx.post(url, json=payload, timeout=120)
        except httpx.HTTPError as exc:
            raise RuntimeError(f"network error talking to Ollama at {url}") from exc
        if resp.status_code != 200:
            raise RuntimeError(f"ollama returned HTTP {resp.status_code}")
        data = resp.json()
        if not isinstance(data, dict):
            raise RuntimeError("unexpected ollama response shape")
        return data
