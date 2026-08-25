"""CLI layer for To-do with JSON persistence.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
Uses :mod:`json` for persistence via :mod:`todo_cli.todo`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from todo_cli.todo import (
    add_todo,
    complete_todo,
    delete_todo,
    list_todos,
    load_todos,
    save_todos,
)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="todo",
        description="To-do CLI с JSON-персистентностью",
    )
    parser.add_argument(
        "--file",
        default="todos.json",
        help="путь к JSON-файлу (по умолчанию todos.json)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="добавить задачу")
    p_add.add_argument("title", nargs="+", help="название задачи")

    p_list = sub.add_parser("list", help="показать задачи")
    p_list.add_argument(
        "--all",
        action="store_true",
        help="показать все задачи (по умолчанию — только невыполненные)",
    )
    p_list.add_argument(
        "--json",
        action="store_true",
        help="вывести как JSON",
    )

    p_done = sub.add_parser("done", help="отметить задачу выполненной")
    p_done.add_argument("id", type=int, help="id задачи")

    p_delete = sub.add_parser("delete", help="удалить задачу")
    p_delete.add_argument("id", type=int, help="id задачи")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m todo_cli``."""
    args = parse_args(argv)
    path = Path(args.file)

    try:
        items = load_todos(path)
    except (OSError, ValueError) as exc:
        print(f"ошибка загрузки: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.command == "add":
        title = " ".join(args.title)
        try:
            item = add_todo(items, title)
            save_todos(path, items)
            print(f"added [{item.id}] {item.title}")
        except ValueError as exc:
            print(f"ошибка: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "list":
        if args.all:
            to_show = list_todos(items)
        else:
            to_show = list_todos(items, completed=False)

        if args.json:
            data = [
                {"id": it.id, "title": it.title, "completed": it.completed}
                for it in to_show
            ]
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            if not to_show:
                print("no todos")
            else:
                for it in to_show:
                    status = "x" if it.completed else " "
                    print(f"[{it.id}] [{status}] {it.title}")

    elif args.command == "done":
        try:
            item = complete_todo(items, args.id)
            save_todos(path, items)
            print(f"completed [{item.id}] {item.title}")
        except ValueError as exc:
            print(f"ошибка: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "delete":
        try:
            delete_todo(items, args.id)
            save_todos(path, items)
            print(f"deleted [{args.id}]")
        except ValueError as exc:
            print(f"ошибка: {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
