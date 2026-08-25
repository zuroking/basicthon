# 01 — CLI Calculator

Isolated beginner project from the `basicthon` series (Foundations).

**What you learn (lock scope):** Basic I/O, pure functions, error handling and safe expression parsing. The project is built in three stages: minimal — four arithmetic functions + CLI with two numbers; improved — safe `ast`-based evaluator with parentheses and precedence; production-like — typed, tested, documented, with REPL and proper error messages.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` is stdlib-only for this project (`# stdlib only, no external dependencies`).

## Usage

Evaluate a single expression:

```bash
python -m cli_calculator "2 + 3 * (4 - 1)"
# 11

python -m cli_calculator --expr "10 / 4"
# 2.5
```

Start interactive mode (no arguments):

```bash
python -m cli_calculator
>> 2 + 3 * 4
14
>> exit
```

Or use the console script after `pip install -e .`:

```bash
calc "2 ** 3 + 1"
# 9
```

## Stages

**Minimal:** `add`/`subtract`/`multiply`/`divide` + CLI that takes two numbers and an operator.

**Improved:** `evaluate()` parses full expression safely via `ast` (no `eval()`), handles `+ - * / // % **` , parentheses, unary `+/-`, whitespace and floats, with whitelisted AST nodes.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy` clean, `pytest` green for every public function in `src/cli_calculator/calculator.py` (excl. `cli.py` per ARCHITECTURE.md §5), clear error messages (`ValueError` for syntax, `ZeroDivisionError`).

## API

```python
from cli_calculator import add, subtract, multiply, divide, power, evaluate

add(2, 3)          # 5
evaluate("2 + 3 * 4")  # 14.0
evaluate("(2 + 3) * 4")  # 20.0
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy .
```

## ZuroKing's note

> I deliberately avoided `eval()` here — beginners often reach for it. Using `ast` with a whitelist is a tiny lesson in "safe by default" that pays off long before you touch auth or DBs. Keep this habit: *parse, don't execute*.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
