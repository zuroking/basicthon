"""CLI layer for password generator.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
"""

from __future__ import annotations

import argparse
import sys

from password_generator.generator import generate_password


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="passgen",
        description="Генератор паролей — создаёт случайный пароль с помощью secrets",
    )
    parser.add_argument(
        "--length",
        type=int,
        default=12,
        help="длина пароля (по умолчанию 12, минимум 4)",
    )
    parser.add_argument(
        "--no-upper",
        action="store_true",
        help="исключить заглавные буквы",
    )
    parser.add_argument(
        "--no-digits",
        action="store_true",
        help="исключить цифры",
    )
    parser.add_argument(
        "--symbols",
        action="store_true",
        help="включить символы (string.punctuation)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m password_generator``."""
    args = parse_args(argv)

    try:
        password = generate_password(
            length=args.length,
            use_upper=not args.no_upper,
            use_digits=not args.no_digits,
            use_symbols=args.symbols,
        )
    except ValueError as exc:
        print(f"ошибка: {exc}", file=sys.stderr)
        sys.exit(1)

    print(password)


if __name__ == "__main__":
    main()
