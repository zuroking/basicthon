"""Tests for ollama_chatbot — covers every public function (G-13).

All HTTP calls are mocked via monkeypatching ``httpx.post`` —
no network, no real inference (G-12).
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from ollama_chatbot.chat import (
    MAX_HISTORY_MESSAGES,
    add_turn,
    build_messages,
    extract_reply,
    get_base_url,
    get_model,
    get_system_prompt,
)
from ollama_chatbot.ollama_api import OllamaClient, build_chat_url


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("OLLAMA_BASE_URL", "CHAT_MODEL", "SYSTEM_PROMPT"):
        monkeypatch.delenv(var, raising=False)
    yield


# ---- env helpers ----


def test_get_base_url_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    assert get_base_url() == "http://localhost:11434"


def test_get_base_url_custom(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:9999/")
    assert get_base_url() == "http://127.0.0.1:9999"


def test_get_base_url_invalid() -> None:
    with pytest.raises(ValueError):
        get_base_url("")
    with pytest.raises(ValueError):
        get_base_url(123)  # type: ignore[arg-type]


def test_get_model_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CHAT_MODEL", raising=False)
    assert get_model() == "tinyllama"


def test_get_model_custom(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAT_MODEL", "llama3")
    assert get_model() == "llama3"
    monkeypatch.setenv("CHAT_MODEL", "  qwen:4b  ")
    assert get_model() == "qwen:4b"


def test_get_model_invalid() -> None:
    with pytest.raises(ValueError):
        get_model("")
    with pytest.raises(ValueError):
        get_model(None)  # type: ignore[arg-type]


def test_get_system_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SYSTEM_PROMPT", raising=False)
    assert get_system_prompt() is None
    monkeypatch.setenv("SYSTEM_PROMPT", "  Be brief. ")
    assert get_system_prompt() == "Be brief."
    monkeypatch.setenv("SYSTEM_PROMPT", "   ")
    assert get_system_prompt() is None


def test_get_system_prompt_invalid() -> None:
    with pytest.raises(ValueError):
        get_system_prompt("")
    with pytest.raises(ValueError):
        get_system_prompt(42)  # type: ignore[arg-type]


# ---- build_messages / add_turn / extract_reply ----


def test_build_messages_empty_no_prompt() -> None:
    assert build_messages([]) == []


def test_build_messages_with_prompt() -> None:
    msgs = build_messages([], system_prompt="You are terse.")
    assert msgs == [{"role": "system", "content": "You are terse."}]


def test_build_messages_keeps_history_order() -> None:
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
        {"role": "user", "content": "bye"},
    ]
    msgs = build_messages(history, system_prompt="sys")
    assert [m["role"] for m in msgs] == ["system", "user", "assistant", "user"]
    # input not mutated
    assert len(history) == 3


def test_build_messages_trims_long_history() -> None:
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": str(i)}
        for i in range(MAX_HISTORY_MESSAGES + 10)
    ]
    msgs = build_messages(history)
    assert len(msgs) == MAX_HISTORY_MESSAGES
    assert msgs[-1]["content"] == str(len(history) - 1)


def test_build_messages_invalid() -> None:
    with pytest.raises(ValueError, match="history must be a list"):
        build_messages("no")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="history items must be dicts"):
        build_messages(["no"])  # type: ignore[list-item]
    bad_role = [{"role": "system", "content": "x"}]
    with pytest.raises(ValueError, match="role user/assistant"):
        build_messages(bad_role)  # type: ignore[arg-type]
    bad_content = [{"role": "user", "content": 5}]
    with pytest.raises(ValueError, match="content str"):
        build_messages(bad_content)  # type: ignore[arg-type]


def test_add_turn_appends() -> None:
    h = add_turn([], "user", "hello")
    assert h == [{"role": "user", "content": "hello"}]
    h2 = add_turn(h, "assistant", "hi there")
    assert h2 == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]
    # original untouched
    assert len(h) == 1


def test_add_turn_strips_content() -> None:
    assert add_turn([], "user", "  hi  ") == [{"role": "user", "content": "hi"}]


def test_add_turn_invalid() -> None:
    with pytest.raises(ValueError, match="role must be user or assistant"):
        add_turn([], "system", "x")
    with pytest.raises(ValueError):
        add_turn([], "user", "")
    with pytest.raises(ValueError):
        add_turn([], "user", "   ")
    with pytest.raises(ValueError):
        add_turn([], "user", 123)  # type: ignore[arg-type]


def test_extract_reply_ok() -> None:
    resp = {"message": {"role": "assistant", "content": "  Hello!  "}}
    assert extract_reply(resp) == "Hello!"


def test_extract_reply_invalid() -> None:
    with pytest.raises(ValueError, match="response must be a dict"):
        extract_reply("no")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="no message dict"):
        extract_reply({})
    with pytest.raises(ValueError, match="empty content"):
        extract_reply({"message": {"role": "assistant", "content": ""}})
    with pytest.raises(ValueError, match="empty content"):
        extract_reply({"message": {"role": "assistant"}})


# ---- ollama_api ----


def test_build_chat_url() -> None:
    assert build_chat_url("http://localhost:11434") == "http://localhost:11434/api/chat"
    assert build_chat_url("http://host/") == "http://host/api/chat"


def test_build_chat_url_invalid() -> None:
    with pytest.raises(ValueError):
        build_chat_url("")
    with pytest.raises(ValueError):
        build_chat_url("   ")
    with pytest.raises(ValueError):
        build_chat_url(None)  # type: ignore[arg-type]


class FakeResponse:
    """Minimal stand-in for httpx.Response."""

    def __init__(self, data: dict[str, Any], status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self._data


def install_fake(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[tuple[str, dict[str, Any]]],
    results: list[FakeResponse],
) -> None:
    def fake_post(url: str, json: dict[str, Any], timeout: Any) -> FakeResponse:
        calls.append((url, json))
        return results.pop(0)

    monkeypatch.setattr(httpx, "post", fake_post)


def make_ollama_response(text: str) -> dict[str, Any]:
    return {"message": {"role": "assistant", "content": text}, "done": True}


def test_client_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient()
    assert client.base_url == "http://localhost:11434"
    assert client.model == "tinyllama"


def test_client_explicit_and_env(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient(base_url="http://h:1/", model=" m2 ")
    assert client.base_url == "http://h:1"
    assert client.model == "m2"
    monkeypatch.setenv("CHAT_MODEL", "envmodel")
    client2 = OllamaClient(base_url="http://h:1")
    assert client2.model == "envmodel"


def test_chat_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    install_fake(
        monkeypatch,
        calls,
        [FakeResponse(make_ollama_response("Hi human!"))],
    )
    client = OllamaClient(base_url="http://mock", model="m1")
    messages = build_messages([{"role": "user", "content": "hello"}])
    data = client.chat(messages)
    assert extract_reply(data) == "Hi human!"
    url, payload = calls[0]
    assert url == "http://mock/api/chat"
    assert payload["model"] == "m1"
    assert payload["stream"] is False
    assert payload["messages"][0] == {"role": "user", "content": "hello"}


def test_chat_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    install_fake(
        monkeypatch,
        calls,
        [FakeResponse({"error": "model not found"}, status_code=404)],
    )
    client = OllamaClient(base_url="http://mock", model="missing")
    with pytest.raises(RuntimeError, match="HTTP 404"):
        client.chat([{"role": "user", "content": "hi"}])


def test_chat_bad_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    install_fake(monkeypatch, calls, [FakeResponse(["not-a-dict"])])
    client = OllamaClient(base_url="http://mock")
    with pytest.raises(RuntimeError, match="unexpected ollama response shape"):
        client.chat([{"role": "user", "content": "hi"}])


def test_chat_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url: str, json: dict[str, Any], timeout: Any) -> Any:
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", fake_post)
    client = OllamaClient(base_url="http://mock")
    with pytest.raises(RuntimeError, match="network error talking to Ollama"):
        client.chat([{"role": "user", "content": "hi"}])


def test_chat_invalid_messages() -> None:
    client = OllamaClient(base_url="http://mock")
    with pytest.raises(ValueError, match="non-empty list"):
        client.chat([])
    with pytest.raises(ValueError):
        client.chat("no")  # type: ignore[arg-type]


# ---- end-to-end conversation flow (still mocked HTTP) ----


def test_conversation_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    responses = [
        FakeResponse(make_ollama_response("first answer")),
        FakeResponse(make_ollama_response("second answer")),
    ]
    install_fake(monkeypatch, calls, responses)
    client = OllamaClient(base_url="http://mock", model="m")

    history: list[dict[str, str]] = []
    for user_text, expected in [("one", "first answer"), ("two", "second answer")]:
        history = add_turn(history, "user", user_text)
        payload = build_messages(history, "be nice")
        reply = extract_reply(client.chat(payload))
        assert reply == expected
        history = add_turn(history, "assistant", reply)

    assert len(calls) == 2
    second_payload = calls[1][1]["messages"]
    roles = [m["role"] for m in second_payload]
    assert roles == ["system", "user", "assistant", "user"]
