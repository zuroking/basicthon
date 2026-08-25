"""CLI layer for Markov chain text generator.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
Uses :mod:`markov_generator.markov` for core logic.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from markov_generator.markov import build_chain, generate


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="markov-generator",
        description="Markov chain text generator (basicthon #15).",
    )
    parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="source text (or use --file)",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="path to text file (overrides positional text if given)",
    )
    parser.add_argument(
        "--order",
        type=int,
        default=1,
        help="Markov order, 1..5 (default: 1)",
    )
    parser.add_argument(
        "--length",
        type=int,
        default=20,
        help="number of words to generate, 1..1000 (default: 20)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="random seed for deterministic output",
    )
    parser.add_argument(
        "--start",
        default=None,
        help="starting words, space-separated, must match order",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m markov_generator``."""
    args = parse_args(argv)

    order: int = int(getattr(args, "order"))
    length: int = int(getattr(args, "length"))
    seed: int | None = getattr(args, "seed")
    file_arg: str | None = getattr(args, "file")
    text_arg: str | None = getattr(args, "text")
    start_arg: str | None = getattr(args, "start")

    text: str | None = None
    if file_arg is not None:
        try:
            text = Path(str(file_arg)).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot read file: {exc}", file=sys.stderr)
            sys.exit(1)
    elif text_arg is not None:
        text = str(text_arg)
    else:
        print("error: provide text argument or --file", file=sys.stderr)
        sys.exit(1)

    assert text is not None

    if not text.strip():
        print("error: text must not be empty", file=sys.stderr)
        sys.exit(1)

    start: tuple[str, ...] | None = None
    if start_arg is not None:
        cleaned = str(start_arg).strip()
        if cleaned:
            start = tuple(cleaned.split())
        else:
            print("error: --start must not be empty", file=sys.stderr)
            sys.exit(1)

    try:
        chain = build_chain(text, order=order)
        if not chain:
            print("error: not enough words to build chain", file=sys.stderr)
            sys.exit(1)
        output = generate(chain, length=length, seed=seed, start=start)
        print(output)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - safety net
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
