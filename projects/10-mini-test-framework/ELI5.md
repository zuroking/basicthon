# ELI5 — Mini Test Framework

Imagine a tiny teacher who checks your homework.

- `assert_equal(2+2, 4)` is like "I think 2+2 is 4 — shout if not!" If wrong, it yells `AssertionError: 5 != 4`.
- `assert_true(is_even(4))` — "this should be True!" Same yell if False. `assert_in(3, [1,2,3])` — "3 should be inside!"
- `assert_raises(ValueError, lambda: int("bad"))` — "this should explode with ValueError!" Yells if no explosion.
- `TestResult(name, passed, error)` is a report card: name, green check or red cross, and why.
- `run_test("my test", my_func)` runs your test in a safety net (`try/except`), catches the yell and writes the card.
- `run_tests({"test_a": a, "test_b": b})` is the teacher checking a whole stack of homeworks, one by one, collecting cards.
- `format_results(cards)` counts greens and reds: `"2 passed, 1 failed, 3 total"` and shows dots `".F."` (dot = ok, F = fail) or `PASS:`/`FAIL:` if verbose.
- `DEMO_SUITE` is 8 example homeworks that are all correct — the teacher tests herself: `run_tests(get_demo_suite())` must be all green.

Rules a child can follow:

- Write a test as a function with no args that only calls asserts.
- To run, put it in a dict `{"name": func}` and call `run_tests`.
- If you add a failing test, teacher must spot it — that's how we know teacher works.
