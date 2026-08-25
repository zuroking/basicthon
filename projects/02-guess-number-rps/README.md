# 02 — Guess Number + Rock-Paper-Scissors

Isolated beginner project from `basicthon` (Foundations).

**What you learn:** `random`, pure functions, input validation, branching. Three stages: minimal — `check_guess`/`rps_result` functions; improved — random secrets and interactive loops; production-like — typed, tested, CLI with `--mode`.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

## Usage

```bash
python -m guess_rps --mode guess --low 1 --high 100
python -m guess_rps --mode rps
```

Or after install:

```bash
guess-rps --mode rps
```

## Stages

**Minimal:** `check_guess(secret, guess) -> "higher"|"lower"|"correct"`, `rps_result(player, computer)`.

**Improved:** `random_secret`, `random_rps_choice`, interactive loops with `input()`.

**Production-like:** Type hints, `ruff`/`black`/`mypy` clean, tests for every public function outside `cli.py`.

## API

```python
from guess_rps import check_guess, rps_result
check_guess(42, 30)  # "higher"
rps_result("rock", "scissors")  # "win"
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy .
```

## ZuroKing's note

> Two tiny games, one lesson: separate pure logic from I/O. `game.py` has no `input()`/`print()` — so you can test it without mocking. `cli.py` is just glue.

## Isolation

Copy this folder anywhere; `pip install -e . && pip install -r requirements.txt` is enough.
