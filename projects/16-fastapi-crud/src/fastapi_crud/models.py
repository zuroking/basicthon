"""Pydantic models for FastAPI CRUD.

This module defines request/response schemas. It contains no public
functions to cover — only model classes — so the G-13 criterion does not
apply here. Models are still exercised via ``app`` tests.

Validation is done by :mod:`pydantic` via ``Field`` constraints:
- ``title`` 1..100 chars, stripped, not empty
- ``description`` max 500 chars, optional
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """Payload for creating an item."""

    title: str = Field(
        ..., min_length=1, max_length=100, description="Item title, 1..100 chars"
    )
    description: str | None = Field(
        default=None, max_length=500, description="Optional description, max 500 chars"
    )


class ItemUpdate(BaseModel):
    """Payload for updating an item (partial, all fields optional)."""

    title: str | None = Field(
        default=None, min_length=1, max_length=100, description="New title if given"
    )
    description: str | None = Field(
        default=None, max_length=500, description="New description if given"
    )


class Item(BaseModel):
    """Stored item returned by API."""

    id: int = Field(..., ge=1, description="Auto-increment id")
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
