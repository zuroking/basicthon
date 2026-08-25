"""SQLite storage layer — adapted from project 11 (sqlite-notes).

This is a copy-paste adaptation per G-08 / GRILL2-08 (snapshot, not an
import): the ``notes`` table became ``tasks`` with a ``completed``
column. CLI parsing lives in ``cli.py`` and is excluded from coverage.

Uses only stdlib (sqlite3, pathlib, dataclasses).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


@dataclass
class Task:
    """Single task stored in SQLite.

    Attributes:
        id: unique integer identifier (autoincrement).
        title: human-readable title (non-empty).
        completed: done flag.
        created_at: timestamp string as stored by SQLite.
    """

    id: int
    title: str
    completed: bool
    created_at: str


def _row_to_task(row: tuple[Any, ...]) -> Task:
    """Convert a DB row tuple to :class:`Task`."""
    return Task(
        id=int(row[0]),
        title=str(row[1]),
        completed=bool(int(row[2])),
        created_at=str(row[3]),
    )


def get_db_path(var_name: str = "DATABASE_PATH") -> str:
    """Return database path from environment.

    Args:
        var_name: env variable name. Defaults to ``DATABASE_PATH``.

    Returns:
        Path string; default ``./tasks.db``.

    Raises:
        ValueError: if ``var_name`` invalid.
    """
    import os

    if not isinstance(var_name, str):
        raise ValueError("var_name must be a string")
    cleaned = var_name.strip()
    if not cleaned:
        raise ValueError("var_name must be a non-empty string")
    value = os.environ.get(cleaned)
    if value is None or not value.strip():
        return "./tasks.db"
    return value.strip()


def create_db(db_path: str | Path) -> None:
    """Create SQLite database and ``tasks`` table if not exists.

    Idempotent — safe to call multiple times.

    Args:
        db_path: filesystem path to SQLite file.
    """
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(p)) as conn:
        conn.execute(_CREATE_TABLE_SQL)
        conn.commit()


def add_task(db_path: str | Path, title: str) -> int:
    """Add a new task.

    Args:
        db_path: path to SQLite file.
        title: task title, must be non-empty after stripping.

    Returns:
        The newly created task id.

    Raises:
        ValueError: if title is invalid or insert fails to return id.
    """
    if not isinstance(title, str):
        raise ValueError("title must be a string")
    cleaned = title.strip()
    if not cleaned:
        raise ValueError("title must not be empty")
    if len(cleaned) > 100:
        raise ValueError("title must be at most 100 chars")
    create_db(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(_CREATE_TABLE_SQL)
        cur: sqlite3.Cursor = conn.execute(
            "INSERT INTO tasks (title) VALUES (?)", (cleaned,)
        )
        conn.commit()
        rowid: int | None = cur.lastrowid
        if rowid is None:
            raise RuntimeError("insert did not return row id")
        return rowid


def list_tasks(db_path: str | Path) -> list[Task]:
    """Return all tasks ordered by id ascending.

    Args:
        db_path: path to SQLite file.

    Returns:
        List of :class:`Task` (empty when no table content).
    """
    create_db(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.execute(
            "SELECT id, title, completed, created_at FROM tasks ORDER BY id"
        )
        rows: list[tuple[Any, ...]] = cur.fetchall()
    return [_row_to_task(r) for r in rows]


def get_task(db_path: str | Path, task_id: int) -> Task | None:
    """Get one task by id.

    Args:
        db_path: path to SQLite file.
        task_id: id to look up; bool rejected.

    Returns:
        Task or None when missing.

    Raises:
        ValueError: on invalid args.
    """
    if isinstance(task_id, bool) or not isinstance(task_id, int):
        raise ValueError("task_id must be an integer")
    create_db(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.execute(
            "SELECT id, title, completed, created_at FROM tasks WHERE id = ?",
            (task_id,),
        )
        row: tuple[Any, ...] | None = cur.fetchone()
    return _row_to_task(row) if row is not None else None


def complete_task(db_path: str | Path, task_id: int) -> bool:
    """Mark a task as completed.

    Args:
        db_path: path to SQLite file.
        task_id: id of task to mark done.

    Returns:
        True if updated, False when task missing.

    Raises:
        ValueError: on invalid args.
    """
    if isinstance(task_id, bool) or not isinstance(task_id, int):
        raise ValueError("task_id must be an integer")
    create_db(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
        conn.commit()
        return cur.rowcount > 0


def delete_task(db_path: str | Path, task_id: int) -> bool:
    """Delete a task by id.

    Args:
        db_path: path to SQLite file.
        task_id: id of task to remove.

    Returns:
        True if deleted, False when missing.

    Raises:
        ValueError: on invalid args.
    """
    if isinstance(task_id, bool) or not isinstance(task_id, int):
        raise ValueError("task_id must be an integer")
    create_db(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cur.rowcount > 0
