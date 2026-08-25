"""Core logic for mini test framework.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): for project 10 the criterion is "framework correctly
tests itself on built-in demo set". CLI parsing lives in cli.py and is
excluded from that criterion.

Uses only stdlib (dataclasses, traceback, typing).
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class TestResult:
    """Result of a single test function.

    Attributes:
        name: Test name (usually function name or dict key).
        passed: True if test passed, False otherwise.
        error: Error message if failed, None if passed.
    """

    name: str
    passed: bool
    error: str | None = None

    # tell pytest not to collect this as a test class
    __test__ = False  # type: ignore[assignment]


def assert_equal(actual: Any, expected: Any, msg: str | None = None) -> None:
    """Assert that actual == expected.

    Raises:
        AssertionError: if values are not equal.
    """
    if actual != expected:
        default = f"{actual!r} != {expected!r}"
        raise AssertionError(f"{msg}: {default}" if msg else default)


def assert_not_equal(actual: Any, expected: Any, msg: str | None = None) -> None:
    """Assert that actual != expected.

    Raises:
        AssertionError: if values are equal.
    """
    if actual == expected:
        default = f"{actual!r} == {expected!r} (expected not equal)"
        raise AssertionError(f"{msg}: {default}" if msg else default)


def assert_true(value: Any, msg: str | None = None) -> None:
    """Assert that value is truthy.

    Raises:
        AssertionError: if value is falsy.
    """
    if not value:
        default = f"{value!r} is not true"
        raise AssertionError(f"{msg}: {default}" if msg else default)


def assert_false(value: Any, msg: str | None = None) -> None:
    """Assert that value is falsy.

    Raises:
        AssertionError: if value is truthy.
    """
    if value:
        default = f"{value!r} is not false"
        raise AssertionError(f"{msg}: {default}" if msg else default)


def assert_in(item: Any, container: Any, msg: str | None = None) -> None:
    """Assert that item is in container.

    Raises:
        AssertionError: if item not in container.
    """
    if item not in container:
        default = f"{item!r} not in {container!r}"
        raise AssertionError(f"{msg}: {default}" if msg else default)


def assert_not_in(item: Any, container: Any, msg: str | None = None) -> None:
    """Assert that item is not in container.

    Raises:
        AssertionError: if item is in container.
    """
    if item in container:
        default = f"{item!r} unexpectedly in {container!r}"
        raise AssertionError(f"{msg}: {default}" if msg else default)


class _AssertRaisesContext:
    """Context manager for assert_raises when used as ``with``."""

    def __init__(self, expected: type[BaseException]) -> None:
        self.expected: type[BaseException] = expected
        self.exception: BaseException | None = None

    def __enter__(self) -> _AssertRaisesContext:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        if exc_type is None:
            raise AssertionError(
                f"expected {self.expected.__name__} but no exception was raised"
            )
        if issubclass(exc_type, self.expected):
            self.exception = exc_val
            return True
        raise AssertionError(
            f"expected {self.expected.__name__} but got {exc_type.__name__}: {exc_val}"
        ) from exc_val


def assert_raises(
    expected: type[BaseException],
    func: Callable[..., Any] | None = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Assert that calling func raises expected exception.

    Can be used in two styles::

        assert_raises(ValueError, int, "bad")
        assert_raises(ValueError, lambda: int("bad"))

        with assert_raises(ValueError):
            int("bad")

    Args:
        expected: Expected exception type.
        func: Callable to invoke. If None, returns context manager.
        *args: Args for func.
        **kwargs: Kwargs for func.

    Raises:
        AssertionError: if no exception or wrong type.
    """
    if func is None:
        return _AssertRaisesContext(expected)
    try:
        func(*args, **kwargs)
    except expected:
        return None
    except Exception as exc:
        raise AssertionError(
            f"expected {expected.__name__} but got {type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError(f"expected {expected.__name__} but no exception was raised")


def run_test(name: str, func: Callable[[], None]) -> TestResult:
    """Run a single test function and capture result.

    Any AssertionError or other exception is treated as failure.
    """
    try:
        func()
        return TestResult(name=name, passed=True, error=None)
    except AssertionError as exc:
        msg = str(exc) if str(exc) else "AssertionError"
        return TestResult(name=name, passed=False, error=msg)
    except Exception as exc:  # pragma: no cover - generic safety
        tb = traceback.format_exc()
        # Keep message concise but include traceback for unexpected errors
        msg = f"{type(exc).__name__}: {exc}\n{tb}"
        return TestResult(name=name, passed=False, error=msg)


def run_tests(tests: dict[str, Callable[[], None]]) -> list[TestResult]:
    """Run a mapping of test name -> test function.

    Args:
        tests: Ordered mapping of name to zero-arg callable.

    Returns:
        List of TestResult in insertion order.
    """
    results: list[TestResult] = []
    for name, func in tests.items():
        results.append(run_test(name, func))
    return results


def format_results(results: list[TestResult], verbose: bool = False) -> str:
    """Format results for human-readable output.

    Args:
        results: List of TestResult.
        verbose: If True, show PASS/FAIL per test, else dots.

    Returns:
        Multiline string with per-test lines and summary.
    """
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    lines: list[str] = []
    if verbose:
        for r in results:
            if r.passed:
                lines.append(f"PASS: {r.name}")
            else:
                lines.append(f"FAIL: {r.name} — {r.error}")
    else:
        # short dots style: . for pass, F for fail
        dots = "".join("." if r.passed else "F" for r in results)
        if dots:
            lines.append(dots)
        for r in results:
            if not r.passed:
                lines.append(f"FAIL: {r.name} — {r.error}")
    lines.append(f"{passed} passed, {failed} failed, {len(results)} total")
    return "\n".join(lines)


def summarize(results: list[TestResult]) -> dict[str, int]:
    """Return summary counts for results.

    Returns:
        Dict with keys passed/failed/total.
    """
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    return {"passed": passed, "failed": failed, "total": len(results)}


# ---- Demo logic and demo suite (used for self-test) ----


def _demo_add(a: int, b: int) -> int:
    return a + b


def _demo_sub(a: int, b: int) -> int:
    return a - b


def _demo_mul(a: int, b: int) -> int:
    return a * b


def _demo_div(a: float, b: float) -> float:
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return a / b


def _demo_is_even(n: int) -> bool:
    return n % 2 == 0


def _demo_reverse(s: str) -> str:
    return s[::-1]


def demo_test_add() -> None:
    assert_equal(_demo_add(2, 3), 5)
    assert_equal(_demo_add(0, 5), 5)


def demo_test_sub() -> None:
    assert_equal(_demo_sub(5, 3), 2)
    assert_not_equal(_demo_sub(5, 3), 3)


def demo_test_mul() -> None:
    assert_equal(_demo_mul(3, 4), 12)


def demo_test_div() -> None:
    assert_equal(_demo_div(10, 2), 5.0)


def demo_test_div_zero() -> None:
    assert_raises(ZeroDivisionError, _demo_div, 10, 0)
    with assert_raises(ZeroDivisionError):
        _demo_div(1, 0)


def demo_test_is_even() -> None:
    assert_true(_demo_is_even(4))
    assert_false(_demo_is_even(3))
    assert_true(_demo_is_even(0))


def demo_test_reverse() -> None:
    assert_equal(_demo_reverse("abc"), "cba")
    assert_equal(_demo_reverse(""), "")


def demo_test_in() -> None:
    assert_in(3, [1, 2, 3])
    assert_not_in(5, [1, 2, 3])
    assert_in("a", "abc")


DEMO_SUITE: dict[str, Callable[[], None]] = {
    "test_add": demo_test_add,
    "test_sub": demo_test_sub,
    "test_mul": demo_test_mul,
    "test_div": demo_test_div,
    "test_div_zero": demo_test_div_zero,
    "test_is_even": demo_test_is_even,
    "test_reverse": demo_test_reverse,
    "test_in": demo_test_in,
}


def get_demo_suite() -> dict[str, Callable[[], None]]:
    """Return a copy of the built-in demo suite (all passing)."""
    return dict(DEMO_SUITE)
