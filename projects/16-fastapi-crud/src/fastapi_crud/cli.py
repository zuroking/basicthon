"""CLI layer for FastAPI CRUD.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
Uses ``uvicorn`` to serve :data:`fastapi_crud.app.app`.
"""

from __future__ import annotations

import argparse
import os
import sys


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="fastapi-crud",
        description="FastAPI CRUD (basicthon #16) — run dev server.",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="host to bind (or $HOST, default 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="port to bind (or $PORT, default 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="enable auto-reload (dev)",
    )
    return parser.parse_args(argv)


def _resolve_host(cli_host: str | None) -> str:
    if cli_host is not None and isinstance(cli_host, str) and cli_host.strip():
        return cli_host.strip()
    env_val = os.environ.get("HOST")
    if env_val is not None and env_val.strip():
        return env_val.strip()
    return "127.0.0.1"


def _resolve_port(cli_port: int | None) -> int:
    if cli_port is not None:
        if not isinstance(cli_port, int) or isinstance(cli_port, bool):
            print("error: --port must be an integer", file=sys.stderr)
            sys.exit(1)
        if cli_port < 1 or cli_port > 65535:
            print("error: --port must be 1..65535", file=sys.stderr)
            sys.exit(1)
        return cli_port
    env_val = os.environ.get("PORT")
    if env_val is not None and env_val.strip():
        try:
            p = int(env_val.strip())
        except ValueError:
            print("error: $PORT must be an integer", file=sys.stderr)
            sys.exit(1)
        if p < 1 or p > 65535:
            print("error: $PORT must be 1..65535", file=sys.stderr)
            sys.exit(1)
        return p
    return 8000


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m fastapi_crud``."""
    args = parse_args(argv)
    host = _resolve_host(getattr(args, "host", None))
    port = _resolve_port(getattr(args, "port", None))
    reload_flag: bool = bool(getattr(args, "reload", False))

    try:
        import uvicorn
    except ImportError:
        msg = "error: uvicorn not installed (pip install -r requirements.txt)"
        print(msg, file=sys.stderr)
        sys.exit(1)

    uvicorn.run("fastapi_crud.app:app", host=host, port=port, reload=reload_flag)
