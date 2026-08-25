# 16 — REST API на FastAPI (CRUD)

Изолированный учебный проект из серии `basicthon` (Systems & Integration).

**Что изучаем (lock scope):** построение типизированного CRUD REST API на FastAPI, валидацию Pydantic, in-memory хранилище и тестирование через `TestClient`. Проект в три этапа: minimal — `Item`/`ItemCreate`/`ItemUpdate` на `pydantic.BaseModel` + `Field`, in-memory `dict[int, Item]` со счётчиком `_next_id`, пять роутов (`POST /items`, `GET /items`, `GET /items/{id}`, `PUT /items/{id}`, `DELETE /items/{id}`) и `reset_store` для тестов; improved — строгая валидация (title 1..100, description до 500, trim, пусто→None), типизированные функции `create_item`/`get_item`/`list_items`/`update_item`/`delete_item`, хелперы окружения `get_database_url`/`get_port`/`get_host` через `os.environ` с `.env.example`, `HTTPException(404)` для отсутствующих записей, `TestClient` без сети; production-like — типизация, тесты, `ruff/black/mypy --strict`, `pytest` зелёный для каждой публичной функции в `src/fastapi_crud/app.py` (кроме `cli.py` по §5), CLI на `argparse` с запуском `uvicorn`.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` содержит `fastapi==0.110.2`, `uvicorn==0.29.0`, `httpx==0.27.2` (пиннинг, см. Stages).

## Использование

Запуск сервера:

```bash
python -m fastapi_crud --port 8000
# или после установки
fastapi-crud --host 127.0.0.1 --port 8000
# с env (см. .env.example)
HOST=127.0.0.1 PORT=8000 python -m fastapi_crud
```

С `DATABASE_URL` (по умолчанию in-memory, `.env.example` показывает `sqlite:///./app.db` для будущего персиста):

```bash
# Linux/macOS
export DATABASE_URL="sqlite:///./app.db"
export PORT=8000
fastapi-crud

# Windows PowerShell
$env:DATABASE_URL="sqlite:///./app.db"
$env:PORT="8000"
python -m fastapi_crud
```

API (сервер на `http://127.0.0.1:8000`):

```bash
curl http://127.0.0.1:8000/
# {"status":"ok"}

curl -X POST http://127.0.0.1:8000/items -H "Content-Type: application/json" -d '{"title":"Купить молоко","description":"2л"}'
curl http://127.0.0.1:8000/items
curl http://127.0.0.1:8000/items/1
curl -X PUT http://127.0.0.1:8000/items/1 -H "Content-Type: application/json" -d '{"title":"Купить хлеб"}'
curl -X DELETE http://127.0.0.1:8000/items/1 -v
```

Как библиотека:

```python
from fastapi_crud import create_item, get_item, list_items, update_item, delete_item, reset_store
from fastapi_crud.models import ItemCreate, ItemUpdate

reset_store()
item = create_item(ItemCreate(title="hello", description="world"))
print(get_item(1))
print(list_items())
print(update_item(1, ItemUpdate(title="hi")))
print(delete_item(1))
```

TestClient без сервера:

```python
from fastapi.testclient import TestClient
from fastapi_crud.app import app

client = TestClient(app)
client.post("/items", json={"title": "a"})
print(client.get("/items").json())
```

Детали:

- `get_database_url(var_name="DATABASE_URL") -> str` читает `os.environ`, trim, возвращает `"memory"` если пусто; валидирует `var_name`.
- `get_port(var_name="PORT") -> int` читает `os.environ`, возвращает `8000` если пусто, парсит int, проверяет 1..65535.
- `get_host(var_name="HOST") -> str` читает `os.environ`, возвращает `"127.0.0.1"` если пусто.
- `create_item(data: ItemCreate) -> Item` валидирует, trims `title`, пустой `description`→`None`, назначает auto-increment `id`.
- `get_item(item_id: int) -> Item | None` возвращает или `None`, валидирует `int` (отклоняет `bool`).
- `list_items() -> list[Item]` отсортировано по `id`.
- `update_item(item_id: int, data: ItemUpdate) -> Item | None` частично, только не-None поля, trims, пустой description→`None`, `None` если не найден.
- `delete_item(item_id: int) -> bool` удаляет, `True` если был.
- `reset_store() -> None` очищает и сбрасывает `_next_id` в 1.
- Роуты: `GET /` и `GET /health` → `{"status":"ok"}`, `POST /items` (201), `GET /items`, `GET /items/{id}` (404), `PUT /items/{id}` (404), `DELETE /items/{id}` (204/404).
- `DELETE` возвращает `204 No Content` с **пустым телом** — по HTTP-спецификации 204 не должен содержать body, поэтому мы возвращаем `Response(status_code=204)` явно. Попытка вернуть JSON с 204 вызовет `AssertionError: Status code 204 must not have a response body` — частая ошибка новичков; если нужно вернуть данные, используйте `200`.
- Модели: `ItemCreate(title: 1..100, description: max 500)`, `ItemUpdate`, `Item(id, title, description)`.

## Этапы

**Minimal:** `models.py` с `ItemCreate`/`Item`/`ItemUpdate` на `BaseModel` + `Field`, `app.py` с `_items: dict[int, Item]` и `_next_id`, функции `create_item`/`get_item`/`list_items`/`update_item`/`delete_item`/`reset_store`, `FastAPI()` с 5 CRUD роутами + `GET /` health, `response_model=Item`, коды 201/204.

**Improved:** Строгая валидация (strip, пусто→ошибка/None, `Field` max_length), type hints на всех публичных функциях, `HTTPException(404)` в хэндлерах, хелперы `get_database_url`/`get_port`/`get_host` через `os.environ` с defaults, диапазон порта 1..65535, тесты через `TestClient` с `autouse` `reset_store`, без сети и без реальной БД.

**Production-like:** Type hints, `ruff/black/mypy --strict` без ошибок (strict для 11–20 по §8), `pytest` зелёный для каждой публичной функции в `app.py` (кроме `cli.py`), `argparse` CLI в `cli.py` с `--host`/`--port`/`--reload` и env `$HOST`/`$PORT` + `uvicorn.run("fastapi_crud.app:app", ...)`, `python -m fastapi_crud`, `.env.example` по GRILL2-06, пиннинг `fastapi==0.110.2` и т.д. по G-17.

## API

```python
from fastapi_crud import Item, ItemCreate, ItemUpdate
from fastapi_crud.app import create_item, get_item, list_items, update_item, delete_item, reset_store, get_database_url, get_port, get_host, app
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## Заметка от ZuroKing

> Новички думают, что API — магия: "отправил POST и данные появились". Покажите раскол: хранение — это просто `dict[int, Item]` и счётчик. `create_item` делает `strip`, кладёт под `_next_id`, инкрементит; `update_item` трогает только не-None поля; `delete_item` — `del`. FastAPI — тонкая обёртка: роут валидирует через Pydantic, вызывает функцию, бросает 404 если `None`. Держите границы жёстко: `models.py` знает только `pydantic`, `app.py` — `dict`+`os.environ`+`fastapi`, `cli.py` — `argparse`+`uvicorn`. Тесты — через `reset_store` + `TestClient`, без сервера и сети, детерминированы. А `os.environ` читайте честно: `get_port`/`get_database_url` с trim, валидацией и defaults — и задокументируйте в `.env.example`, чтобы новичок никогда не хардкодил секреты.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.
