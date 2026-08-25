"""Tests for mini_test.framework — framework tests itself on demo set.

Per GRILL2-05 the criterion for #10 is not per-function pytest coverage
but "framework correctly tests itself on built-in demo suite". So the
central tests run ``run_tests`` on ``DEMO_SUITE`` / ``get_demo_suite``
and assert expected counts.
"""

from __future__ import annotations

import pytest

from mini_test.framework import (
    DEMO_SUITE,
    TestResult,
    assert_equal,
    assert_false,
    assert_in,
    assert_not_equal,
    assert_not_in,
    assert_raises,
    assert_true,
    format_results,
    get_demo_suite,
    run_test,
    run_tests,
    summarize,
)

# ---- assert helpers ----


def test_assert_equal_pass() -> None:
    assert_equal(1, 1)
    assert_equal("a", "a")
    assert_equal([1, 2], [1, 2])


def test_assert_equal_fail() -> None:
    with pytest.raises(AssertionError, match="1 != 2"):
        assert_equal(1, 2)
    with pytest.raises(AssertionError, match="custom"):
        assert_equal(1, 2, msg="custom")


def test_assert_not_equal_pass() -> None:
    assert_not_equal(1, 2)


def test_assert_not_equal_fail() -> None:
    with pytest.raises(AssertionError):
        assert_not_equal(1, 1)


def test_assert_true_pass() -> None:
    assert_true(True)
    assert_true(1)
    assert_true("x")


def test_assert_true_fail() -> None:
    with pytest.raises(AssertionError):
        assert_true(False)
    with pytest.raises(AssertionError, match="my msg"):
        assert_true(False, msg="my msg")


def test_assert_false_pass() -> None:
    assert_false(False)
    assert_false(0)
    assert_false("")


def test_assert_false_fail() -> None:
    with pytest.raises(AssertionError):
        assert_false(True)


def test_assert_in_pass() -> None:
    assert_in(2, [1, 2, 3])
    assert_in("a", "abc")


def test_assert_in_fail() -> None:
    with pytest.raises(AssertionError):
        assert_in(5, [1, 2, 3])


def test_assert_not_in_pass() -> None:
    assert_not_in(5, [1, 2, 3])


def test_assert_not_in_fail() -> None:
    with pytest.raises(AssertionError):
        assert_not_in(2, [1, 2, 3])


def test_assert_raises_func_style_pass() -> None:
    def bad() -> None:
        raise ValueError("bad")

    assert_raises(ValueError, bad)
    assert_raises(ValueError, lambda: int("not-int"))


def test_assert_raises_func_style_with_args() -> None:
    def div(a: float, b: float) -> float:
        if b == 0:
            raise ZeroDivisionError("zero")
        return a / b

    assert_raises(ZeroDivisionError, div, 1, 0)


def test_assert_raises_func_style_fail_no_exception() -> None:
    with pytest.raises(AssertionError, match="no exception"):
        assert_raises(ValueError, lambda: 1 + 1)


def test_assert_raises_func_style_fail_wrong_type() -> None:
    def bad() -> None:
        raise TypeError("oops")

    with pytest.raises(AssertionError, match="expected ValueError but got TypeError"):
        assert_raises(ValueError, bad)


def test_assert_raises_context_pass() -> None:
    with assert_raises(ValueError):
        raise ValueError("ok")
    ctx = assert_raises(ValueError)
    with ctx:
        raise ValueError("also ok")
    assert ctx.exception is not None


def test_assert_raises_context_fail_no_exception() -> None:
    with pytest.raises(AssertionError, match="no exception"):
        with assert_raises(ValueError):
            pass


def test_assert_raises_context_fail_wrong_type() -> None:
    with pytest.raises(AssertionError, match="expected ValueError"):
        with assert_raises(ValueError):
            raise RuntimeError("wrong")


# ---- TestResult / run_test / run_tests ----


def test_testresult_fields() -> None:
    r = TestResult(name="x", passed=True)
    assert r.name == "x"
    assert r.passed is True
    assert r.error is None
    r2 = TestResult(name="y", passed=False, error="boom")
    assert r2.passed is False
    assert r2.error == "boom"


def test_run_test_pass() -> None:
    def ok() -> None:
        assert_equal(1, 1)

    res = run_test("ok", ok)
    assert res.passed is True
    assert res.error is None


def test_run_test_fail_assertion() -> None:
    def bad() -> None:
        assert_equal(1, 2)

    res = run_test("bad", bad)
    assert res.passed is False
    assert res.error is not None
    assert "1" in res.error


def test_run_test_fail_exception() -> None:
    def boom() -> None:
        raise RuntimeError("unexpected")

    res = run_test("boom", boom)
    assert res.passed is False
    assert "RuntimeError" in res.error  # type: ignore[operator]


def test_run_tests_all_pass() -> None:
    def a() -> None:
        assert_true(True)

    def b() -> None:
        assert_equal(2, 2)

    results = run_tests({"a": a, "b": b})
    assert len(results) == 2
    assert all(r.passed for r in results)
    assert summarize(results) == {"passed": 2, "failed": 0, "total": 2}


def test_run_tests_mixed() -> None:
    def passing() -> None:
        assert_equal(1, 1)

    def failing() -> None:
        assert_equal(1, 2)

    results = run_tests({"passing": passing, "failing": failing})
    assert len(results) == 2
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]
    assert len(passed) == 1
    assert len(failed) == 1
    assert failed[0].name == "failing"


def test_format_results_verbose() -> None:
    def ok() -> None:
        assert_true(True)

    def bad() -> None:
        assert_true(False)

    results = run_tests({"ok": ok, "bad": bad})
    text = format_results(results, verbose=True)
    assert "PASS: ok" in text
    assert "FAIL: bad" in text
    assert "1 passed, 1 failed, 2 total" in text


def test_format_results_dots() -> None:
    def ok() -> None:
        assert_true(True)

    def bad() -> None:
        assert_true(False)

    results = run_tests({"ok": ok, "bad": bad})
    text = format_results(results, verbose=False)
    # dots line + fail detail + summary
    assert "1 passed, 1 failed, 2 total" in text
    assert "FAIL: bad" in text


def test_summarize() -> None:
    def ok() -> None:
        pass

    results = run_tests({"ok": ok})
    assert summarize(results)["passed"] == 1
    assert summarize(results)["total"] == 1


def test_get_demo_suite_all_pass() -> None:
    suite = get_demo_suite()
    # ensure copy – mutating returned dict does not affect original
    suite["extra"] = lambda: None
    assert "extra" not in DEMO_SUITE
    assert len(DEMO_SUITE) == len(get_demo_suite())


# ---- The core GRILL2-05 criterion: framework tests itself on demo set ----


def test_demo_suite_self_test() -> None:
    """Framework correctly tests itself on built-in demo suite (all passing)."""
    suite = get_demo_suite()
    assert len(suite) == 8
    results = run_tests(suite)
    assert len(results) == 8
    assert all(r.passed for r in results), format_results(results, verbose=True)
    summary = summarize(results)
    assert summary == {"passed": 8, "failed": 0, "total": 8}
    text = format_results(results, verbose=False)
    assert "8 passed, 0 failed, 8 total" in text


def test_demo_suite_is_deterministic() -> None:
    """Running the demo suite twice yields same results."""
    r1 = run_tests(get_demo_suite())
    r2 = run_tests(get_demo_suite())
    assert [x.passed for x in r1] == [x.passed for x in r2]
    assert [x.name for x in r1] == [x.name for x in r2]


def test_framework_detects_intentional_failure() -> None:
    """Framework must also correctly detect failures (negative check)."""

    def should_fail() -> None:
        assert_equal(1, 2)

    mixed = dict(get_demo_suite())
    mixed["intentional_fail"] = should_fail
    results = run_tests(mixed)
    summary = summarize(results)
    assert summary["total"] == 9
    assert summary["passed"] == 8
    assert summary["failed"] == 1
    failed_names = [r.name for r in results if not r.passed]
    assert "intentional_fail" in failed_names
