"""Thin Telegram Bot API client over ``httpx`` (basicthon #18).

Only the three calls this bot needs: ``getMe`` (sanity check),
``getUpdates`` (long polling) and ``sendMessage`` (replies).
All methods are sync — the CLI runs a simple sequential loop.

The token is read from env via :func:`get_bot_token` and is never
logged or embedded into exceptions. Base URL can be overridden with
``TELEGRAM_API_URL`` for tests against a mock server.
"""

from __future__ import annotations

import os
from typing import Any

import httpx


def get_bot_token(var_name: str = "BOT_TOKEN") -> str:
    """Return the bot token from environment.

    Args:
        var_name: env variable name. Defaults to ``BOT_TOKEN``.

    Returns:
        Stripped token string.

    Raises:
        ValueError: if missing/empty or ``var_name`` invalid.
    """
    if not isinstance(var_name, str):
        raise ValueError("var_name must be a string")
    cleaned = var_name.strip()
    if not cleaned:
        raise ValueError("var_name must be a non-empty string")
    value = os.environ.get(cleaned)
    if value is None or not value.strip():
        raise ValueError("BOT_TOKEN is not set, see .env.example")
    return value.strip()


def get_api_url(var_name: str = "TELEGRAM_API_URL") -> str:
    """Return Bot API base URL from environment.

    Args:
        var_name: env variable name. Defaults to ``TELEGRAM_API_URL``.

    Returns:
        Base URL; default ``https://api.telegram.org``.

    Raises:
        ValueError: if ``var_name`` invalid.
    """
    if not isinstance(var_name, str):
        raise ValueError("var_name must be a string")
    cleaned = var_name.strip()
    if not cleaned:
        raise ValueError("var_name must be a non-empty string")
    value = os.environ.get(cleaned)
    if value is None or not value.strip():
        return "https://api.telegram.org"
    return value.strip().rstrip("/")


def get_poll_timeout(var_name: str = "POLL_TIMEOUT") -> int:
    """Return long-polling timeout in seconds from environment.

    Args:
        var_name: env variable name. Defaults to ``POLL_TIMEOUT``.

    Returns:
        Timeout 1..300, default ``30``.

    Raises:
        ValueError: if invalid.
    """
    if not isinstance(var_name, str):
        raise ValueError("var_name must be a string")
    cleaned = var_name.strip()
    if not cleaned:
        raise ValueError("var_name must be a non-empty string")
    raw = os.environ.get(cleaned)
    if raw is None or not raw.strip():
        return 30
    try:
        timeout = int(raw.strip())
    except ValueError as exc:
        raise ValueError("poll timeout must be an integer") from exc
    if timeout < 1 or timeout > 300:
        raise ValueError("poll timeout must be between 1 and 300")
    return timeout


def build_method_url(api_url: str, token: str, method: str) -> str:
    """Build full URL for a Bot API method.

    Args:
        api_url: base URL without trailing slash.
        token: bot token.
        method: e.g. ``getMe``.

    Returns:
        URL like ``{api_url}/bot{token}/{method}``.

    Raises:
        ValueError: on empty/invalid args.
    """
    if not all(isinstance(a, str) for a in (api_url, token, method)):
        raise ValueError("args must be strings")
    base = api_url.strip().rstrip("/")
    tok = token.strip()
    mth = method.strip()
    if not base or not tok or not mth:
        raise ValueError("api_url, token and method must not be empty")
    return f"{base}/bot{tok}/{mth}"


class TelegramClient:
    """Small sync client for the parts of the Bot API we use."""

    def __init__(self, token: str | None = None, api_url: str | None = None):
        """Create a client.

        Args:
            token: bot token; if None read via ``get_bot_token()``.
            api_url: base URL; if None read via ``get_api_url()``.

        Raises:
            ValueError: if resolved values are empty.
        """
        self.token = (
            token.strip()
            if (isinstance(token, str) and token.strip())
            else get_bot_token()
        )
        self.api_url = (
            api_url.strip().rstrip("/")
            if (isinstance(api_url, str) and api_url.strip())
            else get_api_url()
        )

    def _post(self, method: str, payload: dict[str, Any]) -> Any:
        """POST JSON to a Bot API method and return its result.

        Args:
            method: Bot API method name.
            payload: JSON body.

        Returns:
            The ``result`` field of the response.

        Raises:
            RuntimeError: on network errors or API error responses.
        """
        url = build_method_url(self.api_url, self.token, method)
        try:
            resp = httpx.post(url, json=payload, timeout=35)
        except httpx.HTTPError as exc:
            raise RuntimeError(f"network error calling {method}") from exc
        data = resp.json()
        if not data.get("ok", False):
            description = str(data.get("description", "unknown error"))
            raise RuntimeError(f"{method} failed: {description}")
        return data.get("result")

    def get_me(self) -> dict[str, Any]:
        """Return bot info from ``getMe``."""
        result = self._post("getMe", {})
        if not isinstance(result, dict):
            raise RuntimeError("unexpected getMe response")
        return result

    def get_updates(self, offset: int, timeout: int) -> list[dict[str, Any]]:
        """Fetch updates with id >= ``offset`` using long polling.

        Args:
            offset: last processed update_id + 1.
            timeout: server-side long-poll timeout in seconds.

        Returns:
            List of update dicts (possibly empty).

        Raises:
            RuntimeError: on network/API errors.
            ValueError: if args have wrong types.
        """
        if isinstance(offset, bool) or not isinstance(offset, int):
            raise ValueError("offset must be an integer")
        if isinstance(timeout, bool) or not isinstance(timeout, int):
            raise ValueError("timeout must be an integer")
        if timeout < 1 or timeout > 300:
            raise ValueError("timeout must be between 1 and 300")
        result = self._post("getUpdates", {"offset": offset, "timeout": timeout})
        if not isinstance(result, list):
            raise RuntimeError("unexpected getUpdates response")
        return [u for u in result if isinstance(u, dict)]

    def send_message(self, chat_id: int, text: str) -> dict[str, Any]:
        """Send a text message to a chat.

        Args:
            chat_id: target chat id.
            text: message text (non-empty after strip).

        Returns:
            Sent message object.

        Raises:
            ValueError: on wrong types / empty text.
            RuntimeError: on network/API errors.
        """
        if isinstance(chat_id, bool) or not isinstance(chat_id, int):
            raise ValueError("chat_id must be an integer")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")
        result = self._post("sendMessage", {"chat_id": chat_id, "text": text})
        if not isinstance(result, dict):
            raise RuntimeError("unexpected sendMessage response")
        return result


def next_offset(updates: list[dict[str, Any]]) -> int | None:
    """Compute the next ``offset`` from a batch of updates.

    Args:
        updates: updates returned by ``get_updates``.

    Returns:
        Max update_id + 1, or None when the batch is empty or has no
        valid integer ids.

    Raises:
        ValueError: if ``updates`` is not a list.
    """
    if not isinstance(updates, list):
        raise ValueError("updates must be a list")
    ids: list[int] = []
    for u in updates:
        if not isinstance(u, dict):
            continue
        uid = u.get("update_id")
        if isinstance(uid, int) and not isinstance(uid, bool):
            ids.append(uid)
    if not ids:
        return None
    return max(ids) + 1
