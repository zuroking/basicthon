"""CLI layer for grades analyzer.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
Uses :mod:`grades_analyzer.analyzer` for core logic.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from grades_analyzer.analyzer import (
    average,
    grade_distribution,
    max_grade,
    median,
    min_grade,
    parse_csv,
    top_n,
)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="grades-analyzer",
        description="Analyze grades from CSV (columns: name, grade)",
    )
    parser.add_argument(
        "csv",
        help="path to CSV file with header containing 'name' and 'grade'",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="number of top students to show (default 3)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m grades_analyzer``."""
    args = parse_args(argv)
    path = Path(args.csv)

    try:
        records = parse_csv(path)
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"error parsing CSV: {exc}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"error reading file: {exc}", file=sys.stderr)
        sys.exit(1)

    if not records:
        print("no records found")
        return

    try:
        avg = average(records)
        med = median(records)
        mn = min_grade(records)
        mx = max_grade(records)
        dist = grade_distribution(records)
        top = top_n(records, n=args.top)
    except ValueError as exc:
        print(f"error computing stats: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"records: {len(records)}")
    print(f"average: {avg:.2f}")
    print(f"median: {med:.2f}")
    print(f"min: {mn:.2f}  max: {mx:.2f}")
    print("distribution:")
    for letter in ["A", "B", "C", "D", "F"]:
        print(f"  {letter}: {dist[letter]}")
    print(f"top {args.top}:")
    for rec in top:
        name = rec.get("name") or rec.get("student") or rec.get("Name") or "?"
        print(f"  {name} - {rec['grade']}")


if __name__ == "__main__":
    main()
