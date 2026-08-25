"""CLI layer for currency converter.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
Uses :mod:`currency_converter.converter` for core logic.
"""

from __future__ import annotations

import argparse
import os
import sys

from currency_converter.converter import convert


def _resolve_api_key(cli_key: str | None) -> str | None:
    """Resolve API key from CLI arg or environment.

    Returns None if not provided anywhere — core will raise with clear msg.
    """
    if cli_key is not None and isinstance(cli_key, str) and cli_key.strip():
        return cli_key.strip()
    env_val = os.environ.get("API_KEY")
    if env_val is not None and env_val.strip():
        return env_val.strip()
    return None


def _resolve_api_url(cli_url: str | None) -> str | None:
    """Resolve API URL from CLI arg or environment."""
    if cli_url is not None and isinstance(cli_url, str) and cli_url.strip():
        return cli_url.strip()
    env_val = os.environ.get("API_URL")
    if env_val is not None and env_val.strip():
        return env_val.strip()
    return None


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="currency-converter",
        description="Currency converter via exchange rates API (basicthon #13).",
    )
    parser.add_argument("amount", help="amount to convert, e.g. 100 or 12.5")
    parser.add_argument(
        "from_currency", help="source currency code, e.g. USD (3 letters)"
    )
    parser.add_argument(
        "to_currency", help="target currency code, e.g. EUR (3 letters)"
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key (or $API_KEY, see .env.example)",
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help="API URL (or $API_URL, see .env.example)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m currency_converter``."""
    args = parse_args(argv)

    # Validate and parse amount early for clear error
    raw_amount: str = str(getattr(args, "amount"))
    try:
        # allow int and float strings
        if "." in raw_amount or "e" in raw_amount.lower():
            amount_val: float | int = float(raw_amount)
        else:
            # try int first, fallback to float
            try:
                amount_val = int(raw_amount)
            except ValueError:
                amount_val = float(raw_amount)
    except ValueError:
        print(f"error: invalid amount: {raw_amount!r}", file=sys.stderr)
        sys.exit(1)

    from_cur: str = str(getattr(args, "from_currency"))
    to_cur: str = str(getattr(args, "to_currency"))
    api_key = _resolve_api_key(getattr(args, "api_key", None))
    api_url = _resolve_api_url(getattr(args, "api_url", None))

    try:
        result = convert(amount_val, from_cur, to_cur, api_key=api_key, api_url=api_url)
        src = from_cur.strip().upper()
        dst = to_cur.strip().upper()
        print(f"{float(amount_val)} {src} = {result} {dst}")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - safety net
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
