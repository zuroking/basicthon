"""Pure update-handling logic for the Telegram bot (basicthon #18).

This module contains the "main logic" covered by G-13 / GRILL2-05:
every public function here has at least one test. It knows nothing
about HTTP — ``api.py`` talks to the Bot API, ``cli.py`` runs polling.

Commands:
- /start  -> greeting
- /help   -> list of commands
- /echo X -> replies with X (stripped)
- anything else -> fallback answer

Update shape follows the official Bot API: an update dict may carry a
``message`` with ``chat.id`` and ``text``. Missing/odd fields are
handled explicitly so tests stay deterministic.
"""

from __future__ import annotations


def extract_message(update: dict[str, object]) -> dict[str, object] | None:
    """Return the ``message`` dict from an update, else None.

    Args:
        update: raw update object as returned by ``getUpdates``.

    Returns:
        The message mapping if present and valid type, else None.

    Raises:
        ValueError: if ``update`` is not a dict.
    """
    if not isinstance(update, dict):
        raise ValueError("update must be a dict")
    message = update.get("message")
    if isinstance(message, dict):
        return message
    return None


def extract_chat_id(message: dict[str, object]) -> int | None:
    """Return ``chat.id`` from a message dict.

    Args:
        message: message mapping.

    Returns:
        Chat id as int, or None when missing/not valid.

    Raises:
        ValueError: if ``message`` is not a dict.
    """
    if not isinstance(message, dict):
        raise ValueError("message must be a dict")
    chat = message.get("chat")
    if not isinstance(chat, dict):
        return None
    chat_id = chat.get("id")
    if isinstance(chat_id, bool) or not isinstance(chat_id, int):
        return None
    return chat_id


def extract_text(message: dict[str, object]) -> str | None:
    """Return ``text`` from a message dict.

    Args:
        message: message mapping.

    Returns:
        Text string (may be empty), or None when missing/not str.

    Raises:
        ValueError: if ``message`` is not a dict.
    """
    if not isinstance(message, dict):
        raise ValueError("message must be a dict")
    text = message.get("text")
    if isinstance(text, str):
        return text
    return None


def handle_text(text: str) -> str | None:
    """Turn incoming text into the reply text.

    Args:
        text: raw message text.

    Returns:
        Reply string; None means "do not reply" (empty input).

    Raises:
        ValueError: if ``text`` is not a string.
    """
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    stripped = text.strip()
    if not stripped:
        return None
    if stripped == "/start":
        return (
            "Hi! I am basicthon bot #18.\n"
            "Commands:\n"
            "/help - show commands\n"
            "/echo <text> - repeat after you\n"
            "Or just send me any message."
        )
    if stripped == "/help":
        return (
            "Commands:\n/start - greeting\n/help - this list\n"
            "/echo <text> - repeat your text"
        )
    if stripped.startswith("/echo"):
        rest = stripped[len("/echo") :].strip()
        if not rest:
            return "Usage: /echo <text>"
        return rest
    return f"You said: {stripped}"


def handle_update(update: dict[str, object]) -> tuple[int, str] | None:
    """Process one update into ``(chat_id, reply_text)``.

    Args:
        update: raw update object.

    Returns:
        Tuple of chat id and reply text, or None when there is nothing
        to reply (no message, no chat id, no text, empty text).

    Raises:
        ValueError: if ``update`` is not a dict.
    """
    if not isinstance(update, dict):
        raise ValueError("update must be a dict")
    message = extract_message(update)
    if message is None:
        return None
    chat_id = extract_chat_id(message)
    if chat_id is None:
        return None
    text = extract_text(message)
    if text is None:
        return None
    reply = handle_text(text)
    if reply is None:
        return None
    return (chat_id, reply)
