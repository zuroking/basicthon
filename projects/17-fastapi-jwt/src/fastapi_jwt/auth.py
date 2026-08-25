"""Core auth logic for FastAPI JWT (basicthon #17).

This module holds the "main logic" covered by G-13 / GRILL2-05:
every public function here has at least one test. CLI parsing lives
in ``cli.py`` and is excluded.

Storage is in-memory ``dict[username, hashed_password]`` plus
``dict[username, User]`` for simplicity. ``reset_store`` is exposed
for deterministic tests.

Env helpers ``get_secret_key`` / ``get_algorithm`` /
``get_token_expire`` read ``os.environ`` and are tested via monkeypatch.
``.env.example`` documents them.

Uses :mod:`bcrypt` for password hashing and :mod:`jwt` (PyJWT) for HS256.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import bcrypt  # type: ignore[import-not-found]
import jwt

from fastapi_jwt.models import User, UserCreate

# In-memory user store: username -> hashed_password (str, bcrypt)
_users: dict[str, str] = {}


def get_secret_key(var_name: str = "SECRET_KEY") -> str:
    """Return JWT secret key from environment.

    Args:
        var_name: env variable name. Defaults to ``SECRET_KEY``.

    Returns:
        Stripped secret. If not set, returns a dev-only default
        ``dev-secret-key-change-me`` (never use in prod).

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
        return "dev-secret-key-change-me"
    return value.strip()


def get_algorithm(var_name: str = "ALGORITHM") -> str:
    """Return JWT algorithm from environment.

    Args:
        var_name: env variable name. Defaults to ``ALGORITHM``.

    Returns:
        Stripped algorithm string. If not set, returns ``HS256``.

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
        return "HS256"
    algo = value.strip()
    if algo not in ("HS256",):
        raise ValueError("unsupported algorithm, only HS256 allowed")
    return algo


def get_token_expire(var_name: str = "ACCESS_TOKEN_EXPIRE_MINUTES") -> int:
    """Return token lifetime in minutes from environment.

    Args:
        var_name: env variable name. Defaults to
            ``ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns:
        Expire minutes 1..1440. If not set, returns ``30``.

    Raises:
        ValueError: if ``var_name`` invalid or value not a valid int.
    """
    if not isinstance(var_name, str):
        raise ValueError("var_name must be a string")
    cleaned = var_name.strip()
    if not cleaned:
        raise ValueError("var_name must be a non-empty string")
    raw = os.environ.get(cleaned)
    if raw is None or not raw.strip():
        return 30
    stripped = raw.strip()
    if isinstance(stripped, bool):  # pragma: no cover - unreachable, explicit
        raise ValueError("expire must be an integer")
    try:
        minutes = int(stripped)
    except ValueError as exc:
        raise ValueError("expire must be an integer") from exc
    if minutes < 1 or minutes > 1440:
        raise ValueError("expire must be between 1 and 1440")
    return minutes


def get_database_url(var_name: str = "DATABASE_URL") -> str:
    """Return database URL from environment (kept for consistency with 16).

    Args:
        var_name: env variable name. Defaults to ``DATABASE_URL``.

    Returns:
        Stripped URL or ``memory`` if not set.

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
        return "memory"
    return value.strip()


def reset_store() -> None:
    """Clear all users. Used by tests."""
    _users.clear()


def hash_password(password: str) -> str:
    """Hash a password with bcrypt.

    Args:
        password: plain password, 6..64 chars, must be str.

    Returns:
        Bcrypt hash as utf-8 string.

    Raises:
        ValueError: if password is not a non-empty str.
    """
    if not isinstance(password, str):
        raise ValueError("password must be a string")
    if not password:
        raise ValueError("password must not be empty")
    # bcrypt hashpw returns bytes; decode for storage
    hashed: bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash.

    Args:
        plain: plain password to check.
        hashed: stored bcrypt hash.

    Returns:
        True if matches, else False.

    Raises:
        ValueError: if args are not strings.
    """
    if not isinstance(plain, str):
        raise ValueError("plain must be a string")
    if not isinstance(hashed, str):
        raise ValueError("hashed must be a string")
    try:
        result: bool = bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        return result
    except ValueError:
        return False


def create_access_token(
    username: str,
    secret_key: str | None = None,
    algorithm: str | None = None,
    expires_minutes: int | None = None,
) -> str:
    """Create a JWT for a username.

    Args:
        username: subject to embed. Must be non-empty str.
        secret_key: HMAC key; if None, read from env via ``get_secret_key``.
        algorithm: JWT alg; if None, read via ``get_algorithm``.
        expires_minutes: lifetime; if None, read via ``get_token_expire``.

    Returns:
        Encoded JWT string.

    Raises:
        ValueError: if username invalid or params invalid.
    """
    if not isinstance(username, str):
        raise ValueError("username must be a string")
    cleaned = username.strip()
    if not cleaned:
        raise ValueError("username must not be empty")
    secret = secret_key if secret_key is not None else get_secret_key()
    if not isinstance(secret, str) or not secret.strip():
        raise ValueError("secret_key must be a non-empty string")
    algo = algorithm if algorithm is not None else get_algorithm()
    if algo != "HS256":
        raise ValueError("unsupported algorithm, only HS256 allowed")
    minutes = expires_minutes if expires_minutes is not None else get_token_expire()
    if not isinstance(minutes, int) or isinstance(minutes, bool):
        raise ValueError("expires_minutes must be an integer")
    if minutes < 1 or minutes > 1440:
        raise ValueError("expires_minutes must be between 1 and 1440")
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {"sub": cleaned, "exp": expire}
    token: str = jwt.encode(payload, secret, algorithm=algo)
    return token


def decode_token(
    token: str,
    secret_key: str | None = None,
    algorithm: str | None = None,
) -> str:
    """Decode and verify a JWT, return username.

    Args:
        token: JWT string.
        secret_key: key to verify; if None, from env.
        algorithm: alg to verify; if None, from env.

    Returns:
        Username (sub) from payload.

    Raises:
        ValueError: if token invalid, expired, or payload missing sub.
    """
    if not isinstance(token, str):
        raise ValueError("token must be a string")
    cleaned = token.strip()
    if not cleaned:
        raise ValueError("token must not be empty")
    secret = secret_key if secret_key is not None else get_secret_key()
    algo = algorithm if algorithm is not None else get_algorithm()
    try:
        payload = jwt.decode(cleaned, secret, algorithms=[algo])
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError("invalid token") from exc
    username = payload.get("sub")
    if not isinstance(username, str) or not username.strip():
        raise ValueError("invalid token payload")
    return username.strip()


def get_user(username: str) -> User | None:
    """Get user by username.

    Args:
        username: username to look up.

    Returns:
        User if found, else None.

    Raises:
        ValueError: if username is not a str.
    """
    if not isinstance(username, str):
        raise ValueError("username must be a string")
    cleaned = username.strip()
    if not cleaned:
        raise ValueError("username must not be empty")
    if cleaned in _users:
        return User(username=cleaned)
    return None


def register_user(data: UserCreate) -> User:
    """Register a new user.

    Args:
        data: validated registration payload.

    Returns:
        Created User (public, no password).

    Raises:
        ValueError: if data invalid or username already exists.
    """
    if not isinstance(data, UserCreate):
        raise ValueError("data must be a UserCreate")
    username = data.username.strip()
    if not username:
        raise ValueError("username must not be empty")
    if username in _users:
        raise ValueError("username already exists")
    # password validation already via Pydantic, but also hash
    hashed = hash_password(data.password)
    _users[username] = hashed
    return User(username=username)


def authenticate_user(username: str, password: str) -> User | None:
    """Authenticate a user.

    Args:
        username: username to check.
        password: plain password to verify.

    Returns:
        User if credentials correct, else None.

    Raises:
        ValueError: if args are not strings.
    """
    if not isinstance(username, str):
        raise ValueError("username must be a string")
    if not isinstance(password, str):
        raise ValueError("password must be a string")
    cleaned = username.strip()
    if not cleaned:
        raise ValueError("username must not be empty")
    hashed = _users.get(cleaned)
    if hashed is None:
        return None
    if not verify_password(password, hashed):
        return None
    return User(username=cleaned)
