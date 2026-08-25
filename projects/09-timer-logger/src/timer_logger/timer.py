"""Core logic for timer logger.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): every public function here has at least one test.
CLI parsing lives in cli.py and is intentionally excluded from that criterion.

Uses only stdlib (time, datetime, pathlib).
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path


class _Elapsed(float):
    """Float subclass callable as ``t.elapsed()`` and ``t.elapsed``.

    Returning this from ``elapsed`` lets callers use either style
    without breaking type expectations (compares equal to plain float).
    """

    def __call__(self) -> float:  # type: ignore[override]
        return float(self)


class Timer:
    """Simple stopwatch with optional file logging and context-manager support.

    Example:
        >>> t = Timer(label="task")
        >>> t.start()
        >>> ...  # work
        >>> elapsed = t.stop()
        >>> t.elapsed  # or t.elapsed() — both work
        1.23

        >>> with Timer(label="block", log_file="timer.log") as t:
        ...     ...  # measured block
        >>> # automatically logs on exit if log_file was given
    """

    def __init__(
        self,
        label: str | None = None,
        log_file: str | Path | None = None,
    ) -> None:
        self.label: str | None = label
        self.log_file: Path | None = Path(log_file) if log_file is not None else None
        self._start_time: float | None = None
        self._elapsed: float = 0.0
        self._running: bool = False

    def start(self) -> None:
        """Start the timer.

        Raises:
            RuntimeError: if timer is already running.
        """
        if self._running:
            raise RuntimeError("Timer already running")
        self._start_time = time.perf_counter()
        self._running = True

    def stop(self) -> float:
        """Stop the timer and return elapsed seconds.

        If ``log_file`` was set at construction, appends a timestamped
        line to that file.

        Returns:
            Elapsed seconds as float.

        Raises:
            RuntimeError: if timer was not started or already stopped.
        """
        if not self._running or self._start_time is None:
            raise RuntimeError("Timer is not running")
        end = time.perf_counter()
        self._elapsed = end - self._start_time
        self._running = False
        self._start_time = None
        if self.log_file is not None:
            self._write_log(self._elapsed)
        return self._elapsed

    @property
    def elapsed(self) -> float:  # type: ignore[override]
        """Elapsed seconds.

        If running, returns current running time. If stopped, returns
        last measured interval. If never started, returns ``0.0``.

        Designed to support both ``t.elapsed`` and ``t.elapsed()``
        via :class:`_Elapsed`.
        """
        if self._running and self._start_time is not None:
            current = time.perf_counter() - self._start_time
            return _Elapsed(current)
        return _Elapsed(self._elapsed)

    @property
    def is_running(self) -> bool:
        """Whether the timer is currently running."""
        return self._running

    def reset(self) -> None:
        """Reset timer to initial state (0 elapsed, not running)."""
        self._start_time = None
        self._elapsed = 0.0
        self._running = False

    def __enter__(self) -> Timer:
        """Enter context manager and start timer."""
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Exit context manager, stop timer and log if needed."""
        if self._running:
            self.stop()
        # do not suppress exceptions
        return None

    def __repr__(self) -> str:
        return (
            f"Timer(label={self.label!r}, log_file={self.log_file!r}, "
            f"elapsed={float(self.elapsed):.6f}, running={self._running})"
        )

    def _write_log(self, elapsed: float) -> None:
        """Append a timestamped entry to ``self.log_file``."""
        if self.log_file is None:
            return
        timestamp = datetime.now().isoformat(timespec="seconds")
        label = self.label if self.label is not None else "Timer"
        line = f"{timestamp} - {label}: {elapsed:.6f}s\n"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(line)


def format_elapsed(seconds: float) -> str:
    """Format elapsed seconds as human readable string.

    Always shows three decimal places and ``s`` suffix.
    For values >= 60 uses ``Xm Y.ZZZs``, for >=3600 uses ``Xh Ym Z.ZZZs``.

    Args:
        seconds: elapsed seconds, must be >= 0.

    Returns:
        Formatted string like ``"1.234s"`` or ``"1m 2.345s"``.

    Raises:
        ValueError: if ``seconds`` is negative or not finite.
    """
    if not isinstance(seconds, (int, float)):
        raise ValueError("seconds must be a number")
    sec = float(seconds)
    if sec < 0 or sec != sec or sec == float("inf") or sec == float("-inf"):
        raise ValueError(f"seconds must be finite and >= 0, got {seconds!r}")
    if sec < 60:
        return f"{sec:.3f}s"
    if sec < 3600:
        minutes = int(sec // 60)
        remainder = sec - minutes * 60
        return f"{minutes}m {remainder:.3f}s"
    hours = int(sec // 3600)
    remainder = sec - hours * 3600
    minutes = int(remainder // 60)
    secs = remainder - minutes * 60
    return f"{hours}h {minutes}m {secs:.3f}s"


def log_message(message: str, log_file: str | Path) -> None:
    """Append a timestamped message to a log file.

    Creates parent directories as needed.

    Args:
        message: message to log.
        log_file: path to log file.

    Raises:
        ValueError: if ``message`` is not a string.
        IsADirectoryError: if ``log_file`` is a directory.
    """
    if not isinstance(message, str):
        raise ValueError("message must be a string")
    path = Path(log_file)
    if path.exists() and path.is_dir():
        raise IsADirectoryError(f"log_file is a directory: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")
    line = f"{timestamp} - {message}\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def log_elapsed(label: str, seconds: float, log_file: str | Path) -> None:
    """Log an elapsed time entry with label to file.

    This is a convenience wrapper around :func:`log_message`
    that formats ``label: X.XXXs``.

    Args:
        label: label for the entry.
        seconds: elapsed seconds, must be >= 0 and finite.
        log_file: path to log file.

    Raises:
        ValueError: if label is empty or seconds invalid.
        IsADirectoryError: if log_file is a directory.
    """
    if not isinstance(label, str) or not label.strip():
        raise ValueError("label must be a non-empty string")
    # validate seconds via format_elapsed (raises if bad)
    formatted = format_elapsed(seconds)
    message = f"{label}: {formatted}"
    log_message(message, log_file)


def read_logs(log_file: str | Path) -> list[str]:
    """Read log file and return lines without trailing newline.

    Args:
        log_file: path to log file.

    Returns:
        List of lines. Empty list if file does not exist.

    Raises:
        IsADirectoryError: if path is a directory.
    """
    path = Path(log_file)
    if not path.exists():
        return []
    if path.is_dir():
        raise IsADirectoryError(f"log_file is a directory: {path}")
    with path.open("r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]


def clear_logs(log_file: str | Path) -> None:
    """Clear log file contents (truncate to zero).

    Creates the file and parent directories if they do not exist.

    Args:
        log_file: path to log file.

    Raises:
        IsADirectoryError: if path is a directory.
    """
    path = Path(log_file)
    if path.exists() and path.is_dir():
        raise IsADirectoryError(f"log_file is a directory: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
