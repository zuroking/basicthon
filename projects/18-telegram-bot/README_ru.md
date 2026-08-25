# 18 — Telegram Bot

Изолированный учебный проект из серии `basicthon` (Systems & Integration).

**Что изучаем (lock scope):** работу с реальным внешним HTTP API (Telegram Bot API) через `httpx`, long polling и чистое разделение логики обработки сообщений и сетевого I/O. Проект в три этапа: minimal — чистые `handle_text`/`handle_update` превращают текст в ответ (`/start`, `/help`, `/echo <text>`, fallback), тонкий `TelegramClient` с `get_me`/`get_updates`/`send_message`; improved — env-конфиг (`BOT_TOKEN` обязателен, `TELEGRAM_API_URL`/`POLL_TIMEOUT` опциональны с дефолтами), bookkeeping offset через `next_offset`, явная обработка нетекстовых сообщений, ошибки API как `RuntimeError`; production-like — типизация, тесты, `ruff/black/mypy --strict`, `pytest` зелёный для каждой публичной функции в `src/telegram_bot/bot.py` и `src/telegram_bot/api.py` (кроме `cli.py` по §5), весь HTTP замокан (без сети), `argparse` CLI с циклом polling.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` содержит `httpx==0.27.2` (пиннинг по G-17).

## Настройка

Получите токен у [@BotFather](https://t.me/BotFather): отправьте `/newbot`, следуйте подсказкам, скопируйте токен.

```bash
# Linux/macOS
export BOT_TOKEN="1234567890:AA-your-token-here"

# Windows PowerShell
$env:BOT_TOKEN="1234567890:AA-your-token-here"

# опциональные переопределения (см. .env.example)
# TELEGRAM_API_URL=http://localhost:8081   # например локальный Bot API сервер
# POLL_TIMEOUT=30                          # секунды long-poll, 1..300
```

Никогда не коммитьте реальный токен — `.env.example` документирует только контракт.

## Использование

```bash
python -m telegram_bot
# или после pip install -e .
telegram-bot

# обработать одну пачку апдейтов и выйти (удобно для теста)
telegram-bot --once
```

Поговорите с ботом в Telegram:

```text
вы:    /start
бот:   Hi! I am basicthon bot #18.
       Commands:
       /help - show commands
       /echo <text> - repeat after you
       Or just send me any message.

вы:    /echo привет мир
бот:   привет мир

вы:    хороший бот
бот:   You said: хороший бот

вы:    (отправляет фото)
бот:   (молча игнорирует — нет поля text)
```

Как библиотека:

```python
from telegram_bot import handle_update, handle_text, TelegramClient, next_offset

print(handle_text("/echo hi"))      # "hi"
print(handle_text("что угодно"))    # "You said: что угодно"
print(handle_text(""))              # None -> не отвечать

update = {"update_id": 100, "message": {"chat": {"id": 42}, "text": "/start"}}
print(handle_update(update))        # (42, "Hi! I am basicthon bot #18.\n...")

updates = [{"update_id": 100}, {"update_id": 101}]
print(next_offset(updates))         # 102

client = TelegramClient(token="123:abc", api_url="https://api.telegram.org")
print(client.get_me())              # {"id": ..., "username": "..."} (нужен реальный токен)
client.send_message(42, "hello")    # отправляет сообщение в чат 42
```

Детали:

- `handle_text(text: str) -> str | None` — `/start` приветствие, `/help` список, `/echo X` повторяет X (stripped; пусто → подсказка), любой другой непустой текст → `"You said: ..."`, пусто → None.
- `handle_update(update: dict) -> tuple[int, str] | None` — извлекает message/chat.id/text, возвращает `(chat_id, reply)` или None.
- `extract_message/extract_chat_id/extract_text` — защитное извлечение из сырых dict; сообщения без текста (фото/стикеры) игнорируются.
- `get_bot_token(var_name="BOT_TOKEN") -> str` — читает `os.environ`, strips, бросает `ValueError("BOT_TOKEN is not set, see .env.example")` если отсутствует.
- `get_api_url()` → дефолт `https://api.telegram.org`; хвостовой `/` срезается.
- `get_poll_timeout()` → дефолт `30`, диапазон 1..300.
- `build_method_url(api_url, token, method) -> str` → `{api_url}/bot{token}/{method}`.
- `TelegramClient(token=None, api_url=None)`:
  - `get_me() -> dict` — проверка идентичности бота;
  - `get_updates(offset: int, timeout: int) -> list[dict]` — long polling;
  - `send_message(chat_id: int, text: str) -> dict` — отправка ответа;
  - сетевые ошибки и `ok: false` → `RuntimeError`.
- `next_offset(updates) -> int | None` — max `update_id + 1`.

## Этапы

**Minimal:** `bot.py` с хелперами `extract_*`, `handle_text` для `/start`/`/help`/`/echo`/fallback, `handle_update` → `(chat_id, reply)`; `api.py` с `TelegramClient.get_me/get_updates/send_message`.

**Improved:** Env-хелперы `get_bot_token` (обязателен)/`get_api_url` (дефолт)/`get_poll_timeout` (30, 1..300), URL builder с валидацией, `RuntimeError` на `ok: false` и сетевые ошибки, `next_offset` для bookkeeping, отклонение `bool` там где ожидается `int`, нетекстовые сообщения игнорируются.

**Production-like:** Type hints на всех публичных функциях, `ruff/black/mypy --strict` без ошибок (strict для 11–20 по §8), `pytest` зелёный для каждой публичной функции в `bot.py`+`api.py` (кроме `cli.py` по §5), `httpx.post` замокан — без сети и без реального токена в тестах (G-12), `argparse` CLI с `--once`, Ctrl+C-safe loop, `.env.example` по GRILL2-06 §4, пиннинг `httpx==0.27.2` по G-17.

## API

```python
from telegram_bot import (
    handle_text, handle_update,
    extract_message, extract_chat_id, extract_text,
    TelegramClient, get_bot_token, get_api_url, get_poll_timeout,
    build_method_url, next_offset,
)
```

## Тестирование

```bash
pytest -v          # весь HTTP замокан, токен не нужен
ruff check .
black --check .
mypy --strict src
```

Тесты никогда не ходят в сеть: `httpx.post` заменён фейком, который пишет вызовы и возвращает заготовленные `{"ok": true/false}` — см. G-12.

## Заметка от ZuroKing

> Бот выглядит как магия — «кто-то написал, бот ответил». Покажите раскол: `bot.py` — *чистая функция* от текста к ответу, тестируется вообще без сети. `api.py` — тупая труба: собрать URL, POST JSON, проверить `ok`. Цикл polling — это просто `offset = max(update_id)+1`. Держите границы: `bot.py` не импортирует `httpx`, `api.py` не парсит команды, `cli.py` только связывает их. И относитесь к `BOT_TOKEN` честно: это пароль — читайте из env, документируйте в `.env.example`, не печатайте, не коммитьте. Хотите увидеть, что делает бот оффлайн — запустите pytest: каждый сценарий проигрывается против фейковых ответов.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.
