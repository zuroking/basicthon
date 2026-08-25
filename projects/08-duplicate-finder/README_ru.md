# 08 — Поиск дубликатов

Изолированный учебный проект из серии `basicthon` (Structures & Patterns).

**Что изучаем (lock scope):** хеширование файлов через `hashlib`, обход директорий через `pathlib` и группировка по хешу содержимого. Проект в три этапа: minimal — `hash_file` возвращает SHA-256 хеш, читая файл чанками; improved — `find_duplicates` сканирует директорию, хеширует каждый файл и возвращает `hash -> [Path]` только для групп `>1`; production-like — типизация, тесты, `ruff/black/mypy` и CLI с `--no-recursive`.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` для этого проекта stdlib-only (`# stdlib only, no external dependencies`).

## Использование

```bash
python -m duplicate_finder ./photos
# hash 9f64a747e1b97f131fabb6b447296c9b6f0201e79fb3c5356e6c77e89b6a806a:
#   photos/a.jpg
#   photos/copy_of_a.jpg
# found 1 duplicate group(s), 2 file(s) total

python -m duplicate_finder ./photos --no-recursive
# no duplicates found
```

После `pip install -e .`:

```bash
duplicate-finder ./photos --no-recursive
```

Как библиотека:

```python
from duplicate_finder import hash_file, find_duplicates

print(hash_file("photo.jpg"))
# 9f64a747e1b97f131fabb6b447296c9b6f0201e79fb3c5356e6c77e89b6a806a

dups = find_duplicates("./photos")
dups_flat = find_duplicates("./photos", recursive=False)

for h, paths in dups.items():
    print(h, paths)
```

Детали:

- `hash_file` читает чанками (`chunk_size=8192`) — большие файлы не грузят память. Ошибки: `FileNotFoundError` если нет файла, `IsADirectoryError` если путь — директория, `ValueError` если `chunk_size <= 0`.
- `find_duplicates` собирает файлы через `Path.rglob("*")` при `recursive=True` или `Path.iterdir()` при `False`, хеширует через `hash_file`, группирует в `dict[str, list[Path]]`, оставляет только `len > 1`, сортирует каждую группу. Ошибки: `FileNotFoundError` / `NotADirectoryError` для неверной директории.
- Пустые файлы хешируются корректно — два пустых файла считаются дубликатами.
- Бинарные и текстовые файлы обрабатываются одинаково (чтение `rb`).

## Этапы

**Minimal:** `hash_file(file_path, chunk_size=8192)` через `hashlib.sha256`. Открывает `rb`, цикл `read(chunk_size)` до пустого чанка, `hasher.update`, возвращает `hexdigest()`. Проверяет `chunk_size > 0`, существование и не-директорию.

**Improved:** `find_duplicates(directory, recursive=True)` — проверяет `directory`, собирает файлы (`rglob` vs `iterdir` + `is_file()`), хеширует, группирует `dict[str, list[Path]]`, фильтрует `len > 1`, сортирует списки.

**Production-like:** Type hints на всех публичных функциях, `ruff`/`black`/`mypy` без ошибок, `pytest` зелёный для каждой публичной функции в `src/duplicate_finder/finder.py` (кроме `cli.py` по §5 ARCHITECTURE.md) через `tmp_path`, CLI на `argparse` с позиционным `directory` и флагом `--no-recursive`, точка входа `python -m duplicate_finder`.

## API

```python
from duplicate_finder import hash_file, find_duplicates

hash_file(file_path: str | Path, chunk_size: int = 8192) -> str
find_duplicates(directory: str | Path, recursive: bool = True) -> dict[str, list[Path]]
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## Заметка от ZuroKing

> Поиск дубликатов — первое честное применение хеширования. Без баз и индексов: читаешь байты, кормишь `sha256`, группируешь по дайджесту. Сложность не в хеше, а в краях: чтение чанками для больших файлов, `rglob` против `iterdir` для рекурсии, сортировка групп для стабильных тестов и быстрый fail на плохих путях. Держи `hash_file` глупым и чистым, пусть `find_duplicates` только группирует — и CLI становится двумя строками печати. Поэтому всё тестируется через `tmp_path` — настоящие файлы, настоящие хеши, без моков.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.
