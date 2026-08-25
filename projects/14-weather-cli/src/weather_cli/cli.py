"""CLI layer for weather CLI.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
Uses :mod:`weather_cli.weather` for core logic.
"""

from __future__ import annotations

import argparse
import os
import sys

from weather_cli.weather import fetch_weather


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
        prog="weather-cli",
        description="Weather CLI with retry (basicthon #14).",
    )
    parser.add_argument("city", help="city name, e.g. London or 'New York'")
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
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="max retries on retryable errors (default: 3)",
    )
    parser.add_argument(
        "--backoff",
        type=float,
        default=0.5,
        help="backoff factor in seconds (default: 0.5)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m weather_cli``."""
    args = parse_args(argv)

    city: str = str(getattr(args, "city"))
    api_key = _resolve_api_key(getattr(args, "api_key", None))
    api_url = _resolve_api_url(getattr(args, "api_url", None))
    retries: int = int(getattr(args, "retries"))
    backoff: float = float(getattr(args, "backoff"))

    try:
        data = fetch_weather(
            city,
            api_key=api_key,
            api_url=api_url,
            max_retries=retries,
            backoff_factor=backoff,
        )
        city_out = data.get("city", city)
        temp = data.get("temperature", "?")
        desc = data.get("description", "?")
        hum = data.get("humidity")
        if hum is not None:
            print(f"{city_out}: {temp}°C, {desc}, humidity {hum}%")
        else:
            print(f"{city_out}: {temp}°C, {desc}")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - safety net
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
