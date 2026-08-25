"""Tests for todo_cli.todo — covers every public function (G-13/GRILL2-05).

Uses tmp_path for JSON persistence tests as required.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from todo_cli.todo import (
    TodoItem,
    add_todo,
    complete_todo,
    delete_todo,
    list_todos,
    load_todos,
    save_todos,
)

# ---- TodoItem ----


def test_todo_item_defaults() -> None:
    item = TodoItem(id=1, title="Buy milk")
    assert item.id == 1
    assert item.title == "Buy milk"
    assert item.completed is False

    item2 = TodoItem(id=2, title="Read", completed=True)
    assert item2.completed is True


# ---- load_todos / save_todos ----


def test_load_missing_file_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "todos.json"
    assert load_todos(path) == []
    assert load_todos(str(path)) == []  # also str path


def test_load_empty_file_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "todos.json"
    path.write_text("", encoding="utf-8")
    assert load_todos(path) == []


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "todos.json"
    items = [TodoItem(id=1, title="A"), TodoItem(id=2, title="B", completed=True)]
    save_todos(path, items)
    loaded = load_todos(path)
    assert loaded == items
    # str path variant
    save_todos(str(path), loaded)
    assert load_todos(str(path)) == items


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "dir" / "todos.json"
    items = [TodoItem(id=1, title="X")]
    save_todos(path, items)
    assert path.exists()
    assert load_todos(path) == items


def test_save_writes_pretty_json(tmp_path: Path) -> None:
    path = tmp_path / "todos.json"
    save_todos(path, [TodoItem(id=1, title="hello")])
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert data == [{"id": 1, "title": "hello", "completed": False}]
    assert "\n" in raw  # pretty printed


def test_load_invalid_json_structure(tmp_path: Path) -> None:
    path = tmp_path / "todos.json"
    path.write_text('{"not": "a list"}', encoding="utf-8")
    with pytest.raises(ValueError, match="JSON array"):
        load_todos(path)

    path.write_text("[123]", encoding="utf-8")
    with pytest.raises(ValueError, match="must be an object"):
        load_todos(path)

    path.write_text('[{"id": 1}]', encoding="utf-8")
    with pytest.raises(ValueError, match="missing field"):
        load_todos(path)


def test_load_unicode_title(tmp_path: Path) -> None:
    path = tmp_path / "todos.json"
    items = [TodoItem(id=1, title="Купить молоко")]
    save_todos(path, items)
    loaded = load_todos(path)
    assert loaded[0].title == "Купить молоко"


def test_save_and_load_empty_list(tmp_path: Path) -> None:
    path = tmp_path / "todos.json"
    save_todos(path, [])
    assert load_todos(path) == []


# ---- add_todo ----


def test_add_todo_first() -> None:
    items: list[TodoItem] = []
    item = add_todo(items, "Buy milk")
    assert item.id == 1
    assert item.title == "Buy milk"
    assert item.completed is False
    assert len(items) == 1
    assert items[0] is item


def test_add_todo_increment_id() -> None:
    items = [TodoItem(id=1, title="A"), TodoItem(id=5, title="B")]
    item = add_todo(items, "C")
    assert item.id == 6
    assert len(items) == 3


def test_add_todo_strips_title() -> None:
    items: list[TodoItem] = []
    item = add_todo(items, "  hello  ")
    assert item.title == "hello"


def test_add_todo_empty_raises() -> None:
    items: list[TodoItem] = []
    with pytest.raises(ValueError, match="must not be empty"):
        add_todo(items, "")
    with pytest.raises(ValueError, match="must not be empty"):
        add_todo(items, "   ")
    with pytest.raises(ValueError, match="must be a string"):
        add_todo(items, 123)  # type: ignore[arg-type]


def test_add_todo_after_delete_keeps_increment() -> None:
    items = [TodoItem(id=1, title="A"), TodoItem(id=2, title="B")]
    delete_todo(items, 2)
    item = add_todo(items, "C")
    assert item.id == 2  # max is 1 -> next 2 (reuses deleted id is okay per logic)
    # Actually max after delete is 1 -> 2, correct


# ---- complete_todo ----


def test_complete_todo_marks_done() -> None:
    items = [TodoItem(id=1, title="A"), TodoItem(id=2, title="B")]
    result = complete_todo(items, 1)
    assert result.completed is True
    assert items[0].completed is True
    assert items[1].completed is False


def test_complete_todo_already_completed() -> None:
    items = [TodoItem(id=1, title="A", completed=True)]
    result = complete_todo(items, 1)
    assert result.completed is True


def test_complete_todo_not_found() -> None:
    items = [TodoItem(id=1, title="A")]
    with pytest.raises(ValueError, match="not found"):
        complete_todo(items, 99)


def test_complete_todo_invalid_type() -> None:
    items = [TodoItem(id=1, title="A")]
    with pytest.raises(ValueError, match="must be an integer"):
        complete_todo(items, "1")  # type: ignore[arg-type]


# ---- delete_todo ----


def test_delete_todo_removes() -> None:
    items = [TodoItem(id=1, title="A"), TodoItem(id=2, title="B")]
    delete_todo(items, 1)
    assert len(items) == 1
    assert items[0].id == 2


def test_delete_todo_not_found() -> None:
    items = [TodoItem(id=1, title="A")]
    with pytest.raises(ValueError, match="not found"):
        delete_todo(items, 42)


def test_delete_todo_invalid_type() -> None:
    items = [TodoItem(id=1, title="A")]
    with pytest.raises(ValueError, match="must be an integer"):
        delete_todo(items, "1")  # type: ignore[arg-type]


def test_delete_then_complete_missing() -> None:
    items = [TodoItem(id=1, title="A")]
    delete_todo(items, 1)
    assert items == []
    with pytest.raises(ValueError, match="not found"):
        complete_todo(items, 1)


# ---- list_todos ----


def test_list_todos_all() -> None:
    items = [
        TodoItem(id=1, title="A", completed=False),
        TodoItem(id=2, title="B", completed=True),
    ]
    assert list_todos(items) == items
    # returns copy
    result = list_todos(items)
    assert result is not items
    assert result == items


def test_list_todos_filter_completed() -> None:
    items = [
        TodoItem(id=1, title="A", completed=False),
        TodoItem(id=2, title="B", completed=True),
        TodoItem(id=3, title="C", completed=True),
    ]
    assert list_todos(items, completed=True) == [items[1], items[2]]
    assert list_todos(items, completed=False) == [items[0]]


def test_list_todos_empty() -> None:
    assert list_todos([]) == []
    assert list_todos([], completed=True) == []
    assert list_todos([], completed=False) == []


# ---- integration via tmp_path ----


def test_integration_add_complete_delete_persistence(tmp_path: Path) -> None:
    path = tmp_path / "todos.json"
    items = load_todos(path)
    assert items == []

    add_todo(items, "Task 1")
    add_todo(items, "Task 2")
    save_todos(path, items)

    # reload
    items2 = load_todos(path)
    assert len(items2) == 2
    assert items2[0].title == "Task 1"
    assert items2[1].title == "Task 2"

    complete_todo(items2, 1)
    assert list_todos(items2, completed=True)[0].id == 1
    save_todos(path, items2)

    items3 = load_todos(path)
    assert items3[0].completed is True
    assert items3[1].completed is False

    delete_todo(items3, 2)
    save_todos(path, items3)
    assert load_todos(path) == [TodoItem(id=1, title="Task 1", completed=True)]


def test_integration_list_filter_after_load(tmp_path: Path) -> None:
    path = tmp_path / "todos.json"
    items: list[TodoItem] = []
    add_todo(items, "A")
    add_todo(items, "B")
    complete_todo(items, 2)
    save_todos(path, items)

    loaded = load_todos(path)
    pending = list_todos(loaded, completed=False)
    done = list_todos(loaded, completed=True)
    assert len(pending) == 1 and pending[0].id == 1
    assert len(done) == 1 and done[0].id == 2
