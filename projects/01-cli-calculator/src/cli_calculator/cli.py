"""CLI layer for the calculator.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
"""

from __future__ import annotations

import argparse
import sys

from cli_calculator.calculator import evaluate


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="calc",
        description="CLI-калькулятор — безопасно вычисляет арифметические выражения",
    )
    parser.add_argument(
        "expression",
        nargs="?",
        default=None,
        help=(
            'выражение, например "2 + 3 * (4 - 1)"'
            " (если не указано — запускается REPL)"
        ),
    )
    parser.add_argument(
        "--expr",
        dest="expr_opt",
        default=None,
        help="альтернативный способ передать выражение (совместимость)",
    )
    return parser.parse_args(argv)


def run_expression(expr: str) -> int:
    """Evaluate one expression and print the result.

    Returns exit code (0 on success, 1 on error).
    """
    try:
        result = evaluate(expr)
        # Pretty-print: 3.0 -> 3 if integer-like
        if result.is_integer():
            print(int(result))
        else:
            print(result)
        return 0
    except ZeroDivisionError as exc:
        print(f"ошибка: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"ошибка: {exc}", file=sys.stderr)
        return 1


def repl() -> None:
    """Simple REPL loop."""
    print("Калькулятор (введите выражение, 'exit' для выхода)")
    while True:
        try:
            line = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.lower() in {"exit", "quit", "q"}:
            break
        if not line:
            continue
        run_expression(line)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and `python -m cli_calculator`."""
    args = parse_args(argv)
    expr = args.expr_opt if args.expr_opt is not None else args.expression
    if expr is None:
        repl()
    else:
        code = run_expression(expr)
        if code != 0:
            sys.exit(code)


if __name__ == "__main__":
    main()
