# 08 — Duplicate Finder

Isolated beginner project from the `basicthon` series (Structures & Patterns).

**What you learn (lock scope):** hashing files with `hashlib`, traversing directories with `pathlib`, and grouping by content hash to detect duplicates. The project is built in three stages: minimal — `hash_file` that returns SHA-256 hex digest reading in chunks; improved — `find_duplicates` that scans a directory, hashes each file and returns `hash -> [Paths]` for groups with `>1` member; production-like — typed, tested, `ruff/black/mypy` clean, `argparse` CLI with `--no-recursive`.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` is stdlib-only for this project (`# stdlib only, no external dependencies`).

## Usage

Scan a directory for duplicates (recursive by default):

```bash
python -m duplicate_finder ./photos
# hash 9f64a747e1b97f131fabb6b447296c9b6f0201e79fb3c5356e6c77e89b6a806a:
#   photos/a.jpg
#   photos/copy_of_a.jpg
# found 1 duplicate group(s), 2 file(s) total

# only top-level (no recursion):
python -m duplicate_finder ./photos --no-recursive
# no duplicates found

# explicit path:
python -m duplicate_finder /tmp/my_folder
```

Or use console script after `pip install -e .`:

```bash
duplicate-finder ./photos --no-recursive
```

Use as a library:

```python
from duplicate_finder import hash_file, find_duplicates
from pathlib import Path

print(hash_file("photo.jpg"))
# 9f64a747e1b97f131fabb6b447296c9b6f0201e79fb3c5356e6c77e89b6a806a

dups = find_duplicates("./photos")
# {'9f64a7...': [Path('photos/a.jpg'), Path('photos/copy_of_a.jpg')]}

dups_flat = find_duplicates(Path("./photos"), recursive=False)
# only top-level files

for file_hash, paths in dups.items():
    print(file_hash, [str(p) for p in paths])
```

Details:

- `hash_file` reads in chunks (`chunk_size=8192` by default) so large files do not exhaust memory. Raises `FileNotFoundError` if missing, `IsADirectoryError` if path is a directory, `ValueError` if `chunk_size <= 0`.
- `find_duplicates` collects files via `Path.rglob("*")` when `recursive=True` or `Path.iterdir()` when `False`, hashes each file, groups by hash, keeps only groups with `>1` file, sorts each group for deterministic output. Raises `FileNotFoundError` / `NotADirectoryError` for invalid directory.
- Empty files are handled: two empty files share the SHA-256 of empty bytes and are reported as duplicates.
- Binary and text files are treated identically (read as bytes).

## Stages

**Minimal:** `hash_file(file_path, chunk_size=8192)` via `hashlib.sha256`. Opens file in `rb`, loops `read(chunk_size)` until empty, updates hasher, returns `hexdigest()`. Validates `chunk_size > 0`, existence and not-a-directory.

**Improved:** `find_duplicates(directory, recursive=True)` — validates `directory` exists and is a directory, collects files (`rglob` vs `iterdir` + `is_file()` filter), hashes via `hash_file`, groups with `dict[str, list[Path]]`, filters `len > 1`, sorts each list, returns `dict[str, list[Path]]`.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy` clean, `pytest` green for every public function in `src/duplicate_finder/finder.py` (excl. `cli.py` per ARCHITECTURE.md §5) using `tmp_path` fixtures for real file-system tests, `argparse` CLI with positional `directory` and flag `--no-recursive`, `python -m duplicate_finder` entry point.

## API

```python
from duplicate_finder import hash_file, find_duplicates
from pathlib import Path

hash_file(file_path: str | Path, chunk_size: int = 8192) -> str
# SHA-256 hex digest (64 chars)
# raises FileNotFoundError if missing
# raises IsADirectoryError if path is dir
# raises ValueError if chunk_size <= 0

find_duplicates(directory: str | Path, recursive: bool = True) -> dict[str, list[Path]]
# hash -> sorted list of duplicate Paths (len > 1)
# raises FileNotFoundError if directory missing
# raises NotADirectoryError if path not a directory
# empty dict if no duplicates
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## ZuroKing's note

> Duplicate search is the first honest use of hashing you meet. No database, no index — just read bytes, feed `sha256`, group by digest. The trick is not the hash but the edges: chunked reading for big files, `rglob` vs `iterdir` for recursion, sorting groups for stable tests, and failing fast on bad paths. Keep `hash_file` dumb and pure, let `find_duplicates` do only grouping, and CLI becomes two lines of printing. That separation is why you can test everything with `tmp_path` — real files, real hashes, no mocks.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
