# 16 — REST API on FastAPI (CRUD)

Isolated beginner project from the `basicthon` series (Systems & Integration).

**What you learn (lock scope):** building a typed CRUD REST API with FastAPI, Pydantic validation, in-memory storage, and `TestClient` testing. The project is built in three stages: minimal — `Item`/`ItemCreate`/`ItemUpdate` with Pydantic `BaseModel` + `Field`, in-memory `dict[int, Item]` with `_next_id`, five routes (`POST /items`, `GET /items`, `GET /items/{id}`, `PUT /items/{id}`, `DELETE /items/{id}`) and `reset_store` for tests; improved — strict validation (title 1..100, description max 500, strip, empty→None), typed core functions `create_item`/`get_item`/`list_items`/`update_item`/`delete_item`, environment helpers `get_database_url`/`get_port`/`get_host` via `os.environ` with `.env.example`, `HTTPException(404)` for missing items, `TestClient` without network; production-like — typed, tested, `ruff/black/mypy --strict` clean, `pytest` green for every public function in `src/fastapi_crud/app.py` (excl. `cli.py` per §5), `argparse` CLI launching `uvicorn`.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` contains `fastapi==0.110.2`, `uvicorn==0.29.0`, `httpx==0.27.2` (pinned, see Stages for why).

## Usage

Run the server:

```bash
python -m fastapi_crud --port 8000
# or after install
fastapi-crud --host 127.0.0.1 --port 8000
# with env (see .env.example)
HOST=127.0.0.1 PORT=8000 python -m fastapi_crud
```

With `DATABASE_URL` (in-memory by default, `.env.example` shows `sqlite:///./app.db` for future persistence):

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

Use the API (server running on `http://127.0.0.1:8000`):

```bash
# health
curl http://127.0.0.1:8000/
# {"status":"ok"}

curl http://127.0.0.1:8000/health

# create
curl -X POST http://127.0.0.1:8000/items -H "Content-Type: application/json" -d '{"title":"Buy milk","description":"2L"}'
# {"id":1,"title":"Buy milk","description":"2L"}

# list
curl http://127.0.0.1:8000/items
# [{"id":1,"title":"Buy milk","description":"2L"}]

# get
curl http://127.0.0.1:8000/items/1

# update
curl -X PUT http://127.0.0.1:8000/items/1 -H "Content-Type: application/json" -d '{"title":"Buy bread"}'

# delete
curl -X DELETE http://127.0.0.1:8000/items/1 -v
# 204 No Content
```

Or as a library:

```python
from fastapi_crud import create_item, get_item, list_items, update_item, delete_item, reset_store
from fastapi_crud.models import ItemCreate, ItemUpdate
from fastapi_crud.app import get_database_url, get_port

reset_store()
item = create_item(ItemCreate(title="hello", description="world"))
print(item)
# Item(id=1, title='hello', description='world')

print(get_item(1))
# Item(id=1, title='hello', description='world')

print(list_items())
# [Item(id=1, ...)]

print(update_item(1, ItemUpdate(title="hi")))
# Item(id=1, title='hi', description='world')

print(delete_item(1))
# True

# env helpers
print(get_database_url())  # "memory" if $DATABASE_URL not set
print(get_port())          # 8000 if $PORT not set
```

TestClient example (no server needed):

```python
from fastapi.testclient import TestClient
from fastapi_crud.app import app

client = TestClient(app)
client.post("/items", json={"title": "a"})
print(client.get("/items").json())
# [{"id": 1, "title": "a", "description": null}]
```

Details:

- `get_database_url(var_name="DATABASE_URL") -> str` reads `os.environ`, strips, returns `"memory"` if missing/empty; validates `var_name`.
- `get_port(var_name="PORT") -> int` reads `os.environ`, returns `8000` if missing/empty, parses int, validates 1..65535.
- `get_host(var_name="HOST") -> str` reads `os.environ`, returns `"127.0.0.1"` if missing/empty.
- `create_item(data: ItemCreate) -> Item` validates `ItemCreate`, strips `title`, empty `description` → `None`, assigns auto-increment `id`, stores in `_items`.
- `get_item(item_id: int) -> Item | None` returns item or `None`, validates `item_id` is `int` not `bool`.
- `list_items() -> list[Item]` returns sorted by `id`.
- `update_item(item_id: int, data: ItemUpdate) -> Item | None` partial update, only non-None fields applied, strips, empty description → `None`, returns `None` if not found.
- `delete_item(item_id: int) -> bool` deletes and returns `True` if existed else `False`.
- `reset_store() -> None` clears dict and resets `_next_id` to 1.
- FastAPI routes: `GET /` and `GET /health` → `{"status":"ok"}`, `POST /items` (201), `GET /items`, `GET /items/{id}` (404 if missing), `PUT /items/{id}` (404), `DELETE /items/{id}` (204 or 404).
- `DELETE` returns `204 No Content` with an **empty body** — by HTTP spec 204 must not include a body, so we return `Response(status_code=204)` explicitly. Returning JSON with 204 would raise `AssertionError: Status code 204 must not have a response body` — a common beginner mistake; use `200` if you need to return data.
- Models: `ItemCreate(title: str [1..100], description: str|None [max 500])`, `ItemUpdate(title?: str, description?: str)`, `Item(id: int, title: str, description: str|None)`.

## Stages

**Minimal:** `models.py` with `ItemCreate`/`Item`/`ItemUpdate` via `pydantic.BaseModel` + `Field(min_length=1, max_length=100)`, `app.py` with `_items: dict[int, Item] = {}` and `_next_id: int = 1`, functions `create_item`/`get_item`/`list_items`/`update_item`/`delete_item`/`reset_store`, `FastAPI()` with 5 CRUD routes + `GET /` health, `response_model=Item` and `status_code=201/204`.

**Improved:** Strict validation (strip `title`, reject empty after strip, `description` empty→`None`, max lengths via `Field`), type hints on all public functions (`Item | None`, `list[Item]`, `bool`), `HTTPException(404, "item not found")` in handlers, environment helpers `get_database_url`/`get_port`/`get_host` reading `os.environ` with trimming and defaults (`memory`/`8000`/`127.0.0.1`), port range 1..65535, tests via `TestClient` with `autouse` fixture calling `reset_store`, no network, no real DB.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy --strict` clean (strict for 11–20 per ARCHITECTURE.md §8), `pytest` green for every public function in `src/fastapi_crud/app.py` (excl. `cli.py` per §5) with `TestClient` + direct calls + `monkeypatch` for env, `argparse` CLI in `cli.py` with `--host`/`--port`/`--reload` resolving env `$HOST`/`$PORT` and launching `uvicorn.run("fastapi_crud.app:app", ...)`, `python -m fastapi_crud` entry point, `.env.example` present per GRILL2-06 §4, pinned `fastapi==0.110.2`, `uvicorn==0.29.0`, `httpx==0.27.2` per G-17.

## API

```python
from fastapi_crud import Item, ItemCreate, ItemUpdate
from fastapi_crud.app import create_item, get_item, list_items, update_item, delete_item, reset_store, get_database_url, get_port, get_host, app

get_database_url(var_name: str = "DATABASE_URL") -> str
get_port(var_name: str = "PORT") -> int
get_host(var_name: str = "HOST") -> str
reset_store() -> None
create_item(data: ItemCreate) -> Item
get_item(item_id: int) -> Item | None
list_items() -> list[Item]
update_item(item_id: int, data: ItemUpdate) -> Item | None
delete_item(item_id: int) -> bool

# FastAPI app
app: FastAPI
# POST /items, GET /items, GET /items/{id}, PUT /items/{id}, DELETE /items/{id}
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## ZuroKing's note

> Beginners think an API is magic — "POST and data appears". Show the split: storage is just a `dict[int, Item]` and an `int` counter. `create_item` does `strip`, assigns `_next_id`, stores, increments; `update_item` applies only non-None fields; `delete_item` is `del`. Then FastAPI is a thin wrapper: route validates via Pydantic, calls the function, raises 404 if `None`. Keep boundaries sharp: `models.py` knows only `pydantic`, `app.py` knows only `dict`+`os.environ`+`fastapi`, `cli.py` knows only `argparse`+`uvicorn`. Use `reset_store` + `TestClient` so tests are isolated — no server, no network, no DB file. And treat `os.environ` honestly: `get_port`/`get_database_url` read, strip, validate, default — document in `.env.example` so a beginner never hardcodes a secret.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
