"""CLI layer for contacts OOP.

This file is intentionally CLI-only (argument parsing + I/O) and is excluded
from the coverage criterion "each public function outside cli.py/main.py"
(G-13). It is still type-annotated per project standards.
Uses :mod:`contacts.contact` for core logic.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from contacts.contact import Contact, ContactBook


def _load_book(path: Path) -> ContactBook:
    """Load ContactBook from JSON file."""
    book = ContactBook()
    if not path.exists():
        return book
    if path.stat().st_size == 0:
        return book
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {path}: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, list):
        print(f"error: {path} must contain JSON array", file=sys.stderr)
        sys.exit(1)
    for entry in data:
        if not isinstance(entry, dict):
            continue
        try:
            contact = Contact.from_dict(entry)  # type: ignore[arg-type]
            try:
                book.add(contact)
            except ValueError:
                # skip duplicates in file
                continue
        except ValueError as exc:
            print(f"warning: skipping invalid entry {entry}: {exc}", file=sys.stderr)
            continue
    return book


def _save_book(path: Path, book: ContactBook) -> None:
    """Save ContactBook to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [c.to_dict() for c in book.list_contacts()]
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="contacts",
        description="Contacts book — OOP (basicthon #06)",
    )
    parser.add_argument(
        "--file",
        default="contacts.json",
        help="path to JSON file (default contacts.json)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a contact")
    p_add.add_argument("name", help="contact name")
    p_add.add_argument("phone", help="phone number")
    p_add.add_argument("email", help="email address")

    p_get = sub.add_parser("get", help="get contact by name")
    p_get.add_argument("name", help="contact name")

    p_update = sub.add_parser("update", help="update contact")
    p_update.add_argument("name", help="contact name")
    p_update.add_argument("--phone", help="new phone")
    p_update.add_argument("--email", help="new email")

    p_delete = sub.add_parser("delete", help="delete contact")
    p_delete.add_argument("name", help="contact name")

    p_search = sub.add_parser("search", help="search contacts")
    p_search.add_argument("query", help="search query")

    sub.add_parser("list", help="list all contacts")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m contacts``."""
    args = parse_args(argv)
    path = Path(args.file)
    book = _load_book(path)

    if args.command == "add":
        try:
            contact = Contact(args.name, args.phone, args.email)
            book.add(contact)
            _save_book(path, book)
            print(f"added {contact.name}")
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "get":
        try:
            found = book.get(args.name)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        if found is None:
            print(f"not found: {args.name}", file=sys.stderr)
            sys.exit(1)
        print(f"{found.name} | {found.phone} | {found.email}")

    elif args.command == "update":
        if args.phone is None and args.email is None:
            print("error: provide --phone or --email", file=sys.stderr)
            sys.exit(1)
        try:
            contact = book.update(args.name, phone=args.phone, email=args.email)
            _save_book(path, book)
            print(f"updated {contact.name}")
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "delete":
        try:
            book.delete(args.name)
            _save_book(path, book)
            print(f"deleted {args.name}")
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "search":
        try:
            results = book.search(args.query)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        if not results:
            print("no matches")
        else:
            for c in results:
                print(f"{c.name} | {c.phone} | {c.email}")

    elif args.command == "list":
        contacts = book.list_contacts()
        if not contacts:
            print("no contacts")
        else:
            for c in contacts:
                print(f"{c.name} | {c.phone} | {c.email}")


if __name__ == "__main__":
    main()
