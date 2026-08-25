"""CLI layer for mini test framework.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
Uses :mod:`mini_test.framework` for core logic.
"""

from __future__ import annotations

import argparse
import sys

from mini_test.framework import format_results, get_demo_suite, run_tests


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="mini-test",
        description=(
            "Mini test framework (basicthon #10). "
            "Runs the built-in demo suite using the tiny framework."
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="show PASS/FAIL per test instead of dots",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list demo test names and exit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m mini_test``."""
    args = parse_args(argv)

    suite = get_demo_suite()

    if args.list:
        for name in suite:
            print(name)
        return

    results = run_tests(suite)
    output = format_results(results, verbose=args.verbose)
    print(output)

    # exit 1 if any failure, 0 otherwise
    failed = sum(1 for r in results if not r.passed)
    if failed:
        sys.exit(1)
