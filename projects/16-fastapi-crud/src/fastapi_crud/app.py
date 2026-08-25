"""Core logic and FastAPI app for CRUD.

This module contains the "main logic" covered by G-13 / GRILL2-05:
every public function here has at least one test. CLI parsing lives
in ``cli.py`` and is excluded.

Storage is in-memory ``dict[int, Item]`` with auto-increment ``_next_id``.
``reset_store`` is exposed for tests to get deterministic isolation.
Environment helpers ``get_database_url`` / ``get_port`` read ``os.environ``
and are tested via monkeypatching; ``.env.example`` documents them.

Uses :mod:`fastapi`, :mod:`pydantic` (via ``models``) and :mod:`os`.
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Response, status

from fastapi_crud.models import Item, ItemCreate, ItemUpdate

# In-memory store — module-level state intentionally simple for beginners
_items: dict[int, Item] = {}
_next_id: int = 1


def get_database_url(var_name: str = "DATABASE_URL") -> str:
    """Return database URL from environment.

    Args:
        var_name: env variable name to read. Defaults to ``DATABASE_URL``.

    Returns:
        Stripped URL string. If not set, returns ``"memory"`` (in-memory).

    Raises:
        ValueError: if ``var_name`` is not a non-empty string.
    """
    if not isinstance(var_name, str):
        raise ValueError("var_name must be a string")
    cleaned = var_name.strip()
    if not cleaned:
        raise ValueError("var_name must be a non-empty string")
    value = os.environ.get(cleaned)
    if value is None or not value.strip():
        return "memory"
    return value.strip()


def get_port(var_name: str = "PORT") -> int:
    """Return port number from environment.

    Args:
        var_name: env variable name. Defaults to ``PORT``.

    Returns:
        Port as int 1..65535. If not set, returns ``8000``.

    Raises:
        ValueError: if ``var_name`` invalid or value not a valid port.
    """
    if not isinstance(var_name, str):
        raise ValueError("var_name must be a string")
    cleaned = var_name.strip()
    if not cleaned:
        raise ValueError("var_name must be a non-empty string")
    raw = os.environ.get(cleaned)
    if raw is None or not raw.strip():
        return 8000
    stripped = raw.strip()
    # bool is subclass of int, but stripped is str — this guard is
    # technically unreachable; kept for pedagogical explicitness
    if isinstance(stripped, bool):  # pragma: no cover
        raise ValueError("port must be an integer")
    try:
        port = int(stripped)
    except ValueError as exc:
        raise ValueError("port must be an integer") from exc
    if port < 1 or port > 65535:
        raise ValueError("port must be between 1 and 65535")
    return port


def get_host(var_name: str = "HOST") -> str:
    """Return host from environment.

    Args:
        var_name: env variable name. Defaults to ``HOST``.

    Returns:
        Stripped host string. If not set, returns ``"127.0.0.1"``.

    Raises:
        ValueError: if ``var_name`` invalid.
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


def reset_store() -> None:
    """Clear all items and reset id counter. Used by tests."""
    global _next_id
    _items.clear()
    _next_id = 1


def create_item(data: ItemCreate) -> Item:
    """Create a new item and store it.

    Args:
        data: validated creation payload.

    Returns:
        Created :class:`Item` with assigned id.

    Raises:
        ValueError: if ``data`` is not an ``ItemCreate``.
    """
    if not isinstance(data, ItemCreate):
        raise ValueError("data must be an ItemCreate")
    global _next_id
    title = data.title.strip()
    if not title:
        raise ValueError("title must not be empty")
    desc: str | None = None
    if data.description is not None:
        desc = data.description.strip()
        if desc == "":
            desc = None
        elif len(desc) > 500:
            raise ValueError("description too long")
    item = Item(id=_next_id, title=title, description=desc)
    _items[_next_id] = item
    _next_id += 1
    return item


def get_item(item_id: int) -> Item | None:
    """Get item by id.

    Args:
        item_id: id to look up.

    Returns:
        Item if found, else None.

    Raises:
        ValueError: if ``item_id`` is not an int (bool rejected).
    """
    if isinstance(item_id, bool):
        raise ValueError("item_id must be an integer")
    if not isinstance(item_id, int):
        raise ValueError("item_id must be an integer")
    return _items.get(item_id)


def list_items() -> list[Item]:
    """Return all stored items ordered by id ascending."""
    return sorted(_items.values(), key=lambda x: x.id)


def update_item(item_id: int, data: ItemUpdate) -> Item | None:
    """Update an existing item (partial).

    Args:
        item_id: id of item to update.
        data: update payload; only non-None fields are applied.

    Returns:
        Updated Item if found, else None.

    Raises:
        ValueError: if args have wrong types or title is empty.
    """
    if isinstance(item_id, bool):
        raise ValueError("item_id must be an integer")
    if not isinstance(item_id, int):
        raise ValueError("item_id must be an integer")
    if not isinstance(data, ItemUpdate):
        raise ValueError("data must be an ItemUpdate")
    existing = _items.get(item_id)
    if existing is None:
        return None
    title = existing.title
    description = existing.description
    if data.title is not None:
        cleaned = data.title.strip()
        if not cleaned:
            raise ValueError("title must not be empty")
        title = cleaned
    if data.description is not None:
        cleaned_desc = data.description.strip()
        if cleaned_desc == "":
            description = None
        else:
            description = cleaned_desc
    updated = Item(id=item_id, title=title, description=description)
    _items[item_id] = updated
    return updated


def delete_item(item_id: int) -> bool:
    """Delete item by id.

    Args:
        item_id: id to delete.

    Returns:
        True if deleted, False if not found.

    Raises:
        ValueError: if ``item_id`` is not an int.
    """
    if isinstance(item_id, bool):
        raise ValueError("item_id must be an integer")
    if not isinstance(item_id, int):
        raise ValueError("item_id must be an integer")
    if item_id in _items:
        del _items[item_id]
        return True
    return False


# FastAPI application — routes are thin wrappers over core functions
app = FastAPI(title="FastAPI CRUD (basicthon #16)", version="0.1.0")


@app.get("/", tags=["health"])
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}


@app.get("/health", tags=["health"])
def health_alt() -> dict[str, str]:
    """Alternative health check."""
    return {"status": "ok"}


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
def api_create_item(payload: ItemCreate) -> Item:
    """Create item."""
    try:
        return create_item(payload)
    except ValueError as exc:
        # 422 for validation-like errors (e.g. title stripped to empty)
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/items", response_model=list[Item])
def api_list_items() -> list[Item]:
    """List all items."""
    return list_items()


@app.get("/items/{item_id}", response_model=Item)
def api_get_item(item_id: int) -> Item:
    """Get item by id."""
    item = get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    return item


@app.put("/items/{item_id}", response_model=Item)
def api_update_item(item_id: int, payload: ItemUpdate) -> Item:
    """Update item."""
    try:
        updated = update_item(item_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="item not found")
    return updated


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_item(item_id: int) -> Response:
    """Delete item.

    Returns 204 No Content on success — by HTTP spec 204 must not
    include a body, so we return an explicit empty Response.
    """
    ok = delete_item(item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
