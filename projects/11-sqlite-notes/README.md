# 11 — SQLite Notes

Isolated beginner project from the `basicthon` series (Data & Algorithms).

**What you learn (lock scope):** SQLite CRUD with `sqlite3` + `pathlib`, parameterized queries, and clean separation of DB logic from CLI. The project is built in three stages: minimal — `create_db`/`add_note`/`get_note`/`list_notes` with `INTEGER PRIMARY KEY AUTOINCREMENT`; improved — `update_note`/`delete_note`/`search_notes` with `LIKE` and validation; production-like — typed, tested, `ruff/black/mypy --strict` clean, `argparse` CLI with `tmp_path`-based tests.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` is stdlib-only for this project (`# stdlib only, no external dependencies`).

## Usage

Create and query notes (default DB `notes.db` in current directory):

```bash
python -m sqlite_notes add "Shopping" "buy milk"
# added [1] Shopping

python -m sqlite_notes list
# [1] Shopping | buy milk | 2026-08-25 10:00:00

python -m sqlite_notes get 1
# [1] Shopping | buy milk | 2026-08-25 10:00:00

python -m sqlite_notes update 1 --title "Shopping list"
# updated [1] Shopping list

python -m sqlite_notes search shop
# [1] Shopping list | buy milk

python -m sqlite_notes delete 1
# deleted [1]

# custom DB path
python -m sqlite_notes --db /tmp/my.db add "Idea" "build app"
python -m sqlite_notes --db /tmp/my.db list
```

Or use console script after `pip install -e .`:

```bash
sqlite-notes add "Hello" "world"
sqlite-notes list --db notes.db
sqlite-notes search hello
```

Use as a library:

```python
from pathlib import Path
from sqlite_notes import create_db, add_note, get_note, list_notes, update_note, delete_note, search_notes

db = Path("notes.db")
create_db(db)

nid = add_note(db, "Shopping", "buy milk")
print(get_note(db, nid))
# Note(id=1, title='Shopping', content='buy milk', created_at='2026-08-25 ...')

print(list_notes(db))
# [Note(id=1, ...)]

update_note(db, nid, title="Shopping list")
print(search_notes(db, "shop"))
# [Note(id=1, title='Shopping list', ...)]

delete_note(db, nid)
```

Details:

- `create_db` creates parent directories and `CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`. Idempotent.
- `add_note(db, title, content) -> int` validates `title` non-empty after `strip`, `content` must be `str`, inserts `title.strip()` + `content` (empty content allowed), returns `lastrowid`.
- `get_note(db, id) -> Note | None` returns `None` if DB missing or id not found; raises `ValueError` if `id` not `int`.
- `list_notes(db) -> list[Note]` ordered by `id`; `[]` if DB missing.
- `update_note(db, id, title=None, content=None) -> Note` at least one field required; validates, raises `ValueError` if not found; strips new title.
- `delete_note(db, id) -> None` raises `ValueError` if not found.
- `search_notes(db, query) -> list[Note]` case-insensitive `LIKE %query%` on `title`/`content`, ordered by `id`; `[]` for empty/whitespace query or missing DB; raises `ValueError` if query not `str`.

## Stages

**Minimal:** `Note` dataclass (`id`, `title`, `content`, `created_at`), `create_db(path)` with `pathlib.Path.parent.mkdir` + `sqlite3.connect` + `CREATE TABLE IF NOT EXISTS`, `add_note` with `INSERT ... VALUES (?, ?)` and `lastrowid` check, `get_note` with `SELECT ... WHERE id = ?` and `fetchone`, `list_notes` with `SELECT ... ORDER BY id` and `fetchall`. Validation `ValueError` on empty title.

**Improved:** `update_note` with dynamic `SET` (`title = ?`/`content = ?`) after existence check, `delete_note` with `DELETE ... WHERE id = ?` and `rowcount` check, `search_notes` with `WHERE title LIKE ? OR content LIKE ?` (`%query%` pattern, trims query, empty → `[]`). All mutating paths call `_CREATE_TABLE_SQL` to survive missing table; read paths return `[]`/`None` if file missing.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy --strict` clean (strict for 11–20 per ARCHITECTURE.md §8), `pytest` green for every public function in `src/sqlite_notes/notes.py` (excl. `cli.py` per §5) using `tmp_path` SQLite files, `argparse` CLI with `--db` and subcommands `add/get/list/update/delete/search`, `python -m sqlite_notes` entry point.

## API

```python
from sqlite_notes import Note, create_db, add_note, get_note, list_notes, update_note, delete_note, search_notes
from pathlib import Path

@dataclass
class Note:
    id: int
    title: str
    content: str
    created_at: str

create_db(db_path: str | Path) -> None
add_note(db_path: str | Path, title: str, content: str) -> int
get_note(db_path: str | Path, note_id: int) -> Note | None
list_notes(db_path: str | Path) -> list[Note]
update_note(db_path: str | Path, note_id: int, title: str | None = None, content: str | None = None) -> Note
delete_note(db_path: str | Path, note_id: int) -> None
search_notes(db_path: str | Path, query: str) -> list[Note]
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## ZuroKing's note

> SQLite is the first time a beginner feels that persistence is not a file of JSON but a table you query. Keep the boundary sharp: `notes.py` knows only `sqlite3` + `Path` + `Note`, no `argparse`, no `print`. Let `CREATE TABLE IF NOT EXISTS` make every function idempotent, use `?` placeholders to avoid string-mashing SQL, and check `rowcount`/`fetchone` to turn "not found" into `ValueError`. Then your CLI is just `parse_args` → `add_note`/`search_notes` → `print`, and tests stay honest with `tmp_path` — real files, real SQL, no mocks, no network.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
