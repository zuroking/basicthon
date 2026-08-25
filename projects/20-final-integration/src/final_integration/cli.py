"""CLI layer — adapted from project 04 (todo-cli) pattern.

Subcommands operate on the SQLite store directly; ``serve`` starts
uvicorn. CLI-only file excluded from coverage per G-13.
"""

from __future__ import annotations

import argparse
import sys


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="final-integration",
        description="Task tracker: CLI + SQLite + REST API (basicthon #20).",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("add", help="add a task")
    add_p = sub.add_parser("list", help="list tasks")
    add_p.add_argument("--all", action="store_true", help="show done too")
    get_p = sub.add_parser("get", help="show one task")
    get_p.add_argument("task_id", type=int)
    done_p = sub.add_parser("done", help="mark task completed")
    done_p.add_argument("task_id", type=int)
    del_p = sub.add_parser("delete", help="delete a task")
    del_p.add_argument("task_id", type=int)
    serve_p = sub.add_parser("serve", help="start REST API server")
    serve_p.add_argument("--host", default=None)
    serve_p.add_argument("--port", type=int, default=None)
    return parser.parse_args(argv)


def _print_task(task: object) -> None:
    """Print one Task in a friendly line."""
    from final_integration.storage import Task

    if isinstance(task, Task):
        mark = "x" if task.completed else " "
        print(f"[{mark}] #{task.id} {task.title}  ({task.created_at})")


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m final_integration``."""
    from final_integration import storage

    args = parse_args(argv)
    db = storage.get_db_path()

    if args.command == "add":
        title = (
            input("title> ").strip()
            if sys.stdin.isatty()
            else sys.stdin.readline().strip()
        )
        if not title:
            print("error: empty title", file=sys.stderr)
            sys.exit(1)
        new_id = storage.add_task(db, title)
        print(f"added #{new_id}")
    elif args.command == "list":
        tasks = storage.list_tasks(db)
        visible = (
            tasks
            if getattr(args, "all", False)
            else [t for t in tasks if not t.completed]
        )
        if not visible:
            print("(no tasks)")
        for t in visible:
            _print_task(t)
    elif args.command == "get":
        task = storage.get_task(db, args.task_id)
        if task is None:
            print("not found", file=sys.stderr)
            sys.exit(1)
        _print_task(task)
    elif args.command == "done":
        ok = storage.complete_task(db, args.task_id)
        print("done" if ok else "not found")
        sys.exit(0 if ok else 1)
    elif args.command == "delete":
        ok = storage.delete_task(db, args.task_id)
        print("deleted" if ok else "not found")
        sys.exit(0 if ok else 1)
    elif args.command == "serve":
        try:
            import uvicorn
        except ImportError:
            msg = "error: uvicorn not installed (pip install -r requirements.txt)"
            print(msg, file=sys.stderr)
            sys.exit(1)
        from final_integration.api import get_host, get_port

        host: str = getattr(args, "host", None) or get_host()
        cli_port = getattr(args, "port", None)
        port: int = (
            cli_port
            if isinstance(cli_port, int) and not isinstance(cli_port, bool)
            else get_port()
        )
        uvicorn.run("final_integration.api:app", host=host, port=port)
    else:
        print(
            "usage: final-integration {add|list|get|done|delete|serve}",
            file=sys.stderr,
        )
        sys.exit(2)
