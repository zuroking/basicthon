"""FastAPI app with JWT auth (basicthon #17).

Thin wrappers over ``auth.py`` core functions — routes validate via Pydantic
and raise HTTPExceptions. Env helpers are in ``auth.py``.
"""

from __future__ import annotations

import os

from fastapi import Depends, FastAPI, Header, HTTPException, status

from fastapi_jwt.auth import (
    authenticate_user,
    create_access_token,
    decode_token,
    get_user,
    register_user,
)
from fastapi_jwt.models import Token, User, UserCreate, UserLogin

app = FastAPI(title="FastAPI JWT (basicthon #17)", version="0.1.0")


# ---- helpers for header auth ----


def get_current_user(
    authorization: str | None = Header(default=None),
) -> User:
    """Resolve current user from Authorization header.

    Expects ``Authorization: Bearer <token>``.

    Raises:
        HTTPException 401 if missing/invalid/expired.
    """
    if authorization is None or not authorization.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = parts[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        username = decode_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    user = get_user(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


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
        ValueError: if var_name invalid or value not valid port.
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
    if isinstance(stripped, bool):  # pragma: no cover - unreachable
        raise ValueError("port must be an integer")
    try:
        port = int(stripped)
    except ValueError as exc:
        raise ValueError("port must be an integer") from exc
    if port < 1 or port > 65535:
        raise ValueError("port must be between 1 and 65535")
    return port


# ---- routes ----


@app.get("/", tags=["health"])
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}


@app.get("/health", tags=["health"])
def health_alt() -> dict[str, str]:
    """Alternative health check."""
    return {"status": "ok"}


@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def api_register(payload: UserCreate) -> User:
    """Register a new user."""
    try:
        return register_user(payload)
    except ValueError as exc:
        # 400 for duplicate / validation from core
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/login", response_model=Token)
def api_login(payload: UserLogin) -> Token:
    """Login and return JWT."""
    # Use authenticate_user; it returns None on failure
    try:
        user = authenticate_user(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user.username)
    return Token(access_token=token, token_type="bearer")


@app.get("/me", response_model=User)
def api_me(current: User = Depends(get_current_user)) -> User:
    """Return current authenticated user."""
    return current


# re-export for convenience in tests and __init__
__all__ = ["app", "health", "health_alt", "api_register", "api_login", "api_me"]
