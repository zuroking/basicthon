"""CLI layer for secret manager.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
Uses :mod:`secret_manager.manager` for core logic.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from secret_manager.manager import (
    delete_secret,
    generate_key,
    get_secret,
    list_secrets,
    set_secret,
)


def _resolve_key(cli_key: str | None) -> str:
    """Resolve encryption key from CLI arg or environment.

    Raises:
        ValueError: if no key is available.
    """
    if cli_key is not None and cli_key.strip():
        return cli_key.strip()
    env_val = os.environ.get("SECRET_MANAGER_KEY")
    if env_val is not None and env_val.strip():
        return env_val.strip()
    raise ValueError(
        "missing encryption key: provide --key or set SECRET_MANAGER_KEY "
        "(see .env.example; generate with: secret-manager generate-key)"
    )


def _resolve_store(cli_store: str | None) -> Path:
    """Resolve store path from CLI or env or default."""
    if cli_store is not None and cli_store.strip():
        return Path(cli_store.strip())
    env_store = os.environ.get("SECRET_STORE_PATH")
    if env_store is not None and env_store.strip():
        return Path(env_store.strip())
    return Path("secrets.json")


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="secret-manager",
        description="Secret manager with Fernet (basicthon #12).",
    )
    parser.add_argument(
        "--store",
        default=None,
        help="path to JSON store file (default: ./secrets.json or $SECRET_STORE_PATH)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("generate-key", help="generate a new Fernet key")

    p_set = sub.add_parser("set", help="store a secret (encrypt)")
    p_set.add_argument("name", help="secret name")
    p_set.add_argument("value", help="secret value")
    p_set.add_argument(
        "--key", default=None, help="Fernet key (or $SECRET_MANAGER_KEY)"
    )

    p_get = sub.add_parser("get", help="retrieve a secret (decrypt)")
    p_get.add_argument("name", help="secret name")
    p_get.add_argument(
        "--key", default=None, help="Fernet key (or $SECRET_MANAGER_KEY)"
    )

    p_del = sub.add_parser("delete", help="delete a secret")
    p_del.add_argument("name", help="secret name")

    sub.add_parser("list", help="list secret names")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m secret_manager``."""
    args = parse_args(argv)
    store_path = _resolve_store(getattr(args, "store", None))

    try:
        command: str = getattr(args, "command")

        if command == "generate-key":
            print(generate_key())
            return

        if command == "set":
            key = _resolve_key(getattr(args, "key", None))
            set_secret(
                store_path, str(getattr(args, "name")), str(getattr(args, "value")), key
            )
            print(f"set [{getattr(args, 'name')}]")

        elif command == "get":
            key = _resolve_key(getattr(args, "key", None))
            value = get_secret(store_path, str(getattr(args, "name")), key)
            if value is None:
                print(f"secret not found: {getattr(args, 'name')}", file=sys.stderr)
                sys.exit(1)
            print(value)

        elif command == "delete":
            delete_secret(store_path, str(getattr(args, "name")))
            print(f"deleted [{getattr(args, 'name')}]")

        elif command == "list":
            names = list_secrets(store_path)
            if not names:
                print("no secrets")
            else:
                for n in names:
                    print(n)

        else:
            print(f"unknown command: {command}", file=sys.stderr)
            sys.exit(1)

    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except (OSError, Exception) as exc:  # pragma: no cover - safety net
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
