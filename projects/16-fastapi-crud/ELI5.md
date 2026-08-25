# ELI5 — FastAPI CRUD

Imagine a toy shop with a notebook:

- The notebook is a `dict[int, Item]` called `_items`. Page 1 holds `Item(id=1, title="Buy milk")`, page 2 holds `Item(id=2, title="Walk dog")`. A counter `_next_id` says which page number to use next.
- `create_item(ItemCreate(title="Buy milk"))` writes a new page: strip spaces, check `title` 1..100 chars, `description` ≤500 chars, assign `id=_next_id`, store, then `_next_id += 1`. Returns the new `Item`.
- `get_item(1)` looks up page 1, `list_items()` returns all pages sorted by `id`, `update_item(1, ItemUpdate(title="Buy bread"))` rewrites page 1 title only (other fields stay), `delete_item(1)` tears page out. `reset_store()` throws whole notebook away — used by tests.
- FastAPI is the shop counter: `POST /items` with JSON `{"title":"hello"}` → counter calls `create_item`, returns `201` + JSON. `GET /items` → `list_items`. `GET /items/1` → `get_item` or `404 {"detail":"item not found"}`. Same for `PUT` and `DELETE` (204 on success — 204 means "done, nothing to return", so the response has no body by HTTP rule).
- Validation lives in Pydantic: `ItemCreate(title=Field(min_length=1, max_length=100))` rejects `""` or 101×"x" with `422`. `ItemUpdate` all optional — only non-None fields applied.
- Settings live outside code: `get_database_url()` reads `$DATABASE_URL` (`memory` if missing), `get_port()` reads `$PORT` (`8000` if missing, 1..65535). They are documented in `.env.example` so you never hardcode secrets.
- Tests never start a real server: `from fastapi.testclient import TestClient; client = TestClient(app); client.post("/items", json={"title":"a"})`. An `autouse` fixture calls `reset_store` before each test, so `id` always starts at 1 — deterministic.

Rules a child can follow:

- `title` must be non-empty after `strip`, 1..100 chars; `description` None or ≤500 chars (empty stripped → `None`).
- `item_id` must be `int` not `bool` (1,2,3…), else `ValueError`; API path `/items/not-an-int` → `422`.
- Missing item → `None` from core, `404` from API.
- `DATABASE_URL` and `PORT`/`HOST` live in environment, not code; `get_*` trims and defaults, invalid port (`0`, `70000`, `abc`) → `ValueError`.
- This is a toy notebook. Real shops use a database file (SQLite, Postgres) and keep data after restart; this keeps everything in memory and forgets on `reset_store` or server restart — perfect for learning FastAPI without DB complexity.
