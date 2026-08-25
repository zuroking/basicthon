# ARCHITECTURE — 20 Final Integration

> Required per ARCHITECTURE.md §6 criterion (≥2 decisions from {crypto primitive, auth scheme, secret storage, DB schema, retry/backoff}) — this project has 1 explicit DB-schema decision plus the cross-cutting integration decision (three doors to one store); included here because it is the capstone combining 04/11/16 patterns.

## 1. Decisions

### 1.1 DB schema — single `tasks` table in SQLite (adapted from #11)

**Chosen:** one table `tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`, accessed through `sqlite3` with parameterized queries. Row → dataclass mapping via `_row_to_task`. `completed` stored as INTEGER 0/1 and converted with `bool(int(...))` — SQLite has no native bool.

**Why SQLite:**

- **Zero-config persistence:** stdlib module, single file, no server — matches repo isolation rule; copy folder + file anywhere.
- **Same schema lesson as #11:** table creation is idempotent (`CREATE TABLE IF NOT EXISTS`), so CLI and API can both call `create_db()` defensively.
- **Shared-file access:** both CLI and API open short-lived connections per operation; for a single-user toy this avoids locking issues that would need WAL or a connection pool.

**Alternatives rejected:**

- **JSON file (as #04):** no concurrent-read safety while the API is serving; the point of this project is a *real* database layer under two frontends.
- **SQLAlchemy ORM:** hides SQL from beginners; raw parameterized queries teach more with fewer concepts.
- **Postgres:** requires a server — violates isolation.
- **Multiple tables / users column:** out of scope; single-table keeps focus on integration, not modeling.

### 1.2 Integration shape — three layers over one store (CLI from #04, API from #16)

**Chosen:** `storage.py` holds all SQL and validation; `api.py` wraps those functions in FastAPI routes with Pydantic models (`TaskCreate` title 1..100, `TaskOut` response); `cli.py` offers subcommands (`add/list/get/done/delete/serve`) writing directly to the same SQLite file, plus `serve` launching uvicorn pointing at `final_integration.api:app`.

**Why this split:**

- **One source of truth for rules:** title stripping/length checks live once in `storage.py`; both frontends inherit them. API-level Pydantic constraints are an outer defense line (422 before touching the DB).
- **Proves persistence across layers:** a row added by the CLI appears via `GET /tasks` without any sync code — the test `test_cli_and_api_share_db` demonstrates exactly this.
- **Beginner-visible boundaries:** no framework imports in storage; no SQL strings in api/cli.

**Alternatives rejected:**

- **API as the only writer (CLI calls HTTP):** couples CLI to a running server and adds httpx dependency for local work; direct SQLite access is simpler and works offline.
- **Business logic in routes:** duplicates validation and makes the CLI drift — the exact failure mode this project teaches against.
- **Background worker/queue between CLI and API:** massive scope increase, zero pedagogical gain here.

### 1.3 Config — env-only paths and addresses

**Chosen:** `DATABASE_PATH` (default `./tasks.db`), `HOST` (default `127.0.0.1`), `PORT` (default `8000`) read via small env helpers, documented in `.env.example`. No secrets exist in this project — nothing to leak; `.env.example` still present per GRILL2-06 so the habit is uniform across projects.

## 2. Module boundaries

- `storage.py` — stdlib only (`sqlite3`, `pathlib`, `os` for env): `Task`, `create_db`, `add_task`, `list_tasks`, `get_task`, `complete_task`, `delete_task`, `get_db_path`. Every public function G-13-covered.
- `api.py` — FastAPI app: health route + five task routes wrapping storage; Pydantic models inline (only two small schemas); `get_host`/`get_port` helpers for the server process.
- `cli.py` — argparse subcommands, printing, exit codes, `serve` → uvicorn; excluded from coverage per G-13.
- `__init__.py` re-exports public surface; `__main__.py` enables `python -m final_integration`.

## 3. Why not for production (§9)

Educational capstone:

1. **No migrations:** schema created ad hoc; changing columns later needs manual surgery.
2. **No auth on the API:** anyone who can reach the port mutates tasks; fine locally, wrong publicly.
3. **Per-call connections:** simple but inefficient; production pools connections and uses WAL for concurrency.
4. **Snapshot duplication:** code copied from 04/11/16 will drift; real systems share libraries, not copies (this repo's isolation rule intentionally accepts this trade-off).
5. **No tests against a real server:** TestClient covers routing, not deployment concerns (proxies, timeouts).

## 4. Error model

- `ValueError` in `storage.py`: non-string/empty/too-long title, invalid `task_id` (bool rejected). Routes convert these to 422 where user-facing.
- Missing rows return `False` (`complete_task`/`delete_task`) or `None` (`get_task`); API maps them to 404.
- `DELETE .../` returns 204 with an explicitly empty `Response` body — HTTP spec forbids a body for 204 (lesson carried over from #16).
- `RuntimeError` reserved for "cannot happen" defensive branches.

## 5. Verification

Isolation: copy folder, `pip install -e . && pip install -r requirements.txt`. Tests use `tmp_path` SQLite files and `TestClient` — no network, no external services. `ruff check`, `black --check`, `mypy --strict src` clean per §8 (projects 11–20 strict). `.env.example` present per GRILL2-06; `pyproject.toml:dependencies = []`; runtime deps only in `requirements.txt`.
