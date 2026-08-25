# 10 — Mini Test Framework

Isolated beginner project from the `basicthon` series (Structures & Patterns).

**What you learn (lock scope):** how assertions work, how to collect test results without a third-party runner, and how a test framework tests itself. The project is built in three stages: minimal — `assert_equal`/`assert_raises`, `TestResult` dataclass and `run_tests` on a demo suite; improved — more asserts (`assert_true`/`assert_false`/`assert_in`/`assert_not_in`/`assert_not_equal`), context-manager style `assert_raises`, `format_results`/`summarize`; production-like — typed, tested, `ruff/black/mypy` clean, `argparse` CLI with `--verbose`/`--list`.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` is stdlib-only for this project (`# stdlib only, no external dependencies`).

## Usage

Run the built-in demo suite (all 8 tests should pass):

```bash
python -m mini_test
# ........ (or 8 dots)
# 8 passed, 0 failed, 8 total

python -m mini_test --verbose
# PASS: test_add
# PASS: test_sub
# ...
# 8 passed, 0 failed, 8 total

python -m mini_test --list
# test_add
# test_sub
# ...
```

Or use console script after `pip install -e .`:

```bash
mini-test --verbose
mini-test --list
```

Use as a library:

```python
from mini_test import assert_equal, assert_raises, run_tests, get_demo_suite, format_results

# basic asserts
assert_equal(1 + 1, 2)
assert_raises(ValueError, int, "bad")
with assert_raises(ValueError):
    int("bad")

# run your own suite
def test_add():
    assert_equal(2 + 3, 5)

def test_div_zero():
    assert_raises(ZeroDivisionError, lambda: 1 / 0)

results = run_tests({"test_add": test_add, "test_div_zero": test_div_zero})
print(format_results(results, verbose=True))
# PASS: test_add
# PASS: test_div_zero
# 2 passed, 0 failed, 2 total

# run the built-in demo suite (framework tests itself)
from mini_test import DEMO_SUITE
results = run_tests(get_demo_suite())
print(format_results(results))
# 8 passed, 0 failed, 8 total

# mixed suite — framework correctly detects failures
def failing():
    assert_equal(1, 2)

mixed = {**get_demo_suite(), "fail_demo": failing}
results = run_tests(mixed)
print(format_results(results, verbose=True))
# shows 8 PASS and 1 FAIL
```

Details:

- `assert_equal(actual, expected, msg=None)` raises `AssertionError` with `"{actual!r} != {expected!r}"` if not equal, prefixed by `msg` if given. `assert_not_equal`/`assert_true`/`assert_false`/`assert_in`/`assert_not_in` follow same `msg` pattern.
- `assert_raises(expected, func=None, *args, **kwargs)` works in two styles: `assert_raises(ValueError, int, "bad")` or `with assert_raises(ValueError): int("bad")`. Returns context manager when `func is None`. Raises `AssertionError` if no exception or wrong type, with message `"expected X but got Y"`.
- `TestResult(name, passed, error)` is a dataclass. `run_test(name, func)` runs one zero-arg callable and returns `TestResult`; unexpected exceptions are captured with traceback.
- `run_tests(tests: dict[str, Callable[[], None]])` runs mapping in insertion order and returns `list[TestResult]`. `get_demo_suite()` returns a copy of `DEMO_SUITE` (8 passing demo tests).
- `format_results(results, verbose=False)` prints dots (`"."` pass, `"F"` fail) plus `FAIL` lines and summary `"N passed, M failed, K total"`; with `verbose=True` prints `PASS:`/`FAIL:` per test.
- `summarize(results)` returns `{"passed": int, "failed": int, "total": int}`.
- Demo helpers `_demo_add`/`_demo_sub`/`_demo_mul`/`_demo_div`/`_demo_is_even`/`_demo_reverse` are intentionally private (`_`) — only the 8 `demo_test_*` wrappers are in `DEMO_SUITE`.

## Stages

**Minimal:** `assert_equal(actual, expected, msg)` and `assert_raises(expected, func, *args)` that raise `AssertionError` on failure, `@dataclass TestResult(name, passed, error)`, `run_test(name, func)` with `try/except`, `run_tests(dict)` looping with `results.append(run_test(...))`, demo logic `_demo_add`/`_demo_div` and `DEMO_SUITE` with 2–3 passing tests, `get_demo_suite()` returning copy.

**Improved:** Added `assert_not_equal`/`assert_true`/`assert_false`/`assert_in`/`assert_not_in` with optional `msg`, `_AssertRaisesContext` for `with assert_raises(Exc):` (stores `exception`, `__enter__`/`__exit__` logic), `format_results(results, verbose)` (dots vs `PASS:` lines) and `summarize(results)` (`passed`/`failed`/`total`), expanded demo suite to 8 tests including `demo_test_is_even`/`demo_test_reverse`/`demo_test_in` and context-style `demo_test_div_zero`, helpers cover `str | list` cases.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy` clean (ordinary, not `--strict` per 01–10), `pytest` green via self-test (`run_tests(get_demo_suite())` must be all passed + mixed suite detects failure), `argparse` CLI with `--verbose`/`--list`, exit 1 on failure, `python -m mini_test` entry point, docs with 3 stages and ZuroKing note.

## API

```python
from mini_test import (
    TestResult, assert_equal, assert_not_equal, assert_true, assert_false,
    assert_in, assert_not_in, assert_raises, run_test, run_tests,
    format_results, summarize, get_demo_suite, DEMO_SUITE
)

assert_equal(actual, expected, msg: str | None = None) -> None
assert_not_equal(actual, expected, msg: str | None = None) -> None
assert_true(value, msg: str | None = None) -> None
assert_false(value, msg: str | None = None) -> None
assert_in(item, container, msg: str | None = None) -> None
assert_not_in(item, container, msg: str | None = None) -> None
assert_raises(expected: type[BaseException], func=None, *args, **kwargs) -> Any
# context: with assert_raises(Exc): ...  # .exception holds caught exc

TestResult(name: str, passed: bool, error: str | None = None)

run_test(name: str, func: Callable[[], None]) -> TestResult
run_tests(tests: dict[str, Callable[[], None]]) -> list[TestResult]
format_results(results: list[TestResult], verbose: bool = False) -> str
summarize(results: list[TestResult]) -> dict[str, int]
get_demo_suite() -> dict[str, Callable[[], None]]
DEMO_SUITE: dict[str, Callable[[], None]]  # 8 passing demo tests
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## ZuroKing's note

> Building your own test runner is the first time you see that testing is not magic — it's just a `try/except` around a function. Keep asserts dumb: compare and raise `AssertionError` with a clear message. Let `run_test` do the only smart thing — catch that error and pack `TestResult(name, passed, error)`. Then `run_tests` is a loop, `format_results` is a counter, and self-test is one line: `run_tests(get_demo_suite())` must be all green. Once you feel that loop, `pytest` stops being a black box.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
