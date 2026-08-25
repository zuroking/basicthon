"""Tests for telegram_bot — covers every public function (G-13).

All HTTP calls are mocked via monkeypatching ``httpx.post`` —
no network, no real token (G-12).
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from telegram_bot.api import (
    TelegramClient,
    build_method_url,
    get_api_url,
    get_bot_token,
    get_poll_timeout,
    next_offset,
)
from telegram_bot.bot import (
    extract_chat_id,
    extract_message,
    extract_text,
    handle_text,
    handle_update,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("BOT_TOKEN", "TELEGRAM_API_URL", "POLL_TIMEOUT"):
        monkeypatch.delenv(var, raising=False)
    yield


# ---- bot.py: extraction ----


def test_extract_message_present() -> None:
    update = {"update_id": 1, "message": {"text": "hi"}}
    assert extract_message(update) == {"text": "hi"}


def test_extract_message_missing() -> None:
    assert extract_message({"update_id": 1}) is None
    assert extract_message({"message": "not-a-dict"}) is None


def test_extract_message_invalid() -> None:
    with pytest.raises(ValueError, match="update must be a dict"):
        extract_message("no")  # type: ignore[arg-type]


def test_extract_chat_id() -> None:
    assert extract_chat_id({"chat": {"id": 42}}) == 42
    assert extract_chat_id({"chat": {"id": "42"}}) is None
    assert extract_chat_id({}) is None
    assert extract_chat_id({"chat": {}}) is None


def test_extract_chat_id_invalid() -> None:
    with pytest.raises(ValueError, match="message must be a dict"):
        extract_chat_id(123)  # type: ignore[arg-type]


def test_extract_text() -> None:
    assert extract_text({"text": "hello"}) == "hello"
    assert extract_text({"text": ""}) == ""
    assert extract_text({}) is None
    # non-text message types (photo etc.) have no text field
    assert extract_text({"photo": []}) is None


def test_extract_text_invalid() -> None:
    with pytest.raises(ValueError, match="message must be a dict"):
        extract_text(None)  # type: ignore[arg-type]


# ---- bot.py: handle_text ----


def test_handle_start() -> None:
    reply = handle_text("/start")
    assert reply is not None
    assert "basicthon bot #18" in reply
    assert "/help" in reply


def test_handle_help() -> None:
    reply = handle_text("/help")
    assert reply is not None
    assert "/echo <text>" in reply


def test_handle_echo() -> None:
    assert handle_text("/echo hello world") == "hello world"
    assert handle_text("  /echo   spaced   ") == "spaced"
    assert handle_text("/echo") == "Usage: /echo <text>"


def test_handle_fallback() -> None:
    assert handle_text("just text") == "You said: just text"
    assert handle_text("  hi  ") == "You said: hi"


def test_handle_empty() -> None:
    assert handle_text("") is None
    assert handle_text("   ") is None


def test_handle_text_invalid() -> None:
    with pytest.raises(ValueError, match="text must be a string"):
        handle_text(123)  # type: ignore[arg-type]


# ---- bot.py: handle_update ----


def make_update(text: str, chat_id: int = 1) -> dict[str, Any]:
    """Build a minimal Bot-API-like update."""
    return {
        "update_id": 100,
        "message": {"chat": {"id": chat_id}, "text": text},
    }


def test_handle_update_full() -> None:
    result = handle_update(make_update("/echo x"))
    assert result == (1, "x")


def test_handle_update_no_reply_cases() -> None:
    # no message
    assert handle_update({"update_id": 1}) is None
    # no chat id
    assert handle_update({"message": {"text": "hi"}}) is None
    # no text (e.g. photo message)
    photo = {"message": {"chat": {"id": 5}, "photo": []}}
    assert handle_update(photo) is None
    # empty text -> handle_text returns None
    empty = {"message": {"chat": {"id": 5}, "text": "   "}}
    assert handle_update(empty) is None


def test_handle_update_invalid() -> None:
    with pytest.raises(ValueError, match="update must be a dict"):
        handle_update([1, 2])  # type: ignore[arg-type]


# ---- api.py: env helpers ----


def test_get_bot_token(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="BOT_TOKEN is not set"):
        get_bot_token()
    monkeypatch.setenv("BOT_TOKEN", " 123:abc ")
    assert get_bot_token() == "123:abc"


def test_get_bot_token_custom_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_TOKEN", "x:y")
    assert get_bot_token("MY_TOKEN") == "x:y"


def test_get_bot_token_invalid() -> None:
    with pytest.raises(ValueError):
        get_bot_token("")
    with pytest.raises(ValueError):
        get_bot_token(123)  # type: ignore[arg-type]


def test_get_api_url_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_API_URL", raising=False)
    assert get_api_url() == "https://api.telegram.org"


def test_get_api_url_custom(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_API_URL", "http://localhost:8081/")
    assert get_api_url() == "http://localhost:8081"


def test_get_api_url_invalid() -> None:
    with pytest.raises(ValueError):
        get_api_url("")
    with pytest.raises(ValueError):
        get_api_url(123)  # type: ignore[arg-type]


def test_get_poll_timeout_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POLL_TIMEOUT", raising=False)
    assert get_poll_timeout() == 30


def test_get_poll_timeout_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POLL_TIMEOUT", "10")
    assert get_poll_timeout() == 10


def test_get_poll_timeout_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POLL_TIMEOUT", "bad")
    with pytest.raises(ValueError, match="must be an integer"):
        get_poll_timeout()
    monkeypatch.setenv("POLL_TIMEOUT", "0")
    with pytest.raises(ValueError, match="between 1 and 300"):
        get_poll_timeout()
    monkeypatch.setenv("POLL_TIMEOUT", "500")
    with pytest.raises(ValueError):
        get_poll_timeout()


def test_get_poll_timeout_invalid_var() -> None:
    with pytest.raises(ValueError):
        get_poll_timeout("")
    with pytest.raises(ValueError):
        get_poll_timeout(123)  # type: ignore[arg-type]


def test_build_method_url() -> None:
    url = build_method_url("https://api.telegram.org", "123:abc", "getMe")
    assert url == "https://api.telegram.org/bot123:abc/getMe"
    url2 = build_method_url("http://localhost:8081/", "t", "sendMessage")
    assert url2 == "http://localhost:8081/bott/sendMessage"


def test_build_method_url_invalid() -> None:
    with pytest.raises(ValueError):
        build_method_url("", "t", "getMe")
    with pytest.raises(ValueError):
        build_method_url("https://x", "", "getMe")
    with pytest.raises(ValueError):
        build_method_url("https://x", "t", "")
    with pytest.raises(ValueError):
        build_method_url(123, "t", "getMe")  # type: ignore[arg-type]


# ---- api.py: TelegramClient with mocked HTTP ----


class FakeResponse:
    """Minimal stand-in for httpx.Response."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def json(self) -> dict[str, Any]:
        return self._data


def install_fake(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[tuple[str, dict[str, Any]]],
    results: list[dict[str, Any]],
) -> None:
    """Replace httpx.post with a fake capturing calls."""

    def fake_post(url: str, json: dict[str, Any], timeout: Any) -> FakeResponse:
        calls.append((url, json))
        if results:
            return FakeResponse(results.pop(0))
        # default success for extra calls (e.g. sendMessage)
        return FakeResponse({"ok": True, "result": {}})

    monkeypatch.setattr(httpx, "post", fake_post)


def test_client_reads_env_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123:abc")
    client = TelegramClient()
    assert client.token == "123:abc"
    assert client.api_url == "https://api.telegram.org"


def test_client_explicit_args() -> None:
    client = TelegramClient(token="t1", api_url="http://mock/")
    assert client.token == "t1"
    assert client.api_url == "http://mock"


def test_client_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="BOT_TOKEN is not set"):
        TelegramClient()


def test_get_me_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    install_fake(
        monkeypatch,
        calls,
        [{"ok": True, "result": {"id": 7, "username": "basicthon_bot"}}],
    )
    client = TelegramClient(token="tk", api_url="http://mock")
    me = client.get_me()
    assert me["username"] == "basicthon_bot"
    assert calls[0][0] == "http://mock/bottk/getMe"
    assert calls[0][1] == {}


def test_get_updates_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    updates = [
        {"update_id": 1, "message": {"chat": {"id": 9}, "text": "a"}},
        {"update_id": 2, "message": {"chat": {"id": 9}, "text": "b"}},
    ]
    install_fake(monkeypatch, calls, [{"ok": True, "result": updates}])
    client = TelegramClient(token="tk", api_url="http://mock")
    got = client.get_updates(0, 30)
    assert got == updates
    assert calls[0][1] == {"offset": 0, "timeout": 30}


def test_get_updates_empty_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    install_fake(monkeypatch, calls, [{"ok": True, "result": []}])
    client = TelegramClient(token="tk", api_url="http://mock")
    assert client.get_updates(5, 30) == []


def test_get_updates_bad_args() -> None:
    client = TelegramClient(token="tk", api_url="http://mock")
    with pytest.raises(ValueError):
        client.get_updates("0", 30)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        client.get_updates(0, 0)
    with pytest.raises(ValueError):
        client.get_updates(True, 30)


def test_send_message_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    sent = {"message_id": 3, "chat": {"id": 4}, "text": "reply"}
    install_fake(monkeypatch, calls, [{"ok": True, "result": sent}])
    client = TelegramClient(token="tk", api_url="http://mock")
    out = client.send_message(4, "reply")
    assert out["text"] == "reply"
    assert calls[0][0] == "http://mock/bottk/sendMessage"
    assert calls[0][1] == {"chat_id": 4, "text": "reply"}


def test_send_message_bad_args() -> None:
    client = TelegramClient(token="tk", api_url="http://mock")
    with pytest.raises(ValueError):
        client.send_message("4", "hi")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        client.send_message(4, "")
    with pytest.raises(ValueError):
        client.send_message(4, "   ")


def test_api_error_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    install_fake(
        monkeypatch,
        calls,
        [{"ok": False, "description": "Unauthorized"}],
    )
    client = TelegramClient(token="bad", api_url="http://mock")
    with pytest.raises(RuntimeError, match="getMe failed: Unauthorized"):
        client.get_me()


def test_network_error_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(url: str, json: dict[str, Any], timeout: Any) -> Any:
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx, "post", fake_post)
    client = TelegramClient(token="tk", api_url="http://mock")
    with pytest.raises(RuntimeError, match="network error calling getMe"):
        client.get_me()


def test_unexpected_result_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    install_fake(monkeypatch, calls, [{"ok": True, "result": "not-a-list"}])
    client = TelegramClient(token="tk", api_url="http://mock")
    with pytest.raises(RuntimeError, match="unexpected getUpdates"):
        client.get_updates(0, 30)


# ---- api.py: next_offset ----


def test_next_offset() -> None:
    assert next_offset([]) is None
    assert next_offset([{"update_id": 1}, {"update_id": 5}]) == 6
    assert next_offset([{"foo": 1}]) is None
    # bool ids are not integers for our purposes
    assert next_offset([{"update_id": True}]) is None
    assert next_offset([{"update_id": 3}, {"junk": True}]) == 4


def test_next_offset_invalid() -> None:
    with pytest.raises(ValueError, match="updates must be a list"):
        next_offset("nope")  # type: ignore[arg-type]


# ---- end-to-end through the loop pieces (still mocked HTTP) ----


def test_batch_processing_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate: fetch two updates -> compute replies -> send them."""
    calls: list[tuple[str, dict[str, Any]]] = []
    batch = [
        make_update("/start", chat_id=11),
        make_update("/echo ping", chat_id=22),
    ]
    install_fake(monkeypatch, calls, [{"ok": True, "result": batch}])
    client = TelegramClient(token="tk", api_url="http://mock")
    got = client.get_updates(0, 30)

    replies = [handle_update(u) for u in got]
    assert replies[0] == (11, handle_text("/start"))
    assert replies[1] == (22, "ping")

    for chat_id, text in replies:
        if (chat_id, text) is None:
            continue
        client.send_message(chat_id, text or "")

    send_calls = [c for c in calls if "sendMessage" in c[0]]
    assert len(send_calls) == 2
    assert send_calls[0][1]["chat_id"] == 11
    assert send_calls[1][1]["chat_id"] == 22

    assert next_offset(got) == 101
