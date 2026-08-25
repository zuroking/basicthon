# 18 — Telegram Bot

Isolated beginner project from the `basicthon` series (Systems & Integration).

**What you learn (lock scope):** talking to a real external HTTP API (Telegram Bot API) with `httpx`, long polling, and clean separation between pure message-handling logic and network I/O. The project is built in three stages: minimal — pure `handle_text`/`handle_update` turning text into replies (`/start`, `/help`, `/echo <text>`, fallback), thin `TelegramClient` with `get_me`/`get_updates`/`send_message`; improved — env config (`BOT_TOKEN` required, `TELEGRAM_API_URL`/`POLL_TIMEOUT` optional with defaults), offset bookkeeping via `next_offset`, explicit handling of non-text messages, API errors as `RuntimeError`; production-like — typed, tested, `ruff/black/mypy --strict` clean, `pytest` green for every public function in `src/telegram_bot/bot.py` and `src/telegram_bot/api.py` (excl. `cli.py` per §5), all HTTP mocked in tests (no network), `argparse` CLI running the polling loop.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` contains `httpx==0.27.2` (pinned per G-17).

## Setup

Get a token from [@BotFather](https://t.me/BotFather): send `/newbot`, follow prompts, copy the token.

```bash
# Linux/macOS
export BOT_TOKEN="1234567890:AA-your-token-here"

# Windows PowerShell
$env:BOT_TOKEN="1234567890:AA-your-token-here"

# optional overrides (see .env.example)
# TELEGRAM_API_URL=http://localhost:8081   # e.g. local Bot API server
# POLL_TIMEOUT=30                          # long-poll seconds, 1..300
```

Never commit the real token — `.env.example` documents the contract only.

## Usage

```bash
python -m telegram-bot 2>/dev/null || python -m telegram_bot
# or after pip install -e .
telegram-bot

# process one batch of updates then exit (useful for testing)
telegram-bot --once
```

Talk to your bot in Telegram:

```text
you:   /start
bot:   Hi! I am basicthon bot #18.
       Commands:
       /help - show commands
       /echo <text> - repeat after you
       Or just send me any message.

you:   /echo hello world
bot:   hello world

you:   good bot
bot:   You said: good bot

you:   (sends a photo)
bot:   (silently ignored — no text field)
```

Or as a library:

```python
from telegram_bot import handle_update, handle_text, TelegramClient, next_offset

print(handle_text("/echo hi"))      # "hi"
print(handle_text("anything"))      # "You said: anything"
print(handle_text(""))              # None -> don't reply

update = {"update_id": 100, "message": {"chat": {"id": 42}, "text": "/start"}}
print(handle_update(update))        # (42, "Hi! I am basicthon bot #18.\n...")

updates = [{"update_id": 100}, {"update_id": 101}]
print(next_offset(updates))         # 102

client = TelegramClient(token="123:abc", api_url="https://api.telegram.org")
print(client.get_me())              # {"id": ..., "username": "..."} (needs real token)
client.send_message(42, "hello")    # sends a message to chat 42
```

Details:

- `handle_text(text: str) -> str | None` — `/start` greeting, `/help` list, `/echo X` repeats X (stripped; empty → usage hint), any other non-empty text → `"You said: ..."`, empty → None (don't reply).
- `handle_update(update: dict) -> tuple[int, str] | None` — extracts message/chat.id/text, returns `(chat_id, reply)` or None when nothing to reply.
- `extract_message/extract_chat_id/extract_text` — defensive extraction from raw Bot API dicts; photo/sticker messages (no `text`) are ignored.
- `get_bot_token(var_name="BOT_TOKEN") -> str` — reads `os.environ`, strips, raises `ValueError("BOT_TOKEN is not set, see .env.example")` when missing.
- `get_api_url()` → default `https://api.telegram.org` (override for tests/local Bot API server); trailing `/` stripped.
- `get_poll_timeout()` → default `30`, valid range 1..300.
- `build_method_url(api_url, token, method) -> str` → `{api_url}/bot{token}/{method}`.
- `TelegramClient(token=None, api_url=None)` — resolves args or env; methods:
  - `get_me() -> dict` — bot identity sanity check;
  - `get_updates(offset: int, timeout: int) -> list[dict]` — long polling batch;
  - `send_message(chat_id: int, text: str) -> dict` — sends a reply;
  - network errors and `ok: false` responses raise `RuntimeError`.
- `next_offset(updates) -> int | None` — max `update_id + 1`, so already-seen messages are not fetched again.

## Stages

**Minimal:** `bot.py` with `extract_*` helpers, `handle_text` for `/start`/`/help`/`/echo`/fallback, `handle_update` returning `(chat_id, reply)`; `api.py` with `TelegramClient.get_me/get_updates/send_message`.

**Improved:** Env helpers `get_bot_token` (required)/`get_api_url` (default)/`get_poll_timeout` (30, 1..300), URL builder with validation, `RuntimeError` on `ok: false` and network errors, `next_offset` for polling bookkeeping, type validation rejecting `bool` where `int` expected, non-text messages ignored.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy --strict` clean (strict for 11–20 per ARCHITECTURE.md §8), `pytest` green for every public function in `bot.py`+`api.py` (excl. `cli.py` per §5) with `httpx.post` monkeypatched — no network, no real token in tests (G-12), `argparse` CLI with `--once`, Ctrl+C-safe loop, `.env.example` present per GRILL2-06 §4, pinned `httpx==0.27.2` per G-17.

## API

```python
from telegram_bot import (
    handle_text, handle_update,
    extract_message, extract_chat_id, extract_text,
    TelegramClient, get_bot_token, get_api_url, get_poll_timeout,
    build_method_url, next_offset,
)

handle_text(text: str) -> str | None
handle_update(update: dict[str, object]) -> tuple[int, str] | None
extract_message(update: dict[str, object]) -> dict[str, object] | None
extract_chat_id(message: dict[str, object]) -> int | None
extract_text(message: dict[str, object]) -> str | None
get_bot_token(var_name: str = "BOT_TOKEN") -> str
get_api_url(var_name: str = "TELEGRAM_API_URL") -> str
get_poll_timeout(var_name: str = "POLL_TIMEOUT") -> int
build_method_url(api_url: str, token: str, method: str) -> str
next_offset(updates: list[dict[str, object]]) -> int | None

class TelegramClient:
    def __init__(self, token: str | None = None, api_url: str | None = None)
    def get_me(self) -> dict[str, object]
    def get_updates(self, offset: int, timeout: int) -> list[dict[str, object]]
    def send_message(self, chat_id: int, text: str) -> dict[str, object]
```

## Testing

```bash
pytest -v          # all HTTP mocked, no token needed
ruff check .
black --check .
mypy --strict src
```

Tests never touch the network: `httpx.post` is replaced by a fake that records calls and returns canned `{"ok": true/false}` responses — see G-12 in ARCHITECTURE.md.

## ZuroKing's note

> Bots look like magic — "someone typed, bot answered". Show the split: `bot.py` is a *pure function* from text to reply — you can test it without any network at all. `api.py` is a dumb pipe: build URL, POST JSON, check `ok`. The polling loop is just `offset = max(update_id)+1` repeated. Keep boundaries sharp: `bot.py` never imports `httpx`, `api.py` never parses commands, `cli.py` only wires them together. And treat `BOT_TOKEN` honestly: it is a password — read it from env, document in `.env.example`, never print it, never commit it. If you want to see what the bot does offline, run pytest — every scenario is replayed against fake responses.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
