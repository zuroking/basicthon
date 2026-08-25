# 09 — Timer Logger

Isolated beginner project from the `basicthon` series (Structures & Patterns).

**What you learn (lock scope):** measuring elapsed time with `time.perf_counter`, implementing the context-manager protocol (`__enter__`/`__exit__`), and logging timestamped entries to a file with `pathlib` + `datetime`. The project is built in three stages: minimal — `Timer` with `start`/`stop`/`elapsed` and `is_running`/`reset`; improved — context-manager support and automatic file logging on `stop`; production-like — typed, tested, `ruff/black/mypy` clean, `argparse` CLI with `--sleep`/`--label`/`--log`.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` is stdlib-only for this project (`# stdlib only, no external dependencies`).

## Usage

Measure a block with the Timer class:

```bash
python -m timer_logger --label "my task" --sleep 0.5
# my task: 0.501s

python -m timer_logger --label "logged" --sleep 0.2 --log timer.log
# logged: 0.201s
# logged to timer.log
cat timer.log
# 2026-08-25T10:00:00 - logged: 0.200123s

# custom log file, string path also works:
python -m timer_logger --sleep 1 --log /tmp/run.log --label "sleep 1s"
```

Or use console script after `pip install -e .`:

```bash
timer-logger --sleep 0.3 --label demo
timer-logger --sleep 0.1 --log ./my.log --label "quick"
```

Use as a library:

```python
from timer_logger import Timer, format_elapsed, log_message, read_logs, clear_logs, log_elapsed
from unittest.mock import patch

# basic start/stop
with patch("timer_logger.timer.time.perf_counter", side_effect=[100.0, 102.5]):
    t = Timer(label="task")
    t.start()
    elapsed = t.stop()  # 2.5
    print(float(t.elapsed))  # 2.5  (also t.elapsed() works)
    print(t.is_running)  # False

# context manager (auto stop + optional logging)
from pathlib import Path
import tempfile
tmp = Path(tempfile.gettempdir()) / "demo.log"
with Timer(label="block", log_file=tmp) as t:
    # work here
    pass
print(read_logs(tmp))  # ["2026-... - block: 0.000123s"]

# helpers
print(format_elapsed(90.123))  # "1m 30.123s"
log_message("hello", tmp)
log_elapsed("task", 1.5, tmp)
print(read_logs(tmp))
clear_logs(tmp)
```

Details:

- `Timer` uses `time.perf_counter` for monotonic high-resolution timing. `elapsed` works both as property (`t.elapsed`) and callable (`t.elapsed()`) via a float subclass, returning current interval if running or last interval if stopped (`0.0` if never started).
- `start` raises `RuntimeError` if already running; `stop` raises `RuntimeError` if not running. `reset` clears state to `0.0` and not running.
- Context manager `with Timer(...) as t:` calls `start` on entry and `stop` on exit (even if exception), logging automatically if `log_file` was given.
- `log_file` can be `str` or `Path`; parent directories are created. Each `stop` appends `"{iso_timestamp} - {label}: {elapsed:.6f}s\n"`. Label defaults to `"Timer"` if not given.
- `format_elapsed` formats `float` to `"X.XXXs"`, `"Xm Y.ZZZs"` for `>=60`, `"Xh Ym Z.ZZZs"` for `>=3600`; raises `ValueError` for negative/non-finite.
- `log_message`/`log_elapsed`/`read_logs`/`clear_logs` are thin file helpers — `read_logs` returns `[]` if missing, `clear_logs` truncates or creates empty file, all raise `IsADirectoryError` if path is a directory.

## Stages

**Minimal:** `Timer` with `__init__(label, log_file)`, `start()`, `stop() -> float`, `elapsed` (property/callable float), `is_running` property, `reset() -> None`. Internally stores `_start_time`/`_elapsed`/`_running`, uses `time.perf_counter`, raises `RuntimeError` on misuse, returns `0.0` before first start.

**Improved:** Context-manager protocol `__enter__`/`__exit__` (stop on exit even after exception), automatic logging in `stop`/`__exit__` via `_write_log` when `log_file` is set (creates parents, writes `datetime.now().isoformat(timespec="seconds") + " - {label}: {elapsed:.6f}s"`), `__repr__` with label/elapsed/running, plus helpers `format_elapsed`/`log_message`/`log_elapsed`/`read_logs`/`clear_logs`.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy` clean, `pytest` green for every public function in `src/timer_logger/timer.py` (excl. `cli.py` per ARCHITECTURE.md §5) using `unittest.mock.patch` for `time.perf_counter` and `tmp_path` for file logging, `argparse` CLI with `--label`/`--log`/`--sleep`, `python -m timer_logger` entry point.

## API

```python
from timer_logger import Timer, format_elapsed, log_message, log_elapsed, read_logs, clear_logs
from pathlib import Path

Timer(label: str | None = None, log_file: str | Path | None = None)
# methods: start() -> None, stop() -> float, reset() -> None
# properties: elapsed -> float (also callable), is_running -> bool
# context: with Timer(...) as t: ...
# raises RuntimeError if start twice or stop without start
# auto-logs on stop/__exit__ if log_file set

format_elapsed(seconds: float) -> str
# "0.000s" | "1m 2.345s" | "1h 2m 3.456s"
# raises ValueError if negative or non-finite

log_message(message: str, log_file: str | Path) -> None
# appends "timestamp - message", creates parents
# raises IsADirectoryError if path is dir, ValueError if message not str

log_elapsed(label: str, seconds: float, log_file: str | Path) -> None
# like log_message but formats "label: X.XXXs"

read_logs(log_file: str | Path) -> list[str]
# [] if missing, raises IsADirectoryError if dir

clear_logs(log_file: str | Path) -> None
# truncates to "", creates file+parents if missing
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## ZuroKing's note

> Timing is the first place you feel that "now" is not a clock on the wall but a counter you can mock. Keep `perf_counter` inside `Timer` and nothing else knows time exists — that's why `patch("timer_logger.timer.time.perf_counter")` tests your whole flow with zero sleep. Do logging as plain text append, not a framework: `datetime.now().isoformat` + `Path.mkdir` + `open(..., "a")`. Then your Timer stays dumb — start, stop, maybe write one line — and the helpers `format_elapsed`/`log_message` become pure, testable with `tmp_path`. That split is the lesson: context manager is just `__enter__` start and `__exit__` stop.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
