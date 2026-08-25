# 15 — Markov Chain Text Generator

Isolated beginner project from the `basicthon` series (Data & Algorithms).

**What you learn (lock scope):** building a Markov chain from text with `collections` and generating new text with `random`. The project is built in three stages: minimal — `build_chain`/`generate` for order-1 on whitespace-split words with `collections.defaultdict(list)` and `random.choice`; improved — support for n-gram `order` 1..5, `seed` for deterministic output via `random.Random(seed)`, `start` state validation, dead-end handling and strict input validation; production-like — typed, tested, `ruff/black/mypy --strict` clean, `argparse` CLI with deterministic tests.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` is stdlib-only for this project (`# stdlib only, no external dependencies`).

## Usage

Generate text from a string or file:

```bash
python -m markov_generator "hello world hello there world hello there"
# hello there world hello ...

python -m markov_generator --file story.txt --order 2 --length 30 --seed 42
# once upon a time there was ...

python -m markov_generator "a b a c a b a d" --order 1 --length 10 --seed 0 --start "a"
# a b a c a b a d a b

# custom order and deterministic seed
python -m markov_generator "the cat sat on the mat the cat ate" --order 2 --length 15 --seed 123
# the cat ate ...
```

Or use console script after `pip install -e .`:

```bash
markov-generator "hello world hello there" --length 10 --seed 1
markov-generator --file inputs/sample.txt --order 2 --length 20 --seed 42
markov-generator "a b c a b d" --order 2 --seed 0 --start "a b"
```

Use as a library:

```python
from markov_generator import build_chain, generate

text = "hello world hello there world hello"
chain = build_chain(text, order=1)
print(chain)
# {('hello',): ['world', 'there'], ('world',): ['hello'], ('there',): ['world']}

print(generate(chain, length=10, seed=42))
# hello world hello there world hello there world hello ...

# order-2 chain
chain2 = build_chain("a b c a b d a b e", order=2)
print(chain2)
# {('a', 'b'): ['c', 'd', 'e'], ('b', 'c'): ['a'], ('c', 'a'): ['b'], ...}

print(generate(chain2, length=6, seed=0, start=("a", "b")))
# a b c a b d

# deterministic: same seed -> same output
assert generate(chain, length=5, seed=0) == generate(chain, length=5, seed=0)
```

Details:

- `build_chain(text: str, order: int = 1) -> dict[tuple[str, ...], list[str]]` validates `text` is `str` and `order` is `int` 1..5 (rejects `bool`), splits on whitespace, returns `{}` if `len(words) <= order`, otherwise maps each `order`-gram tuple to list of successors using `collections.defaultdict(list)`.
- `generate(chain: dict[tuple[str, ...], list[str]], length: int = 20, seed: int | None = None, start: tuple[str, ...] | None = None) -> str` validates chain non-empty, uniform key length, values non-empty `list[str]`, `length` 1..1000, `seed` int if given, `start` tuple matching order and existing in chain. Uses `random.Random(seed)` and `rng.choice` for deterministic walks; starts from random key if `start` is `None`, walks with `tuple(result[-order:])`, stops early on dead-end, returns `" ".join(result[:length])`.

## Stages

**Minimal:** `build_chain(text, order=1)` split, `collections.defaultdict(list)`, loop `for i in range(len(words)-order): key=tuple(words[i:i+order]), chain[key].append(words[i+order])`, `generate(chain, length=20)` random walk from random key with `random.choice`, join. Basic `ValueError` on wrong types.

**Improved:** `order` 1..5, `seed` via `random.Random(seed)` for determinism, `start` param with validation (tuple length matches order, exists in chain), length 1..1000, dead-end break when `chain.get(key)` missing, chain shape validation (keys tuples, values lists, uniform order, non-empty strings), empty/whitespace text returns `{}`, `text`/`order` `bool` rejection.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy --strict` clean (strict for 11–20 per ARCHITECTURE.md §8), `pytest` green for every public function in `src/markov_generator/markov.py` (excl. `cli.py` per §5) with deterministic `seed` tests, `argparse` CLI with `text`/`--file`/`--order`/`--length`/`--seed`/`--start` and `python -m markov_generator` entry point.

## API

```python
from markov_generator import build_chain, generate

build_chain(text: str, order: int = 1) -> dict[tuple[str, ...], list[str]]
generate(chain: dict[tuple[str, ...], list[str]], length: int = 20, seed: int | None = None, start: tuple[str, ...] | None = None) -> str
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## ZuroKing's note

> Beginners think text generation is magic from an LLM. Show the primitive: a Markov chain remembers only the last `order` words. With `order=1`, `"hello"` is followed by what you saw after `hello` before — `world` or `there`. `collections.defaultdict(list)` builds that table, `random.Random(seed).choice` walks it. Keep the boundary sharp: `markov.py` knows only `collections` + `random` + validation, no `argparse`, no `print`. Make `seed` explicit so tests are deterministic (`generate(chain, seed=0)` always same), handle dead-ends by stopping early, and validate everything (`order` 1..5, `length` 1..1000, `start` must exist). Then CLI is just `parse_args → build_chain → generate → print`, and tests stay honest with no mocks — just `seed`.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
