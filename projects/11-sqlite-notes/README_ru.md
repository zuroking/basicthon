# 11 — Заметки на SQLite

Изолированный учебный проект из серии `basicthon` (Data & Algorithms).

**Что изучаем (lock scope):** CRUD на SQLite через `sqlite3` + `pathlib`, параметризованные запросы и чистое отделение логики БД от CLI. Проект в три этапа: minimal — `create_db`/`add_note`/`get_note`/`list_notes` с `AUTOINCREMENT`; improved — `update_note`/`delete_note`/`search_notes` через `LIKE` и валидацию; production-like — типизация, тесты, `ruff/black/mypy --strict`, CLI на `argparse` с тестами на `tmp_path`.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` для этого проекта stdlib-only (`# stdlib only, no external dependencies`).

## Использование

```bash
python -m sqlite_notes add "Покупки" "купить молоко"
# added [1] Покупки

python -m sqlite_notes list
# [1] Покупки | купить молоко | 2026-08-25 10:00:00

python -m sqlite_notes get 1
# [1] Покупки | купить молоко | 2026-08-25 10:00:00

python -m sqlite_notes update 1 --title "Список покупок"
# updated [1] Список покупок

python -m sqlite_notes search покуп
# [1] Список покупок | купить молоко

python -m sqlite_notes delete 1
# deleted [1]

# свой файл БД
python -m sqlite_notes --db /tmp/my.db add "Идея" "сделать приложение"
python -m sqlite_notes --db /tmp/my.db list
```

После `pip install -e .`:

```bash
sqlite-notes add "Привет" "мир"
sqlite-notes list --db notes.db
sqlite-notes search привет
```

Как библиотека:

```python
from pathlib import Path
from sqlite_notes import create_db, add_note, get_note, list_notes, update_note, delete_note, search_notes

db = Path("notes.db")
create_db(db)

nid = add_note(db, "Покупки", "купить молоко")
print(get_note(db, nid))
print(list_notes(db))
update_note(db, nid, title="Список")
print(search_notes(db, "список"))
delete_note(db, nid)
```

Детали:

- `create_db` создаёт директории и `CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`, идемпотентен.
- `add_note(db, title, content) -> int` — `title` после `strip` не пустой, `content` — `str` (пустой можно), вставляет `title.strip()` + `content`, возвращает `lastrowid`.
- `get_note(db, id) -> Note | None` — `None` если файла нет или не найдено; `ValueError` если `id` не `int`.
- `list_notes(db) -> list[Note]` по `id`; `[]` если файла нет.
- `update_note(db, id, title?, content?) -> Note` — хотя бы одно поле, валидация, `ValueError` если не найдено; новый `title` стрипуется.
- `delete_note(db, id) -> None` — `ValueError` если не найдено.
- `search_notes(db, query) -> list[Note]` — `LIKE %query%` по `title`/`content` без учёта регистра, по `id`; `[]` для пустого запроса или отсутствующего файла.

## Этапы

**Minimal:** Датакласс `Note` (`id`, `title`, `content`, `created_at`), `create_db(path)` через `Path.parent.mkdir` + `sqlite3.connect` + `CREATE TABLE IF NOT EXISTS`, `add_note` с `INSERT` и проверкой `lastrowid`, `get_note` с `SELECT ... WHERE id = ?` и `fetchone`, `list_notes` с `SELECT ... ORDER BY id`. `ValueError` на пустой `title`.

**Improved:** `update_note` с динамическим `SET` после проверки существования, `delete_note` с `DELETE` и проверкой `rowcount`, `search_notes` с `WHERE title LIKE ? OR content LIKE ?` (`%query%`, трим, пустой → `[]`). Мутирующие вызывают `CREATE TABLE IF NOT EXISTS`, читающие возвращают `[]`/`None` если файла нет.

**Production-like:** Type hints на всех публичных функциях, `ruff`/`black`/`mypy --strict` без ошибок (strict для 11–20 по §8 ARCHITECTURE.md), `pytest` зелёный для каждой публичной функции в `src/sqlite_notes/notes.py` (кроме `cli.py` по §5) с `tmp_path`, CLI на `argparse` с `--db` и подкомандами `add/get/list/update/delete/search`, точка входа `python -m sqlite_notes`.

## API

```python
from sqlite_notes import Note, create_db, add_note, get_note, list_notes, update_note, delete_note, search_notes

create_db(db_path: str | Path) -> None
add_note(db_path: str | Path, title: str, content: str) -> int
get_note(db_path: str | Path, note_id: int) -> Note | None
list_notes(db_path: str | Path) -> list[Note]
update_note(db_path: str | Path, note_id: int, title: str | None = None, content: str | None = None) -> Note
delete_note(db_path: str | Path, note_id: int) -> None
search_notes(db_path: str | Path, query: str) -> list[Note]
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## Заметка от ZuroKing

> SQLite — первый раз когда персистентность ощущается не как JSON-файл, а как таблица, которую ты спрашиваешь. Держи границу жёстко: `notes.py` знает только `sqlite3` + `Path` + `Note`, никакого `argparse` и `print`. Пусть `CREATE TABLE IF NOT EXISTS` делает каждую функцию идемпотентной, `?`-плейсхолдеры спасают от склейки SQL, а проверка `rowcount`/`fetchone` превращает "не найдено" в `ValueError`. Тогда CLI остаётся склейкой `parse_args` → `notes` → `print`, а тесты честны с `tmp_path` — реальные файлы, реальный SQL, без моков и сети.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.
