"""FastAPI layer — adapted from project 16 (fastapi-crud).

Copy-paste adaptation per G-08 / GRILL2-08: routes wrap the SQLite
storage functions from ``storage.py`` instead of an in-memory dict.
Thin wrappers only — all logic lives in ``storage.py``.
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

from final_integration import storage

app = FastAPI(title="Final integration (basicthon #20)", version="0.1.0")


class TaskCreate(BaseModel):
    """Payload for creating a task (validated by Pydantic)."""

    title: str = Field(
        ..., min_length=1, max_length=100, description="Task title 1..100"
    )


class TaskOut(BaseModel):
    """Task as returned by API."""

    id: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=100)
    completed: bool
    created_at: str


def _db_path() -> str:
    """Resolve DB path from env for the API process."""
    return storage.get_db_path()


def get_host(var_name: str = "HOST") -> str:
    """Return host from environment.

    Args:
        var_name: env variable name. Defaults to ``HOST``.

    Returns:
        Stripped host or ``127.0.0.1`` if not set.

    Raises:
        ValueError: if var_name invalid.
    """
    if not isinstance(var_name, str):
        raise ValueError("var_name must be a string")
    cleaned = var_name.strip()
    if not cleaned:
        raise ValueError("var_name must be a non-empty string")
    value = os.environ.get(cleaned)
    if value is None or not value.strip():
        return "127.0.0.1"
    return value.strip()


def get_port(var_name: str = "PORT") -> int:
    """Return port from environment.

    Args:
        var_name: env variable name. Defaults to ``PORT``.

    Returns:
        Port 1..65535 or ``8000`` if not set.

    Raises:
        ValueError: if invalid.
    """
    if not isinstance(var_name, str):
        raise ValueError("var_name must be a string")
    cleaned = var_name.strip()
    if not cleaned:
        raise ValueError("var_name must be a non-empty string")
    raw = os.environ.get(cleaned)
    if raw is None or not raw.strip():
        return 8000
    try:
        port = int(raw.strip())
    except ValueError as exc:
        raise ValueError("port must be an integer") from exc
    if port < 1 or port > 65535:
        raise ValueError("port must be between 1 and 65535")
    return port


@app.get("/", tags=["health"])
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}


@app.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def api_add_task(payload: TaskCreate) -> TaskOut:
    """Add a task."""
    try:
        new_id = storage.add_task(_db_path(), payload.title)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    task = storage.get_task(_db_path(), new_id)
    if task is None:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail="task vanished")
    return TaskOut(
        id=task.id,
        title=task.title,
        completed=task.completed,
        created_at=task.created_at,
    )


@app.get("/tasks", response_model=list[TaskOut])
def api_list_tasks() -> list[TaskOut]:
    """List all tasks."""
    return [
        TaskOut(
            id=t.id,
            title=t.title,
            completed=t.completed,
            created_at=t.created_at,
        )
        for t in storage.list_tasks(_db_path())
    ]


@app.get("/tasks/{task_id}", response_model=TaskOut)
def api_get_task(task_id: int) -> TaskOut:
    """Get one task."""
    task = storage.get_task(_db_path(), task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return TaskOut(
        id=task.id,
        title=task.title,
        completed=task.completed,
        created_at=task.created_at,
    )


@app.put("/tasks/{task_id}/complete", response_model=TaskOut)
def api_complete_task(task_id: int) -> TaskOut:
    """Mark a task completed."""
    ok = storage.complete_task(_db_path(), task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="task not found")
    task = storage.get_task(_db_path(), task_id)
    if task is None:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail="task vanished")
    return TaskOut(
        id=task.id,
        title=task.title,
        completed=task.completed,
        created_at=task.created_at,
    )


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_task(task_id: int) -> Response:
    """Delete a task.

    Returns 204 No Content — by HTTP spec this status must not carry a
    body, so we return an explicit empty Response.
    """
    ok = storage.delete_task(_db_path(), task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
