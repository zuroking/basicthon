# 04 — To-do CLI с JSON-персистентностью

Изолированный учебный проект из серии `basicthon` (Foundations).

**Что изучаем (lock scope):** Персистентность на `json` + `pathlib`, модель домена на `dataclass`, разделение чистой логики и I/O. Проект строится в три этапа: minimal — `TodoItem` в памяти с `add/complete/delete/list`; improved — `load_todos`/`save_todos` в JSON-файл, авто-инкремент id и работа с `Path`; production-like — типизация, тесты, CLI на `argparse` с `add/list/done/delete` и тесты на `tmp_path`.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` для этого проекта stdlib-only (`# stdlib only, no external dependencies`).

## Использование

```bash
python -m todo_cli add "Купить молоко"
# added [1] Купить молоко

python -m todo_cli list
# [1] [ ] Купить молоко

python -m todo_cli done 1
# completed [1] Купить молоко

python -m todo_cli list --all
# [1] [x] Купить молоко

python -m todo_cli list --json
# [
#   {"id": 1, "title": "Купить молоко", "completed": true}
# ]

python -m todo_cli delete 1
# deleted [1]
```

Свой файл:

```bash
python -m todo_cli --file /tmp/my.json add "Задача"
python -m todo_cli --file /tmp/my.json list --all
```

После `pip install -e .`:

```bash
todo add "Купить молоко"
todo list --all
```

Как библиотека:

```python
from pathlib import Path
from todo_cli import add_todo, complete_todo, list_todos, load_todos, save_todos

path = Path("todos.json")
items = load_todos(path)
add_todo(items, "Написать тесты")
complete_todo(items, 1)
print(list_todos(items, completed=False))
save_todos(path, items)
```

## Этапы

**Minimal:** Датакласс `TodoItem` (`id`, `title`, `completed=False`) и чистые функции `add_todo(items, title)`, `complete_todo(items, id)`, `delete_todo(items, id)`, `list_todos(items)` без I/O, `id = max+1`, `ValueError` на пустой title или отсутствующий id.

**Improved:** JSON-персистентность `load_todos(path)`/`save_todos(path, items)` через `json` + `Path`, отсутствующий/пустой файл → `[]`, создание родительских директорий, `ensure_ascii=False` + `indent=2`, round-trip через `asdict`/`TodoItem`, фильтрация `list_todos(..., completed=True/False/None)`.

**Production-like:** Type hints на всех публичных функциях, `ruff`/`black`/`mypy` без ошибок, `pytest` зелёный для каждой публичной функции в `src/todo_cli/todo.py` (кроме `cli.py` по §5 ARCHITECTURE.md) с `tmp_path`, CLI на `argparse` с подкомандами `add/list/done/delete`, флаги `--file`/`--json`, точка входа `python -m todo_cli`.

## API

```python
from todo_cli import TodoItem, load_todos, save_todos, add_todo, complete_todo, delete_todo, list_todos

load_todos(path: str | Path) -> list[TodoItem]
save_todos(path: str | Path, items: list[TodoItem]) -> None
add_todo(items: list[TodoItem], title: str) -> TodoItem
complete_todo(items: list[TodoItem], todo_id: int) -> TodoItem
delete_todo(items: list[TodoItem], todo_id: int) -> None
list_todos(items: list[TodoItem], *, completed: bool | None = None) -> list[TodoItem]
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## Заметка от ZuroKing

> Персистентность — это не магия, а `json.dump`/`json.load` и путь к файлу. Главный приём здесь — держать чистую логику списка в `todo.py`, а `Path`/`json` и `argparse` выносить в `cli.py`. Тогда каждое правило тестируется через `tmp_path` без моков CLI, а формат хранения остаётся прозрачным — JSON-массив, который можно открыть и прочитать глазами.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.
