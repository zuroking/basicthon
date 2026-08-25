"""CLI layer for duplicate finder.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
Uses :mod:`duplicate_finder.finder` for core logic.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from duplicate_finder.finder import find_duplicates


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="duplicate-finder",
        description=(
            "Find duplicate files by content hash (basicthon #08). "
            "Groups files with identical SHA-256 hashes."
        ),
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="directory to scan for duplicates (default: current directory)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="disable recursive scan (only top-level files)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m duplicate_finder``."""
    args = parse_args(argv)
    directory = Path(args.directory)
    recursive = not args.no_recursive

    try:
        duplicates = find_duplicates(directory, recursive=recursive)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except NotADirectoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except IsADirectoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not duplicates:
        print("no duplicates found")
        return

    total_groups = len(duplicates)
    total_files = sum(len(paths) for paths in duplicates.values())

    for file_hash in sorted(duplicates):
        paths = duplicates[file_hash]
        print(f"hash {file_hash}:")
        for path in paths:
            print(f"  {path}")

    print(f"found {total_groups} duplicate group(s), {total_files} file(s) total")
