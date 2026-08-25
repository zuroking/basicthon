# 20 — Final Integration (CLI + SQLite + API)

Isolated beginner project from the `basicthon` series (Systems & Integration).

> **This project reuses patterns from projects 04, 11 and 16 — the code is copied and adapted, not imported, to preserve project isolation.**
> **Snapshot at creation time — later changes in 04/11/16 are not ported automatically.**

**What you learn (lock scope):** combining three layers into one app — a CLI (`argparse`), SQLite persistence (stdlib `sqlite3`), and a REST API (FastAPI) over the same database. The project is built in three stages: minimal — `storage.py` with `Task` dataclass and CRUD on a `tasks` table; improved — FastAPI routes wrapping storage functions, env config via `DATABASE_PATH`/`HOST`/`PORT`; production-like — typed, tested, `ruff/black/mypy --strict` clean, `pytest` green for every public function in `src/final_integration/storage.py` and `src/final_integration/api.py` (excl. `cli.py` per §5), TestClient tests sharing one temp DB with the CLI layer.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` contains `fastapi==0.110.2`, `uvicorn==0.29.0`, `httpx==0.27.2` (pinned per G-17).

## Usage

CLI (writes directly to SQLite):

```bash
python -m final_integration list
# (no tasks)

echo "write final report" | python -m final_integration add
# added #1

python -m final_integration add        # interactive prompt if tty
python -m final_integration list --all
# [ ] #1 write final report  (2026-08-25 09:00:00)

python -m final_integration done 1
python -m final_integration get 1
python -m final_integration delete 1
```

REST API (same database file):

```bash
python -m final_integration serve            # $DATABASE_PATH, default ./tasks.db
# or
final-integration serve --host 127.0.0.1 --port 8000

curl http://127.0.0.1:8000/tasks
curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"title":"deploy"}'
curl -X PUT http://127.0.0.1:8000/tasks/1/complete
curl -X DELETE http://127.0.0.1:8000/tasks/1   # 204, no body
```

Or as a library:

```python
from pathlib import Path
from final_integration import (
    add_task, get_task, list_tasks, complete_task, delete_task, create_db,
)

db = Path("tasks.db")
create_db(db)
tid = add_task(db, "ship it")
print(get_task(db, tid))       # Task(id=1, title='ship it', completed=False, ...)
complete_task(db, tid)
print(list_tasks(db))
delete_task(db, tid)
```

Details:

- `get_db_path(var_name="DATABASE_PATH") -> str` — default `./tasks.db`.
- `create_db(db_path) -> None` — idempotent table creation.
- `add_task(db_path, title) -> int` — strips title, rejects empty/>100 chars, autoincrement id.
- `list_tasks(db_path) -> list[Task]`, ordered by id.
- `get_task(db_path, task_id) -> Task | None` — bool rejected.
- `complete_task(db_path, task_id) -> bool`, `delete_task(db_path, task_id) -> bool`.
- API: `GET /`, `POST /tasks` (201), `GET /tasks`, `GET /tasks/{id}` (404), `PUT /tasks/{id}/complete` (404), `DELETE /tasks/{id}` (204 — no body per HTTP spec).

## Stages

**Minimal:** `storage.py` adapted from project 11: `tasks` table (`id`, `title`, `completed`, `created_at`), `Task` dataclass, `create_db`/`add_task`/`list_tasks`.

**Improved:** Full CRUD (`get_task`/`complete_task`/`delete_task`) with validation, `get_db_path` from env (`.env.example` documents `DATABASE_PATH`/`HOST`/`PORT`), `api.py` adapted from project 16 wrapping storage functions with Pydantic models.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy --strict` clean (strict for 11–20 per ARCHITECTURE.md §8), `pytest` green for every public function in `storage.py`+`api.py` (excl. `cli.py` per §5), tmp_path SQLite + TestClient without network, `argparse` CLI with subcommands and `serve` launching uvicorn, pinned deps per G-17.

## API

```python
from final_integration import (
    Task, add_task, complete_task, create_db, delete_task,
    get_db_path, get_host, get_port, get_task, list_tasks, app,
)
```

## Testing

```bash
pytest -v          # temp SQLite files + mocked HTTP, no network
ruff check .
black --check .
mypy --strict src
```

## ZuroKing's note

> This is the graduation cap: one app, three doors to the same data. The CLI writes rows that the API reads back — because both go through the same `storage.py`. That's the whole lesson: *layers*, not frameworks. Keep `storage.py` free of `fastapi` imports and `api.py` free of SQL — swap either side out and the other survives. Notice what was deliberately copied from projects 04, 11, 16 rather than imported: isolation means you can delete any sibling folder and this one still works. And when something feels duplicated across your own apps — that feeling is your next refactoring lesson, not this repo's job.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.

See also: [ARCHITECTURE.md](ARCHITECTURE.md) — required per §6.
