# 19 — Чат-бот поверх локальной LLM (Ollama)

Изолированный учебный проект из серии `basicthon` (Systems & Integration).

**Что изучаем (lock scope):** работу с локально запущенным LLM-сервером (Ollama `POST /api/chat`) через `httpx`, управление историей диалога как списком сообщений role/content и тестируемость цикла чата без инференса. Проект в три этапа: minimal — чистые `build_messages`/`add_turn`/`extract_reply` над `list[{"role","content"}]`, тонкий `OllamaClient.chat()`; improved — env-конфиг (`OLLAMA_BASE_URL`, `CHAT_MODEL`, опциональный `SYSTEM_PROMPT`), обрезка истории до последних 20 ходов, защитное извлечение и `RuntimeError` на сетевые/HTTP ошибки; production-like — типизация, тесты, `ruff/black/mypy --strict`, `pytest` зелёный для каждой публичной функции в `src/ollama_chatbot/chat.py` и `src/ollama_chatbot/ollama_api.py` (кроме `cli.py` по §5), весь HTTP замокан (без реального инференса — G-12), `argparse` REPL CLI.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` содержит `httpx==0.27.2` (пиннинг по G-17).

## Настройка

Нужен локальный сервер [Ollama](https://ollama.com) и небольшая модель:

```bash
ollama serve                 # поднимает http://localhost:11434
ollama pull tinyllama        # ~640 МБ; подойдёт любая chat-модель
```

Переменные окружения (см. `.env.example`; все опциональны):

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

## Использование

```bash
python -m ollama_chatbot
# или после pip install -e .
ollama-chatbot --model tinyllama --url http://localhost:11434
```

Пример сессии:

```text
Chatting with 'tinyllama' at http://localhost:11434
Type your message; /exit or Ctrl+C to quit.
you> привет, кто ты?
bot> I am a language model running locally via Ollama.
you> /exit
Bye!
```

Как библиотека:

```python
from ollama_chatbot import (
    add_turn, build_messages, extract_reply, OllamaClient,
    get_base_url, get_model,
)

print(get_base_url())  # "http://localhost:11434" если env не задан
print(get_model())     # "tinyllama" если env не задан

history = add_turn([], "user", "привет")
payload = build_messages(history, system_prompt="Отвечай кратко.")

client = OllamaClient()          # нужен запущенный ollama serve
response = client.chat(payload)  # POST {base_url}/api/chat
print(extract_reply(response))
```

Детали:

- `get_base_url(var_name="OLLAMA_BASE_URL") -> str` — дефолт `http://localhost:11434`.
- `get_model(var_name="CHAT_MODEL") -> str` — дефолт `tinyllama`.
- `get_system_prompt(var_name="SYSTEM_PROMPT") -> str | None` — None если пусто.
- `add_turn(history, role, content) -> list` — добавляет проверенный ход (`role` user/assistant, непустой content), возвращает новый список.
- `build_messages(history, system_prompt=None) -> list` — добавляет system-промпт, режет историю до последних 20 ходов.
- `extract_reply(response) -> str` — достаёт `response["message"]["content"]`.
- `build_chat_url(base_url) -> str` — `{base_url}/api/chat`.
- `OllamaClient(base_url=None, model=None)`; `chat(messages)` шлёт `{"model", "messages", "stream": false}` с таймаутом 120с; сетевые ошибки, не-200 статус и кривой JSON → `RuntimeError`.

## Этапы

**Minimal:** `chat.py` с `build_messages`/`add_turn`/`extract_reply`; `ollama_api.py` с `OllamaClient.chat` на `/api/chat` без стриминга.

**Improved:** Env-хелперы с дефолтами, обрезка истории (последние 20), валидация ролей/content, URL builder, `RuntimeError` на ошибки соединения/статус/кривые payload.

**Production-like:** Type hints на всех публичных функциях, `ruff/black/mypy --strict` без ошибок (strict для 11–20 по §8), `pytest` зелёный для каждой публичной функции в `chat.py`+`ollama_api.py` (кроме `cli.py` по §5), `httpx.post` замокан — без сети, без скачивания модели, без инференса в CI (G-12), `argparse` REPL с `--model`/`--url` и Ctrl+C-safe выходом, `.env.example` по GRILL2-06 §4, пиннинг `httpx==0.27.2` по G-17.

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
```

## Тестирование

```bash
pytest -v          # весь HTTP замокан, Ollama не нужен
ruff check .
black --check .
mypy --strict src
```

Тесты никогда не запускают реальную модель: `httpx.post` заменён фейком, возвращающим заготовленные `{"message": {"content": ...}}` — см. G-12.

## Заметка от ZuroKing

> LLM-приложения выглядят как магия — «спросил, получил мудрость». Покажите раскол: *диалог* — это просто список словарей `{"role", "content"}`, его можно напечатать, обрезать, сохранить. `build_messages` добавляет system-промпт и режет историю, чтобы длинные чаты не раздували контекст. `OllamaClient` — один `httpx.post`, тот же навык, что в проекте №18, другой эндпоинт. Держите границы: `chat.py` — чистая логика, тестируется без сервера; `ollama_api.py` знает только URL и JSON; `cli.py` только крутит цикл ввод→отправка→печать. И относитесь к модели как к медленному внешнему сервису: таймаут, обработка ошибок соединения, никогда не дёргать её в юнит-тестах — только мокать. Local-first AI значит, что ваши данные остаются у вас — в этом весь смысл Ollama.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.
