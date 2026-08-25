# 19 — Chat Bot over Local LLM (Ollama)

Isolated beginner project from the `basicthon` series (Systems & Integration).

**What you learn (lock scope):** talking to a locally running LLM server (Ollama `POST /api/chat`) with `httpx`, managing conversation history as a plain list of role/content messages, and keeping the chat loop testable without any inference. The project is built in three stages: minimal — pure `build_messages`/`add_turn`/`extract_reply` over a `list[{"role","content"}]`, thin `OllamaClient.chat()`; improved — env config (`OLLAMA_BASE_URL`, `CHAT_MODEL`, optional `SYSTEM_PROMPT`), history trimming to the last 20 turns, defensive extraction and `RuntimeError` on network/HTTP errors; production-like — typed, tested, `ruff/black/mypy --strict` clean, `pytest` green for every public function in `src/ollama_chatbot/chat.py` and `src/ollama_chatbot/ollama_api.py` (excl. `cli.py` per §5), all HTTP mocked in tests (no real inference — G-12), `argparse` REPL CLI.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` contains `httpx==0.27.2` (pinned per G-17).

## Setup

You need a local [Ollama](https://ollama.com) server and a small model:

```bash
ollama serve                 # starts http://localhost:11434
ollama pull tinyllama        # ~640 MB; any chat-capable model works
```

Environment (see `.env.example`; all optional):

```bash
# Linux/macOS
export OLLAMA_BASE_URL="http://localhost:11434"
export CHAT_MODEL="tinyllama"
export SYSTEM_PROMPT="You are a helpful assistant. Answer briefly."

# Windows PowerShell
$env:OLLAMA_BASE_URL="http://localhost:11434"
$env:CHAT_MODEL="tinyllama"
$env:SYSTEM_PROMPT="You are a helpful assistant. Answer briefly."
```

## Usage

```bash
python -m ollama_chatbot
# or after pip install -e .
ollama-chatbot --model tinyllama --url http://localhost:11434
```

Session example:

```text
Chatting with 'tinyllama' at http://localhost:11434
Type your message; /exit or Ctrl+C to quit.
you> hi, who are you?
bot> I am a language model running locally via Ollama.
you> /exit
Bye!
```

Or as a library:

```python
from ollama_chatbot import (
    add_turn, build_messages, extract_reply, OllamaClient,
    get_base_url, get_model,
)

print(get_base_url())  # "http://localhost:11434" if env unset
print(get_model())     # "tinyllama" if env unset

history = add_turn([], "user", "hello")
payload = build_messages(history, system_prompt="Be brief.")

client = OllamaClient()          # needs a running ollama serve
response = client.chat(payload)  # POST {base_url}/api/chat
print(extract_reply(response))
```

TestClient-style offline check (what the tests do):

```python
from unittest.mock import patch
from ollama_chatbot import OllamaClient, build_messages, extract_reply

fake = {"message": {"role": "assistant", "content": "Hi human!"}}
with patch("httpx.post"):
    ...
```

Details:

- `get_base_url(var_name="OLLAMA_BASE_URL") -> str` — default `http://localhost:11434`, trailing `/` stripped.
- `get_model(var_name="CHAT_MODEL") -> str` — default `tinyllama`.
- `get_system_prompt(var_name="SYSTEM_PROMPT") -> str | None` — None when unset/empty.
- `add_turn(history, role, content) -> list` — appends a validated turn (`role` in user/assistant, non-empty content), returns a new list (input not mutated).
- `build_messages(history, system_prompt=None) -> list` — prepends system prompt, trims history to last `MAX_HISTORY_MESSAGES` (=20) turns, validates shape.
- `extract_reply(response) -> str` — pulls `response["message"]["content"]`, strips, raises `ValueError` on bad shape.
- `build_chat_url(base_url) -> str` — `{base_url}/api/chat`.
- `OllamaClient(base_url=None, model=None)` — resolves from args or env; `chat(messages)` posts `{"model", "messages", "stream": false}` with a 120s timeout; network errors, non-200 status and malformed JSON raise `RuntimeError`.

## Stages

**Minimal:** `chat.py` with `build_messages`/`add_turn`/`extract_reply`; `ollama_api.py` with `OllamaClient.chat` posting to `/api/chat` non-streaming.

**Improved:** Env helpers (`get_base_url`/`get_model`/`get_system_prompt`) with defaults, history trimming (last 20), validation of roles/content, URL builder, `RuntimeError` on connection errors/HTTP status/bad payloads.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy --strict` clean (strict for 11–20 per ARCHITECTURE.md §8), `pytest` green for every public function in `chat.py`+`ollama_api.py` (excl. `cli.py` per §5) with `httpx.post` monkeypatched — no network, no model download, no inference in CI (G-12), `argparse` REPL with `--model`/`--url` and Ctrl+C-safe exit, `.env.example` present per GRILL2-06 §4, pinned `httpx==0.27.2` per G-17.

## API

```python
from ollama_chatbot import (
    MAX_HISTORY_MESSAGES,
    OllamaClient,
    add_turn,
    build_chat_url,
    build_messages,
    extract_reply,
    get_base_url,
    get_model,
    get_system_prompt,
)

get_base_url(var_name: str = "OLLAMA_BASE_URL") -> str
get_model(var_name: str = "CHAT_MODEL") -> str
get_system_prompt(var_name: str = "SYSTEM_PROMPT") -> str | None
add_turn(history: list[dict[str, str]], role: str, content: str) -> list[dict[str, str]]
build_messages(history: list[dict[str, str]], system_prompt: str | None = None) -> list[dict[str, str]]
extract_reply(response: dict[str, object]) -> str
build_chat_url(base_url: str) -> str

class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None)
    def chat(self, messages: list[dict[str, str]]) -> dict[str, object]
```

## Testing

```bash
pytest -v          # all HTTP mocked, no Ollama needed
ruff check .
black --check .
mypy --strict src
```

Tests never run a real model: `httpx.post` is replaced by a fake returning canned `{"message": {"content": ...}}` responses — see G-12 in ARCHITECTURE.md.

## ZuroKing's note

> LLM apps look like magic — "ask, receive wisdom". Show the split: the *conversation* is just a list of dicts `{"role", "content"}` — you can print it, trim it, save it. `build_messages` prepends a system prompt and cuts history so long chats don't blow up the context. `OllamaClient` is one `httpx.post` away — same skill as project #18, different endpoint. Keep boundaries sharp: `chat.py` is pure logic testable without a server, `ollama_api.py` knows only URLs and JSON, `cli.py` only loops input→send→print. And treat the model like a slow external service: timeout, handle connection errors, never call it in unit tests — mock it. Local-first AI means your data stays on your machine; that's the whole point of Ollama.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
