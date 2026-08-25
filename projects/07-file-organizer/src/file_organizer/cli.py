"""CLI layer for file organizer.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
Uses :mod:`file_organizer.organizer` for core logic.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from file_organizer.organizer import organize


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="file-organizer",
        description=(
            "File organizer — categorize files by extension and move them "
            "into subfolders (basicthon #07)"
        ),
    )
    parser.add_argument(
        "source",
        help="source directory whose files will be organized",
    )
    parser.add_argument(
        "dest",
        nargs="?",
        default=None,
        help="destination directory (default: same as source, organize in-place)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show what would be done without moving files",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m file_organizer``."""
    args = parse_args(argv)
    src = Path(args.source)
    dst = Path(args.dest) if args.dest is not None else src

    try:
        result = organize(src, dst, dry_run=args.dry_run)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except NotADirectoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not result:
        print("no files to organize")
        return

    total = sum(len(files) for files in result.values())
    for category in sorted(result):
        for filename in sorted(result[category]):
            if args.dry_run:
                print(f"[dry-run] {filename} -> {category}/")
            else:
                print(f"{filename} -> {category}/")

    if args.dry_run:
        print(f"dry-run: {total} file(s) would be organized")
    else:
        print(f"organized {total} file(s) into {len(result)} categor(ies)")
