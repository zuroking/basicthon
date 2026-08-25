# ELI5 — Timer Logger

Imagine a stopwatch with a notebook.

- `Timer` is the stopwatch: `start()` presses start, `stop()` presses stop and tells seconds, `elapsed` shows how long has passed (works as `t.elapsed` or `t.elapsed()`), `is_running` says if ticking, `reset()` zeros it.
- `with Timer() as t:` is like "hold button automatically": it starts when you enter, stops when you leave, even if you stumble (exception).
- If you give `log_file`, the stopwatch writes `2026-08-25T10:00:00 - label: 1.234567s` into that file, creating folders if needed.
- `format_elapsed(90.123)` is the friendly display: `"1m 30.123s"` (or `"1h 2m 3.456s"` for long).
- `log_message("hello", "my.log")` writes `"timestamp - hello"` to file. `read_logs` reads lines, `clear_logs` erases, `log_elapsed` writes `"label: 1.500s"`.

Rules a child can follow:

- Press start twice → error. Press stop before start → error.
- `elapsed` before start is `0.0`; while running it shows current time.
- Every public piece is tested with fake time (`patch perf_counter`) and real files in `tmp_path`, no real waiting.
