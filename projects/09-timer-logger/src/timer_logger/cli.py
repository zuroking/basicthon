"""CLI layer for timer logger.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
Uses :mod:`timer_logger.timer` for core logic.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from timer_logger.timer import Timer, format_elapsed


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="timer-logger",
        description=(
            "Timer/stopwatch with file logging (basicthon #09). "
            "Measures elapsed time and optionally logs to a file."
        ),
    )
    parser.add_argument(
        "--label",
        "-n",
        default="Timer",
        help="label for timing (default: Timer)",
    )
    parser.add_argument(
        "--log",
        "-l",
        dest="log_file",
        default=None,
        help="path to log file (if set, elapsed time is appended)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.1,
        help="seconds to sleep as demo work (default: 0.1)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m timer_logger``."""
    args = parse_args(argv)

    if args.sleep < 0:
        print("error: --sleep must be >= 0", file=sys.stderr)
        sys.exit(1)
    if (
        args.sleep != args.sleep
        or args.sleep == float("inf")
        or args.sleep == float("-inf")
    ):
        print("error: --sleep must be finite", file=sys.stderr)
        sys.exit(1)

    log_path = Path(args.log_file) if args.log_file is not None else None
    timer = Timer(label=args.label, log_file=log_path)

    # Use context manager to ensure stop + logging even if sleep interrupted.
    try:
        with timer:
            time.sleep(args.sleep)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        sys.exit(130)

    # After context, elapsed is available via property or method.
    elapsed_val = float(timer.elapsed)  # supports _Elapsed
    formatted = format_elapsed(elapsed_val)
    print(f"{args.label}: {formatted}")
    if log_path is not None:
        print(f"logged to {log_path}")
