"""Core logic for SQLite notes.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): every public function here has at least one test.
CLI parsing lives in cli.py and is intentionally excluded from that criterion.

Uses only stdlib (sqlite3, pathlib, dataclasses).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


@dataclass
class Note:
    """Single note stored in SQLite.

    Attributes:
        id: unique integer identifier (autoincrement).
        title: human-readable title (non-empty).
        content: note body (may be empty).
        created_at: timestamp string as stored by SQLite.
    """

    id: int
    title: str
    content: str
    created_at: str


def _row_to_note(row: tuple[Any, ...]) -> Note:
    """Convert a DB row tuple to :class:`Note`."""
    return Note(
        id=int(row[0]),
        title=str(row[1]),
        content=str(row[2]),
        created_at=str(row[3]),
    )


def create_db(db_path: str | Path) -> None:
    """Create SQLite database and ``notes`` table if not exists.

    Creates parent directories as needed. Idempotent — safe to call
    multiple times.

    Args:
        db_path: filesystem path to SQLite file.
    """
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(p)) as conn:
        conn.execute(_CREATE_TABLE_SQL)
        conn.commit()


def add_note(db_path: str | Path, title: str, content: str) -> int:
    """Add a new note to the database.

    Ensures table exists (calls :func:`create_db`).

    Args:
        db_path: path to SQLite file.
        title: note title, must be non-empty after stripping.
        content: note body, must be a string (may be empty).

    Returns:
        The newly created note id.

    Raises:
        ValueError: if title is not a string, content not a string,
            or title is empty/whitespace.
        RuntimeError: if insert fails to return row id.
    """
    if not isinstance(title, str):
        raise ValueError("title must be a string")
    if not isinstance(content, str):
        raise ValueError("content must be a string")
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValueError("title must not be empty")
    # content is kept as-is (empty allowed); no strip validation
    create_db(db_path)
    p = Path(db_path)
    with sqlite3.connect(str(p)) as conn:
        conn.execute(_CREATE_TABLE_SQL)
        cur: sqlite3.Cursor = conn.execute(
            "INSERT INTO notes (title, content) VALUES (?, ?)",
            (cleaned_title, content),
        )
        conn.commit()
        rowid: int | None = cur.lastrowid
        if rowid is None:
            raise RuntimeError("failed to insert note")
        return int(rowid)


def get_note(db_path: str | Path, note_id: int) -> Note | None:
    """Get a single note by id.

    Args:
        db_path: path to SQLite file.
        note_id: id of note to retrieve.

    Returns:
        :class:`Note` if found, else ``None``.

    Raises:
        ValueError: if note_id is not an integer.
    """
    if not isinstance(note_id, int):
        raise ValueError("note_id must be an integer")
    p = Path(db_path)
    if not p.exists():
        return None
    with sqlite3.connect(str(p)) as conn:
        conn.execute(_CREATE_TABLE_SQL)
        cur: sqlite3.Cursor = conn.execute(
            "SELECT id, title, content, created_at FROM notes WHERE id = ?",
            (note_id,),
        )
        fetched: Any = cur.fetchone()
        if fetched is None:
            return None
        row: tuple[Any, ...] = fetched
        return _row_to_note(row)


def list_notes(db_path: str | Path) -> list[Note]:
    """List all notes ordered by id.

    Args:
        db_path: path to SQLite file.

    Returns:
        List of notes, empty if none or DB does not exist.
    """
    p = Path(db_path)
    if not p.exists():
        return []
    with sqlite3.connect(str(p)) as conn:
        conn.execute(_CREATE_TABLE_SQL)
        cur: sqlite3.Cursor = conn.execute(
            "SELECT id, title, content, created_at FROM notes ORDER BY id"
        )
        rows: list[tuple[Any, ...]] = cur.fetchall()
        return [_row_to_note(r) for r in rows]


def update_note(
    db_path: str | Path,
    note_id: int,
    title: str | None = None,
    content: str | None = None,
) -> Note:
    """Update title and/or content of a note.

    At least one of ``title`` or ``content`` must be provided.

    Args:
        db_path: path to SQLite file.
        note_id: id of note to update.
        title: new title (if given, must be non-empty after stripping).
        content: new content (if given, must be a string).

    Returns:
        Updated :class:`Note`.

    Raises:
        ValueError: if note_id is not int, nothing to update,
            title/content validation fails, or note not found.
    """
    if not isinstance(note_id, int):
        raise ValueError("note_id must be an integer")
    if title is None and content is None:
        raise ValueError("nothing to update: provide title or content")
    if title is not None:
        if not isinstance(title, str):
            raise ValueError("title must be a string")
        if not title.strip():
            raise ValueError("title must not be empty")
    if content is not None and not isinstance(content, str):
        raise ValueError("content must be a string")

    p = Path(db_path)
    if not p.exists():
        raise ValueError(f"note with id {note_id} not found")

    with sqlite3.connect(str(p)) as conn:
        conn.execute(_CREATE_TABLE_SQL)
        # check existence
        cur: sqlite3.Cursor = conn.execute(
            "SELECT id, title, content, created_at FROM notes WHERE id = ?",
            (note_id,),
        )
        fetched: Any = cur.fetchone()
        if fetched is None:
            raise ValueError(f"note with id {note_id} not found")

        # build dynamic update
        fields: list[str] = []
        params: list[Any] = []
        if title is not None:
            fields.append("title = ?")
            params.append(title.strip())
        if content is not None:
            fields.append("content = ?")
            params.append(content)
        params.append(note_id)
        set_clause = ", ".join(fields)
        conn.execute(
            f"UPDATE notes SET {set_clause} WHERE id = ?", params
        )  # noqa: S608
        conn.commit()

        # fetch updated
        cur2: sqlite3.Cursor = conn.execute(
            "SELECT id, title, content, created_at FROM notes WHERE id = ?",
            (note_id,),
        )
        fetched2: Any = cur2.fetchone()
        if fetched2 is None:
            raise RuntimeError("failed to fetch updated note")
        row2: tuple[Any, ...] = fetched2
        return _row_to_note(row2)


def delete_note(db_path: str | Path, note_id: int) -> None:
    """Delete a note by id.

    Args:
        db_path: path to SQLite file.
        note_id: id of note to delete.

    Raises:
        ValueError: if note_id is not int or note not found.
    """
    if not isinstance(note_id, int):
        raise ValueError("note_id must be an integer")
    p = Path(db_path)
    if not p.exists():
        raise ValueError(f"note with id {note_id} not found")
    with sqlite3.connect(str(p)) as conn:
        conn.execute(_CREATE_TABLE_SQL)
        cur: sqlite3.Cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f"note with id {note_id} not found")


def search_notes(db_path: str | Path, query: str) -> list[Note]:
    """Search notes by substring in title or content (case-insensitive).

    Args:
        db_path: path to SQLite file.
        query: substring to search; empty/whitespace returns [].

    Returns:
        List of matching notes ordered by id.

    Raises:
        ValueError: if query is not a string.
    """
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    cleaned = query.strip()
    if not cleaned:
        return []
    p = Path(db_path)
    if not p.exists():
        return []
    pattern = f"%{cleaned}%"
    with sqlite3.connect(str(p)) as conn:
        conn.execute(_CREATE_TABLE_SQL)
        cur: sqlite3.Cursor = conn.execute(
            "SELECT id, title, content, created_at FROM notes "
            "WHERE title LIKE ? OR content LIKE ? ORDER BY id",
            (pattern, pattern),
        )
        rows: list[tuple[Any, ...]] = cur.fetchall()
        return [_row_to_note(r) for r in rows]
