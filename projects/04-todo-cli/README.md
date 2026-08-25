# 04 — To-do CLI with JSON Persistence

Isolated beginner project from the `basicthon` series (Foundations).

**What you learn (lock scope):** JSON persistence with `json` + `pathlib`, dataclasses for domain modeling, and clean separation of pure logic from I/O. The project is built in three stages: minimal — in-memory `TodoItem` with `add/complete/delete/list`; improved — `load_todos`/`save_todos` with JSON file, auto-increment ids and `pathlib` handling; production-like — typed, tested, `argparse` CLI with `add/list/done/delete` and `tmp_path`-based tests.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` is stdlib-only for this project (`# stdlib only, no external dependencies`).

## Usage

Add, list, complete and delete todos (default file `todos.json` in current directory):

```bash
python -m todo_cli add "Buy milk"
# added [1] Buy milk

python -m todo_cli add "Read book"
# added [2] Read book

python -m todo_cli list
# [1] [ ] Buy milk
# [2] [ ] Read book

python -m todo_cli done 1
# completed [1] Buy milk

python -m todo_cli list --all
# [1] [x] Buy milk
# [2] [ ] Read book

python -m todo_cli list --json
# [
#   {"id": 1, "title": "Buy milk", "completed": true},
#   {"id": 2, "title": "Read book", "completed": false}
# ]

python -m todo_cli delete 2
# deleted [2]
```

Use custom file:

```bash
python -m todo_cli --file /tmp/my.json add "Task"
python -m todo_cli --file /tmp/my.json list --all
```

Or use console script after `pip install -e .`:

```bash
todo add "Buy milk"
todo list --all
```

Use as a library:

```python
from pathlib import Path
from todo_cli import TodoItem, add_todo, complete_todo, delete_todo, list_todos, load_todos, save_todos

path = Path("todos.json")
items = load_todos(path)
add_todo(items, "Write tests")
complete_todo(items, 1)
print(list_todos(items, completed=False))
save_todos(path, items)
```

## Stages

**Minimal:** `TodoItem` dataclass (`id`, `title`, `completed=False`) and pure in-memory functions `add_todo(items, title)`, `complete_todo(items, id)`, `delete_todo(items, id)`, `list_todos(items)` — no file I/O, `id` as `max+1`, `ValueError` on empty title or missing id.

**Improved:** JSON persistence with `load_todos(path)`/`save_todos(path, items)` via `json` + `Path`, missing/empty file → `[]`, parent dirs auto-created, `ensure_ascii=False` + `indent=2`, round-trip `asdict`/`TodoItem`, filtering `list_todos(..., completed=True/False/None)`.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy` clean, `pytest` green for every public function in `src/todo_cli/todo.py` (excl. `cli.py` per ARCHITECTURE.md §5) using `tmp_path`, `argparse` CLI with subcommands `add/list/done/delete`, `--file` and `--json` flags, `python -m todo_cli` entry point.

## API

```python
from todo_cli import TodoItem, load_todos, save_todos, add_todo, complete_todo, delete_todo, list_todos

@dataclass
class TodoItem:
    id: int
    title: str
    completed: bool = False

load_todos(path: str | Path) -> list[TodoItem]
save_todos(path: str | Path, items: list[TodoItem]) -> None

add_todo(items: list[TodoItem], title: str) -> TodoItem
# raises ValueError if title empty or not str; mutates list, id = max+1

complete_todo(items: list[TodoItem], todo_id: int) -> TodoItem
# raises ValueError if not found

delete_todo(items: list[TodoItem], todo_id: int) -> None
# raises ValueError if not found

list_todos(items: list[TodoItem], *, completed: bool | None = None) -> list[TodoItem]
# None -> all, True -> done, False -> pending
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## ZuroKing's note

> Persistence is not magic — it's just `json.dump` and `json.load` with a file path. The key habit here is to keep pure list logic in `todo.py` and push `Path`/`json` + `argparse` into `cli.py`. That way you can test every rule with `tmp_path` without mocking CLI, and the file format stays obvious: a JSON array you can open and read yourself.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
