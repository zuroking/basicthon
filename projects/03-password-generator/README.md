# 03 — Password Generator

Isolated beginner project from the `basicthon` series (Foundations).

**What you learn (lock scope):** Cryptographically strong randomness with `secrets`, input validation, and simple heuristics for password strength. The project is built in three stages: minimal — generate a password from a fixed charset; improved — configurable charset (upper/digits/symbols) and length validation; production-like — typed, tested, `secrets.choice`-based, with strength estimator and argparse CLI.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` is stdlib-only for this project (`# stdlib only, no external dependencies`).

## Usage

Generate a default 12-character password (lower + upper + digits):

```bash
python -m password_generator
# aB3xK9mQ2pLq

python -m password_generator --length 16 --symbols
# aB3!xK9$mQ2@pLq&

python -m password_generator --length 8 --no-upper --no-digits
# abcdwxyz
```

Or use the console script after `pip install -e .`:

```bash
passgen --length 20 --symbols
# 9fG!2bQ@...
```

Use as a library:

```python
from password_generator import generate_password, check_strength

pwd = generate_password(length=16, use_symbols=True)
print(pwd, check_strength(pwd))
# "aB3!..." "strong"
```

## Stages

**Minimal:** `generate_password(length)` with fixed `string.ascii_letters + string.digits`, `secrets.choice`, `length >= 4` validation.

**Improved:** Configurable charset via `use_upper`/`use_digits`/`use_symbols` (lowercase always included), helper `_build_charset()` that raises `ValueError` if charset empty, `string.punctuation` for symbols.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy` clean, `pytest` green for every public function in `src/password_generator/generator.py` (excl. `cli.py` per ARCHITECTURE.md §5), `check_strength()` returning `"weak"`/`"medium"`/`"strong"` based on length and variety, CLI with `--length`/`--no-upper`/`--no-digits`/`--symbols`.

## API

```python
from password_generator import generate_password, check_strength

generate_password(length=12, use_upper=True, use_digits=True, use_symbols=False) -> str
# raises ValueError if length < 4 or charset empty

check_strength("aB3!5678")  # "strong"
check_strength("abcdef12")  # "medium"
check_strength("abc")       # "weak"
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## ZuroKing's note

> For passwords, never use `random` — it's predictable. `secrets` is the right tool even in a toy project. The habit "security-sensitive randomness = secrets" costs you nothing now and saves you later when you handle tokens or secrets for real.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
