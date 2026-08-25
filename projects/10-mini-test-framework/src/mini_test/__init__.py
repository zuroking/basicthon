"""mini_test — simple test framework (basicthon #10)."""

from mini_test.framework import (
    DEMO_SUITE,
    TestResult,
    _AssertRaisesContext,
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

__all__ = [
    "DEMO_SUITE",
    "TestResult",
    "_AssertRaisesContext",
    "assert_equal",
    "assert_false",
    "assert_in",
    "assert_not_equal",
    "assert_not_in",
    "assert_raises",
    "assert_true",
    "format_results",
    "get_demo_suite",
    "run_test",
    "run_tests",
    "summarize",
]
