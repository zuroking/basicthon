"""Core chat logic for the Ollama chatbot (basicthon #19).

This module contains the "main logic" covered by G-13 / GRILL2-05:
every public function here has at least one test. HTTP lives in
``ollama_api.py``, CLI in ``cli.py`` — both excluded from the
coverage criterion (cli) or mocked in tests (HTTP).

Conversation is a plain ``list[dict]`` of
``{"role": "system"|"user"|"assistant", "content": str}`` — exactly
what Ollama's ``/api/chat`` expects. History trimming keeps the last
N exchanges so long sessions do not grow forever.
"""

from __future__ import annotations

import os

MAX_HISTORY_MESSAGES = 20


def get_base_url(var_name: str = "OLLAMA_BASE_URL") -> str:
    """Return Ollama base URL from environment.

    Args:
        var_name: env variable name. Defaults to ``OLLAMA_BASE_URL``.

    Returns:
        Base URL without trailing slash; default ``http://localhost:11434``.

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
        return "http://localhost:11434"
    return value.strip().rstrip("/")


def get_model(var_name: str = "CHAT_MODEL") -> str:
    """Return model name from environment.

    Args:
        var_name: env variable name. Defaults to ``CHAT_MODEL``.

    Returns:
        Model name; default ``tinyllama``.

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
        return "tinyllama"
    return value.strip()


def get_system_prompt(var_name: str = "SYSTEM_PROMPT") -> str | None:
    """Return optional system prompt from environment.

    Args:
        var_name: env variable name. Defaults to ``SYSTEM_PROMPT``.

    Returns:
        Prompt string or None when unset/empty.

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
        return None
    return value.strip()


def build_messages(
    history: list[dict[str, str]], system_prompt: str | None = None
) -> list[dict[str, str]]:
    """Build the messages payload for ``/api/chat``.

    Prepends an optional system prompt and trims history to the last
    ``MAX_HISTORY_MESSAGES`` user/assistant entries so requests stay
    small on long sessions.

    Args:
        history: prior turns as ``{"role", "content"}`` dicts.
        system_prompt: optional persona prepended to every request.

    Returns:
        New list starting with the system message (if any), followed by
        trimmed history. Input list is not mutated.

    Raises:
        ValueError: if ``history`` is not a list or items malformed.
    """
    if not isinstance(history, list):
        raise ValueError("history must be a list")
    valid_roles = {"user", "assistant"}
    for item in history:
        if not isinstance(item, dict):
            raise ValueError("history items must be dicts")
        role = item.get("role")
        content = item.get("content")
        if (
            not isinstance(role, str)
            or role not in valid_roles
            or not isinstance(content, str)
        ):
            raise ValueError(
                "history items must have role user/assistant and content str"
            )
    messages: list[dict[str, str]] = []
    if system_prompt is not None and system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})
    trimmed = [
        {"role": m["role"], "content": m["content"]}
        for m in history[-MAX_HISTORY_MESSAGES:]
    ]
    return messages + trimmed


def add_turn(
    history: list[dict[str, str]], role: str, content: str
) -> list[dict[str, str]]:
    """Append one turn and return the new history list.

    Args:
        history: current conversation.
        role: ``user`` or ``assistant``.
        content: message text (non-empty after strip).

    Returns:
        New list with the appended turn (input not mutated).

    Raises:
        ValueError: on invalid args.
    """
    if role not in ("user", "assistant"):
        raise ValueError("role must be user or assistant")
    if not isinstance(content, str):
        raise ValueError("content must be a string")
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("content must not be empty")
    return history + [{"role": role, "content": cleaned}]


def extract_reply(response: dict[str, object]) -> str:
    """Extract assistant text from an Ollama chat response.

    Args:
        response: parsed JSON like
            ``{"message": {"role": "assistant", "content": "..."}, ...}``.

    Returns:
        Assistant content string.

    Raises:
        ValueError: if response shape is unexpected or empty content.
    """
    if not isinstance(response, dict):
        raise ValueError("response must be a dict")
    message = response.get("message")
    if not isinstance(message, dict):
        raise ValueError("response has no message dict")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("response has empty content")
    return content.strip()
