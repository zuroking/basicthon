"""Tests for final_integration — covers every public function (G-13).

SQLite uses tmp_path files; HTTP layer is mocked via TestClient with
a temp DB (no network). Env vars are monkeypatched per test.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from final_integration.api import app, get_host, get_port
from final_integration.storage import (
    Task,
    add_task,
    complete_task,
    create_db,
    delete_task,
    get_db_path,
    get_task,
    list_tasks,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _temp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db = tmp_path / "t.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    yield db


# ---- storage ----


def test_get_db_path_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    assert get_db_path() == "./tasks.db"


def test_get_db_path_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_PATH", " /tmp/x.db ")
    assert get_db_path() == "/tmp/x.db"


def test_get_db_path_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError):
        get_db_path("")
    with pytest.raises(ValueError):
        get_db_path(123)  # type: ignore[arg-type]


def test_create_db_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "a" / "b.db"
    create_db(db)
    create_db(db)  # second call is a no-op
    assert db.exists()


def test_add_and_get_task(tmp_path: Path) -> None:
    db = tmp_path / "x.db"
    tid = add_task(db, "  write tests  ")
    task = get_task(db, tid)
    assert isinstance(task, Task)
    assert task.id == tid
    assert task.title == "write tests"
    assert task.completed is False
    assert task.created_at  # sqlite timestamp present
    assert get_task(db, 9999) is None


def test_add_task_autoincrement(tmp_path: Path) -> None:
    db = tmp_path / "x.db"
    a = add_task(db, "one")
    b = add_task(db, "two")
    c = add_task(db, "three")
    assert (a, b, c) == (1, 2, 3)


def test_add_task_invalid(tmp_path: Path) -> None:
    db = tmp_path / "x.db"
    with pytest.raises(ValueError, match="title must be a string"):
        add_task(db, 5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="title must not be empty"):
        add_task(db, "")
    with pytest.raises(ValueError, match="title must not be empty"):
        add_task(db, "   ")
    with pytest.raises(ValueError, match="at most 100"):
        add_task(db, "x" * 101)


def test_list_tasks_ordered(tmp_path: Path) -> None:
    db = tmp_path / "x.db"
    assert list_tasks(db) == []
    add_task(db, "b")
    add_task(db, "a")
    tasks = list_tasks(db)
    assert [t.title for t in tasks] == ["b", "a"]
    assert [t.id for t in tasks] == [1, 2]


def test_complete_task(tmp_path: Path) -> None:
    db = tmp_path / "x.db"
    tid = add_task(db, "task")
    assert complete_task(db, tid) is True
    task = get_task(db, tid)
    assert task is not None and task.completed is True
    assert complete_task(db, 999) is False


def test_delete_task(tmp_path: Path) -> None:
    db = tmp_path / "x.db"
    tid = add_task(db, "doomed")
    assert delete_task(db, tid) is True
    assert get_task(db, tid) is None
    assert delete_task(db, tid) is False


def test_id_args_validation(tmp_path: Path) -> None:
    db = tmp_path / "x.db"
    for bad in ("1", True, None, 1.5):  # type: ignore[list-item]
        with pytest.raises(ValueError, match="task_id must be an integer"):
            get_task(db, bad)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            complete_task(db, bad)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            delete_task(db, bad)  # type: ignore[arg-type]


# ---- env helpers in api.py ----


def test_api_env_host_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    assert get_host() == "127.0.0.1"
    assert get_port() == 8000
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "9000")
    assert get_host() == "0.0.0.0"
    assert get_port() == 9000


def test_api_env_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PORT", "bad")
    with pytest.raises(ValueError, match="port must be an integer"):
        get_port()
    monkeypatch.setenv("PORT", "70000")
    with pytest.raises(ValueError, match="between 1 and 65535"):
        get_port()


# ---- API via TestClient (uses the same temp SQLite file) ----


def test_health() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_api_crud_flow(tmp_path: Path) -> None:
    # create
    r = client.post("/tasks", json={"title": "integrate everything"})
    assert r.status_code == 201
    data = r.json()
    tid = data["id"]
    assert data["completed"] is False
    # read
    got = client.get(f"/tasks/{tid}")
    assert got.status_code == 200
    assert got.json()["title"] == "integrate everything"
    # list
    lst = client.get("/tasks")
    assert lst.status_code == 200
    assert len(lst.json()) == 1
    # complete
    comp = client.put(f"/tasks/{tid}/complete")
    assert comp.status_code == 200
    assert comp.json()["completed"] is True
    # delete
    dele = client.delete(f"/tasks/{tid}")
    assert dele.status_code == 204
    assert client.get(f"/tasks/{tid}").status_code == 404


def test_api_not_found() -> None:
    assert client.get("/tasks/999").status_code == 404
    assert client.put("/tasks/999/complete").status_code == 404
    assert client.delete("/tasks/999").status_code == 404


def test_api_validation() -> None:
    assert client.post("/tasks", json={"title": ""}).status_code == 422
    assert client.post("/tasks", json={"title": "x" * 101}).status_code == 422
    assert client.get("/tasks/not-an-int").status_code == 422


def test_api_204_has_no_body(tmp_path: Path) -> None:
    tid = add_task(tmp_path / "y.db", "to delete")
    # ensure the API sees the same file
    import os

    old = os.environ["DATABASE_PATH"]
    os.environ["DATABASE_PATH"] = str(tmp_path / "y.db")
    try:
        r = client.delete(f"/tasks/{tid}")
        assert r.status_code == 204
        assert r.content == b""  # HTTP spec: no body for 204
    finally:
        os.environ["DATABASE_PATH"] = old


def test_cli_and_api_share_db(tmp_path: Path) -> None:
    """Data written via storage functions is visible through the API."""
    tid = add_task(tmp_path / "t.db", "shared row")
    import os

    os.environ["DATABASE_PATH"] = str(tmp_path / "t.db")
    resp = client.get(f"/tasks/{tid}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "shared row"
