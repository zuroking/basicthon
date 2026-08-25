# 07 — Организатор файлов

Изолированный учебный проект из серии `basicthon` (Structures & Patterns).

**Что изучаем (lock scope):** категоризация файлов по расширению через `pathlib`, перемещение через `shutil` и разделение чистой логики и CLI. Проект в три этапа: minimal — `get_category` мапит расширения на категории; improved — `organize` сканирует директорию и раскладывает файлы по `<категория>/` с обработкой коллизий; production-like — типизация, тесты, `ruff/black/mypy` и CLI с `--dry-run`.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` для этого проекта stdlib-only (`# stdlib only, no external dependencies`).

## Использование

```bash
python -m file_organizer ./messy ./organized
# photo.jpg -> images/
# organized 3 file(s) into 3 categor(ies)

python -m file_organizer ./messy ./organized --dry-run
# [dry-run] photo.jpg -> images/
# dry-run: 1 file(s) would be organized

# разложить на месте (dest по умолчанию = source):
python -m file_organizer ./messy
```

После `pip install -e .`:

```bash
file-organizer ./messy ./organized --dry-run
```

Как библиотека:

```python
from file_organizer import get_category, organize

print(get_category("photo.JPG"))  # images
print(get_category("README"))  # others

result = organize("./messy", "./organized")
preview = organize("./messy", "./organized", dry_run=True)
```

Категории: `images`, `documents`, `archives`, `audio`, `video`, `code`, `others` (для неизвестных и без расширения). Сравнение расширений — без учёта регистра через `Path.suffix.lower()`.

Коллизии: если `dest/images/photo.jpg` уже есть, входящий файл переименуется в `photo_1.jpg`, затем `_2` и т.д. Папки в `source` пропускаются — раскладываются только файлы верхнего уровня (без рекурсии).

## Этапы

**Minimal:** `get_category(filename)` через `CATEGORY_MAP` и обратный индекс `EXTENSION_TO_CATEGORY`. `Path.suffix.lower()`, `"others"` для отсутствующих/неизвестных.

**Improved:** `organize(source, dest, dry_run=False)` — проверяет `source`, создаёт `dest` при отсутствии, собирает файлы `Path.iterdir()`, считает категорию, создаёт `dest/category/`, решает коллизии `_unique_dest`, перемещает `shutil.move` (или пропускает при `dry_run`), возвращает `dict[str, list[str]]`.

**Production-like:** Type hints на всех публичных функциях, `ruff`/`black`/`mypy` без ошибок, `pytest` зелёный для каждой публичной функции в `src/file_organizer/organizer.py` (кроме `cli.py` по §5 ARCHITECTURE.md) через `tmp_path`, CLI на `argparse` с позиционными `source`/`dest` и флагом `--dry-run`, точка входа `python -m file_organizer`.

## API

```python
from file_organizer import get_category, organize

get_category(filename: str | Path) -> str
organize(source: str | Path, dest: str | Path, *, dry_run: bool = False) -> dict[str, list[str]]
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## Заметка от ZuroKing

> Раскладка файлов — первый раз когда файловая система чувствуется как база. Правило нарочно скучное: расширение → категория, переместить, при коллизии переименовать. Без рекурсии и магии — только `pathlib` и `shutil`. Это заставляет думать о краях сразу: что если файл уже есть в `dest`? что если `source == dest`? что если расширения нет? Решается маленьким `_unique_dest` и однострочным `get_category`, а `organize` остаётся тупым и тестируемым — CLI лишь печатает. Тестировать файловый код проще всего через `tmp_path` — настоящие файлы, настоящие перемещения, без моков.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.
