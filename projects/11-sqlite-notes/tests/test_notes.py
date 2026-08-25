"""Tests for sqlite_notes.notes — covers every public function."""

from __future__ import annotations

from pathlib import Path

import pytest

from sqlite_notes.notes import (
    Note,
    add_note,
    create_db,
    delete_note,
    get_note,
    list_notes,
    search_notes,
    update_note,
)


def test_create_db_creates_file(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    assert not db.exists()
    create_db(db)
    assert db.exists()
    # table exists — add should work
    nid = add_note(db, "hello", "world")
    assert nid == 1


def test_create_db_creates_parent_dirs(tmp_path: Path) -> None:
    db = tmp_path / "a" / "b" / "notes.db"
    create_db(db)
    assert db.exists()


def test_create_db_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    create_db(db)
    nid1 = add_note(db, "t1", "c1")
    create_db(db)  # second call should not wipe data
    notes = list_notes(db)
    assert len(notes) == 1
    assert notes[0].id == nid1
    nid2 = add_note(db, "t2", "c2")
    assert nid2 == 2


def test_create_db_string_path(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    create_db(str(db))
    assert db.exists()


# ---- add_note ----


def test_add_note_basic(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    create_db(db)
    nid = add_note(db, "Title", "Content")
    assert nid == 1
    note = get_note(db, nid)
    assert note is not None
    assert note.title == "Title"
    assert note.content == "Content"
    assert isinstance(note.created_at, str)
    assert len(note.created_at) > 0
    assert note.id == 1


def test_add_note_strips_title(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    nid = add_note(db, "  spaced  ", "body")
    note = get_note(db, nid)
    assert note is not None
    assert note.title == "spaced"


def test_add_note_empty_title_raises(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    with pytest.raises(ValueError, match="title must not be empty"):
        add_note(db, "", "c")
    with pytest.raises(ValueError):
        add_note(db, "   ", "c")
    with pytest.raises(ValueError):
        add_note(db, "   ", "")


def test_add_note_invalid_types(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    with pytest.raises(ValueError):
        add_note(db, 123, "c")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        add_note(db, "t", 123)  # type: ignore[arg-type]


def test_add_note_autoincrement(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    n1 = add_note(db, "a", "1")
    n2 = add_note(db, "b", "2")
    n3 = add_note(db, "c", "3")
    assert n1 == 1
    assert n2 == 2
    assert n3 == 3
    assert len(list_notes(db)) == 3


def test_add_note_content_may_be_empty(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    nid = add_note(db, "t", "")
    note = get_note(db, nid)
    assert note is not None
    assert note.content == ""


def test_add_note_string_path(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    nid = add_note(str(db), "t", "c")
    assert get_note(str(db), nid) is not None


# ---- get_note ----


def test_get_note_found_and_not_found(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    assert get_note(db, 1) is None  # no db yet
    nid = add_note(db, "t", "c")
    note = get_note(db, nid)
    assert note is not None
    assert note.title == "t"
    assert get_note(db, 999) is None


def test_get_note_invalid_id(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "t", "c")
    with pytest.raises(ValueError):
        get_note(db, "1")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        get_note(db, 1.5)  # type: ignore[arg-type]


def test_get_note_returns_note_dataclass(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    nid = add_note(db, "hello", "world")
    note = get_note(db, nid)
    assert isinstance(note, Note)
    assert note.id == nid
    assert note.title == "hello"
    assert note.content == "world"


# ---- list_notes ----


def test_list_notes_empty(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    assert list_notes(db) == []
    create_db(db)
    assert list_notes(db) == []


def test_list_notes_ordered(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "b", "2")
    add_note(db, "a", "1")
    add_note(db, "c", "3")
    notes = list_notes(db)
    assert [n.id for n in notes] == [1, 2, 3]
    assert [n.title for n in notes] == ["b", "a", "c"]


def test_list_notes_string_path(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "t", "c")
    assert len(list_notes(str(db))) == 1


# ---- update_note ----


def test_update_note_title_only(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    nid = add_note(db, "old", "content")
    updated = update_note(db, nid, title="new")
    assert updated.id == nid
    assert updated.title == "new"
    assert updated.content == "content"
    # persisted
    fetched = get_note(db, nid)
    assert fetched is not None
    assert fetched.title == "new"


def test_update_note_content_only(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    nid = add_note(db, "t", "old")
    updated = update_note(db, nid, content="new content")
    assert updated.title == "t"
    assert updated.content == "new content"


def test_update_note_both(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    nid = add_note(db, "a", "b")
    updated = update_note(db, nid, title="x", content="y")
    assert updated.title == "x"
    assert updated.content == "y"


def test_update_note_strips_title(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    nid = add_note(db, "a", "b")
    updated = update_note(db, nid, title="  spaced  ")
    assert updated.title == "spaced"


def test_update_note_not_found(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "t", "c")
    with pytest.raises(ValueError, match="not found"):
        update_note(db, 999, title="x")
    # missing db file
    db2 = tmp_path / "missing.db"
    with pytest.raises(ValueError, match="not found"):
        update_note(db2, 1, title="x")


def test_update_note_nothing_to_update(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    nid = add_note(db, "t", "c")
    with pytest.raises(ValueError, match="nothing to update"):
        update_note(db, nid)


def test_update_note_invalid_title(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    nid = add_note(db, "t", "c")
    with pytest.raises(ValueError):
        update_note(db, nid, title="   ")
    with pytest.raises(ValueError):
        update_note(db, nid, title=123)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        update_note(db, nid, content=123)  # type: ignore[arg-type]


def test_update_note_invalid_id_type(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "t", "c")
    with pytest.raises(ValueError):
        update_note(db, "1", title="x")  # type: ignore[arg-type]


# ---- delete_note ----


def test_delete_note_basic(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    n1 = add_note(db, "a", "1")
    n2 = add_note(db, "b", "2")
    delete_note(db, n1)
    assert get_note(db, n1) is None
    assert len(list_notes(db)) == 1
    assert get_note(db, n2) is not None


def test_delete_note_not_found(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "t", "c")
    with pytest.raises(ValueError, match="not found"):
        delete_note(db, 999)
    db2 = tmp_path / "missing.db"
    with pytest.raises(ValueError, match="not found"):
        delete_note(db2, 1)


def test_delete_note_invalid_type(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "t", "c")
    with pytest.raises(ValueError):
        delete_note(db, "1")  # type: ignore[arg-type]


def test_delete_note_string_path(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    nid = add_note(db, "t", "c")
    delete_note(str(db), nid)
    assert get_note(db, nid) is None


# ---- search_notes ----


def test_search_notes_by_title(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "Shopping list", "buy milk")
    add_note(db, "Work", "finish report")
    add_note(db, "Shopping ideas", "new shoes")
    results = search_notes(db, "shop")
    assert len(results) == 2
    titles = [n.title for n in results]
    assert "Shopping list" in titles
    assert "Shopping ideas" in titles


def test_search_notes_by_content(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "t1", "hello world")
    add_note(db, "t2", "goodbye")
    add_note(db, "t3", "Hello again")
    results = search_notes(db, "hello")
    # LIKE is case-insensitive for ASCII, so both hello variants match
    assert len(results) == 2


def test_search_notes_case_insensitive(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "Hello", "World")
    assert len(search_notes(db, "hello")) == 1
    assert len(search_notes(db, "HELLO")) == 1
    assert len(search_notes(db, "HeLLo")) == 1


def test_search_notes_empty_query(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "t", "c")
    assert search_notes(db, "") == []
    assert search_notes(db, "   ") == []
    assert search_notes(db, "\t\n") == []


def test_search_notes_no_matches(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "a", "b")
    assert search_notes(db, "zzz") == []


def test_search_notes_missing_db(tmp_path: Path) -> None:
    db = tmp_path / "missing.db"
    assert search_notes(db, "hello") == []


def test_search_notes_invalid_query(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "t", "c")
    with pytest.raises(ValueError):
        search_notes(db, 123)  # type: ignore[arg-type]


def test_search_notes_ordered_by_id(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "b hello", "x")
    add_note(db, "a hello", "y")
    add_note(db, "c", "hello z")
    results = search_notes(db, "hello")
    assert [r.id for r in results] == [1, 2, 3]


def test_search_notes_string_path(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "hello", "world")
    assert len(search_notes(str(db), "hello")) == 1


def test_search_notes_trims_query(tmp_path: Path) -> None:
    db = tmp_path / "notes.db"
    add_note(db, "hello", "world")
    assert len(search_notes(db, "  hello  ")) == 1
