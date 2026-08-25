"""Core logic for To-do CLI with JSON persistence.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): every public function here has at least one test.
CLI parsing lives in cli.py and is intentionally excluded from that criterion.

Persistence is JSON-based: a list of dicts with ``id``, ``title``, ``completed``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class TodoItem:
    """Single to-do item.

    Attributes:
        id: unique integer identifier (incremental, 1-based).
        title: human-readable task title.
        completed: whether task is done.
    """

    id: int
    title: str
    completed: bool = False


def load_todos(path: str | Path) -> list[TodoItem]:
    """Load todos from JSON file.

    If file does not exist or is empty, returns empty list.
    Expects JSON array of objects with ``id``, ``title``, ``completed``.

    Args:
        path: filesystem path to JSON file.

    Returns:
        List of :class:`TodoItem` objects.

    Raises:
        ValueError: if file contains invalid JSON structure.
    """
    p = Path(path)
    if not p.exists():
        return []
    if p.stat().st_size == 0:
        return []
    with p.open("r", encoding="utf-8") as f:
        data: Any = json.load(f)
    if not isinstance(data, list):
        raise ValueError("todos file must contain a JSON array")
    items: list[TodoItem] = []
    for entry in data:
        if not isinstance(entry, dict):
            raise ValueError("each todo entry must be an object")
        try:
            tid = int(entry["id"])
            title = str(entry["title"])
            completed = bool(entry.get("completed", False))
        except KeyError as exc:
            raise ValueError(f"missing field in todo entry: {exc}") from exc
        items.append(TodoItem(id=tid, title=title, completed=completed))
    return items


def save_todos(path: str | Path, items: list[TodoItem]) -> None:
    """Save todos to JSON file.

    Creates parent directories if needed. Writes pretty-printed JSON
    with ``ensure_ascii=False`` to keep unicode titles readable.

    Args:
        path: filesystem path to JSON file.
        items: list of todos to persist.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = [asdict(item) for item in items]
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def add_todo(items: list[TodoItem], title: str) -> TodoItem:
    """Add a new todo to the list.

    Generates next id as ``max(existing ids) + 1`` or ``1`` if empty.
    Mutates ``items`` in place and returns the created item.

    Args:
        items: current todo list (mutated).
        title: task title, must be non-empty after stripping.

    Returns:
        The newly created :class:`TodoItem`.

    Raises:
        ValueError: if title is not a string or is empty/whitespace.
    """
    if not isinstance(title, str):
        raise ValueError("title must be a string")
    cleaned = title.strip()
    if not cleaned:
        raise ValueError("title must not be empty")
    next_id = max((item.id for item in items), default=0) + 1
    new_item = TodoItem(id=next_id, title=cleaned, completed=False)
    items.append(new_item)
    return new_item


def complete_todo(items: list[TodoItem], todo_id: int) -> TodoItem:
    """Mark todo as completed.

    Args:
        items: current todo list.
        todo_id: id of todo to complete.

    Returns:
        The updated :class:`TodoItem`.

    Raises:
        ValueError: if todo_id is not int or not found.
    """
    if not isinstance(todo_id, int):
        raise ValueError("todo_id must be an integer")
    for item in items:
        if item.id == todo_id:
            item.completed = True
            return item
    raise ValueError(f"todo with id {todo_id} not found")


def delete_todo(items: list[TodoItem], todo_id: int) -> None:
    """Delete todo by id.

    Mutates ``items`` in place.

    Args:
        items: current todo list.
        todo_id: id of todo to delete.

    Raises:
        ValueError: if todo_id is not int or not found.
    """
    if not isinstance(todo_id, int):
        raise ValueError("todo_id must be an integer")
    for idx, item in enumerate(items):
        if item.id == todo_id:
            del items[idx]
            return
    raise ValueError(f"todo with id {todo_id} not found")


def list_todos(
    items: list[TodoItem], *, completed: bool | None = None
) -> list[TodoItem]:
    """List todos, optionally filtered by completion state.

    Args:
        items: current todo list.
        completed: if None — return all; if True — only completed;
            if False — only pending.

    Returns:
        New list (shallow copy) filtered accordingly.
    """
    if completed is None:
        return list(items)
    return [item for item in items if item.completed == completed]
