# 05 — Grades Analyzer from CSV

Isolated beginner project from the `basicthon` series (Foundations).

**What you learn (lock scope):** CSV parsing with `csv` + `pathlib`, type-hinted statistics (average/median/min/max), sorting and bucketing, and clean separation of pure logic from I/O. The project is built in three stages: minimal — `parse_csv` + `average` with `csv.DictReader`; improved — `median`/`min_grade`/`max_grade`/`top_n` with file handling and validation; production-like — typed, tested, `argparse` CLI with `tmp_path`-based tests.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` is stdlib-only for this project (`# stdlib only, no external dependencies`).

## Usage

Create a CSV (header must contain `grade`):

```csv
name,grade
Alice,95
Bob,82
Cara,91
Dan,60
```

Analyze it:

```bash
python -m grades_analyzer grades.csv
# records: 4
# average: 82.00
# median: 86.50
# min: 60.00  max: 95.00
# distribution:
#   A: 2
#   B: 1
#   D: 1
#   F: 0
# top 3:
#   Alice — 95
#   Cara — 91
#   Bob — 82

python -m grades_analyzer grades.csv --top 2
# top 2:
#   Alice — 95
#   Cara — 91
```

Or use console script after `pip install -e .`:

```bash
grades-analyzer grades.csv --top 5
```

Use as a library:

```python
from grades_analyzer import parse_csv, average, median, top_n, grade_distribution

rows = parse_csv("grades.csv")
print(average(rows))              # 82.0
print(median(rows))               # 86.5
print(top_n(rows, n=2))           # [{'name': 'Alice', 'grade': '95'}, ...]
print(grade_distribution(rows))   # {'A': 2, 'B': 1, 'C': 0, 'D': 1, 'F': 0}
```

CSV may have extra columns (e.g., `subject`) — they are preserved in `parse_csv` but ignored by stats.

## Stages

**Minimal:** `parse_csv(path)` via `csv.DictReader` + `average(records)` (`sum/len`, `0.0` for empty). Validates existence of `grade` column, `ValueError` on missing/invalid grades, `FileNotFoundError` if file absent.

**Improved:** `median(records)` (sorted + even/odd handling, `0.0` for empty), `min_grade`/`max_grade` (`ValueError` if empty), `top_n(records, n=3)` stable descending sort, `grade_distribution(records)` bucketing `A` 90+, `B` 80-89, `C` 70-79, `D` 60-69, `F` <60. Pure functions operate on `list[dict[str, str]]` — easy to test without I/O.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy` clean, `pytest` green for every public function in `src/grades_analyzer/analyzer.py` (excl. `cli.py` per ARCHITECTURE.md §5) using `tmp_path` CSV fixtures, `argparse` CLI with positional `csv` and `--top` flag, `python -m grades_analyzer` entry point.

## API

```python
from grades_analyzer import parse_csv, average, median, min_grade, max_grade, top_n, grade_distribution
from pathlib import Path

parse_csv(path: str | Path) -> list[dict[str, str]]
# raises FileNotFoundError, ValueError if empty/missing grade column

average(records: list[dict[str, str]]) -> float
# 0.0 for empty

median(records: list[dict[str, str]]) -> float
# 0.0 for empty

min_grade(records: list[dict[str, str]]) -> float
# raises ValueError if empty

max_grade(records: list[dict[str, str]]) -> float
# raises ValueError if empty

top_n(records: list[dict[str, str]], n: int = 3) -> list[dict[str, str]]
# raises ValueError if n <= 0 or not int

grade_distribution(records: list[dict[str, str]]) -> dict[str, int]
# {'A': ..., 'B': ..., 'C': ..., 'D': ..., 'F': ...}
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## ZuroKing's note

> CSV looks trivial until you hit encodings, headers, and bad grades. The habit here is simple: validate early (`grade` column exists, every value is numeric), keep parsing in one place (`parse_csv`), and keep math pure (functions take `list[dict]` not a path). Then your CLI is just glue — `parse_csv` → `average/median/...` → `print` — and tests need only `tmp_path` to cover every rule.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
