"""Pydantic models for FastAPI JWT auth.

No public functions here — only schemas — so G-13 does not apply.
Models are exercised via app/auth tests.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    """Payload for registration."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=32,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username 3..32, letters/digits/_/- only",
    )
    password: str = Field(
        ..., min_length=6, max_length=64, description="Password 6..64 chars"
    )

    @field_validator("username", mode="before")
    @classmethod
    def _strip_username(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


class UserLogin(BaseModel):
    """Payload for login — same fields as registration."""

    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6, max_length=64)

    @field_validator("username", mode="before")
    @classmethod
    def _strip_username(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


class User(BaseModel):
    """Public user info (no password)."""

    username: str = Field(..., description="Username")


class Token(BaseModel):
    """JWT response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Always bearer")


class TokenData(BaseModel):
    """Decoded token payload (internal)."""

    username: str | None = None
