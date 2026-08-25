"""CLI layer for SQLite notes.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
Uses :mod:`sqlite_notes.notes` for core logic.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlite_notes.notes import (
    add_note,
    create_db,
    delete_note,
    get_note,
    list_notes,
    search_notes,
    update_note,
)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="sqlite-notes",
        description="Notes on SQLite — simple CRUD with sqlite3 (basicthon #11).",
    )
    parser.add_argument(
        "--db",
        default="notes.db",
        help="path to SQLite file (default: notes.db)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a new note")
    p_add.add_argument("title", help="note title")
    p_add.add_argument("content", nargs="?", default="", help="note content")

    p_get = sub.add_parser("get", help="get note by id")
    p_get.add_argument("id", type=int, help="note id")

    sub.add_parser("list", help="list all notes")

    p_upd = sub.add_parser("update", help="update a note")
    p_upd.add_argument("id", type=int, help="note id")
    p_upd.add_argument("--title", default=None, help="new title")
    p_upd.add_argument("--content", default=None, help="new content")

    p_del = sub.add_parser("delete", help="delete a note")
    p_del.add_argument("id", type=int, help="note id")

    p_search = sub.add_parser("search", help="search notes by query")
    p_search.add_argument("query", help="search query")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m sqlite_notes``."""
    args = parse_args(argv)
    db_path = Path(args.db)

    # Ensure DB exists for read commands
    # (create if missing for list etc is handled in core)
    # but we explicitly ensure for user-facing commands.
    try:
        if args.command == "add":
            create_db(db_path)
            nid = add_note(db_path, args.title, args.content)
            print(f"added [{nid}] {args.title}")

        elif args.command == "get":
            note = get_note(db_path, args.id)
            if note is None:
                print(f"note {args.id} not found", file=sys.stderr)
                sys.exit(1)
            print(f"[{note.id}] {note.title} | {note.content} | {note.created_at}")

        elif args.command == "list":
            notes = list_notes(db_path)
            if not notes:
                print("no notes")
            else:
                for n in notes:
                    print(f"[{n.id}] {n.title} | {n.content} | {n.created_at}")

        elif args.command == "update":
            if args.title is None and args.content is None:
                print(
                    "nothing to update: provide --title or --content",
                    file=sys.stderr,
                )
                sys.exit(1)
            note = update_note(db_path, args.id, title=args.title, content=args.content)
            print(f"updated [{note.id}] {note.title}")

        elif args.command == "delete":
            delete_note(db_path, args.id)
            print(f"deleted [{args.id}]")

        elif args.command == "search":
            results = search_notes(db_path, args.query)
            if not results:
                print("no matches")
            else:
                for n in results:
                    print(f"[{n.id}] {n.title} | {n.content}")

    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except (OSError, Exception) as exc:  # pragma: no cover - safety net
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
