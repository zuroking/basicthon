# 07 — File Organizer

Isolated beginner project from the `basicthon` series (Structures & Patterns).

**What you learn (lock scope):** categorizing files by extension with `pathlib`, moving files with `shutil`, and keeping pure logic separate from CLI. The project is built in three stages: minimal — `get_category` mapping extensions to categories; improved — `organize` that scans a directory and moves files into `<category>/` subfolders with collision handling; production-like — typed, tested, `ruff/black/mypy` clean, `argparse` CLI with `--dry-run`.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` is stdlib-only for this project (`# stdlib only, no external dependencies`).

## Usage

Organize files from `source` into `dest` (creates `dest/<category>/` folders):

```bash
python -m file_organizer ./messy ./organized
# photo.jpg -> images/
# doc.pdf -> documents/
# song.mp3 -> audio/
# organized 3 file(s) into 3 categor(ies)

# dry-run — show what would be done without moving:
python -m file_organizer ./messy ./organized --dry-run
# [dry-run] photo.jpg -> images/
# dry-run: 1 file(s) would be organized

# organize in-place (dest defaults to source):
python -m file_organizer ./messy
# -> creates ./messy/images/, ./messy/documents/, ...
```

Or use console script after `pip install -e .`:

```bash
file-organizer ./messy ./organized --dry-run
```

Use as a library:

```python
from file_organizer import get_category, organize

print(get_category("photo.JPG"))  # images
print(get_category("report.pdf"))  # documents
print(get_category("archive.zip"))  # archives
print(get_category("README"))  # others

# move files, return mapping category -> [filenames]
result = organize("./messy", "./organized")
# {'images': ['photo.jpg'], 'documents': ['report.pdf']}

# preview without moving
preview = organize("./messy", "./organized", dry_run=True)
```

Categories: `images`, `documents`, `archives`, `audio`, `video`, `code`, `others` (fallback for unknown or no extension). Extension matching is case-insensitive and uses `Path.suffix`.

Collision handling: if `dest/images/photo.jpg` already exists, the incoming file is renamed to `photo_1.jpg`, then `photo_2.jpg`, etc. Directories in `source` are skipped — only top-level files are organized (non-recursive).

## Stages

**Minimal:** `get_category(filename)` via `CATEGORY_MAP` and reverse lookup `EXTENSION_TO_CATEGORY`. Case-insensitive `Path.suffix.lower()`, returns `"others"` for missing/unknown extensions.

**Improved:** `organize(source, dest, dry_run=False)` — validates `source` exists and is a directory, creates `dest` if needed, collects top-level files via `Path.iterdir()`, computes `category` per file, creates `dest/category/`, resolves collisions with `_unique_dest` (`_1`, `_2` …), moves with `shutil.move` (or skips if `dry_run`), returns `dict[str, list[str]]`.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy` clean, `pytest` green for every public function in `src/file_organizer/organizer.py` (excl. `cli.py` per ARCHITECTURE.md §5) using `tmp_path` fixtures for file-system tests, `argparse` CLI with positional `source`/`dest` and `--dry-run`, `python -m file_organizer` entry point.

## API

```python
from file_organizer import get_category, organize, CATEGORY_MAP
from pathlib import Path

get_category(filename: str | Path) -> str
# "images" | "documents" | "archives" | "audio" | "video" | "code" | "others"

organize(source: str | Path, dest: str | Path, *, dry_run: bool = False) -> dict[str, list[str]]
# raises FileNotFoundError if source missing
# raises NotADirectoryError if source not a dir or dest is a file
# moves files, returns mapping category -> [final filenames]

CATEGORY_MAP: dict[str, set[str]]
# category -> set of extensions (with dot, lowercased)
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## ZuroKing's note

> Organizing files is the first time you feel the filesystem as a database. The rule is boring on purpose: extension → category, move to folder, rename on collision. No recursion, no magic detection — just `pathlib` and `shutil`. That discipline forces you to think about edges early: what if `dest` already has the file? what if `source == dest`? what if there is no extension? Solve those with a tiny helper `_unique_dest` and a one-line `get_category`, keep `organize` dumb and testable, and the CLI becomes just printing. Filesystem code is easiest to test with `tmp_path` — real files, real moves, no mocks needed.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
