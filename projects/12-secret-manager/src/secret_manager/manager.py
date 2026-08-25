"""Core logic for secret manager.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): every public function here has at least one test.
CLI parsing lives in cli.py and is intentionally excluded.

Storage scheme: JSON file mapping secret name -> Fernet token string.
Crypto primitive: Fernet (AES-128-CBC + HMAC-SHA256, authenticated
encryption) from ``cryptography``. Chosen for high-level misuse-resistant API.

Educational only — not for production (see ARCHITECTURE.md §9).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


def generate_key() -> str:
    """Generate a new Fernet key as a base64 urlsafe string.

    Returns:
        44-character urlsafe base64 string suitable for ``SECRET_MANAGER_KEY``.
    """
    return Fernet.generate_key().decode("utf-8")


def get_key_from_env(var_name: str = "SECRET_MANAGER_KEY") -> str:
    """Return encryption key from environment variable.

    Args:
        var_name: name of env variable to read.

    Returns:
        Key string from env.

    Raises:
        ValueError: if variable is missing or empty/whitespace.
    """
    if not isinstance(var_name, str):
        raise ValueError("var_name must be a string")
    cleaned = var_name.strip()
    if not cleaned:
        raise ValueError("var_name must not be empty")
    value = os.environ.get(cleaned)
    if value is None or not value.strip():
        raise ValueError(f"environment variable {cleaned} is not set")
    return value.strip()


def _get_fernet(key: str | bytes) -> Fernet:
    """Create Fernet instance from key, validating format.

    Args:
        key: Fernet key as utf-8 string or bytes.

    Returns:
        Fernet instance.

    Raises:
        ValueError: if key is invalid.
    """
    if isinstance(key, str):
        key_bytes = key.encode("utf-8")
    elif isinstance(key, bytes):
        key_bytes = key
    else:
        raise ValueError("key must be str or bytes")
    try:
        return Fernet(key_bytes)
    except Exception as exc:
        raise ValueError(f"invalid Fernet key: {exc}") from exc


def _load_store(store_path: str | Path) -> dict[str, str]:
    """Load JSON store from file.

    Args:
        store_path: path to JSON file.

    Returns:
        Mapping name -> token string. Empty dict if file does not exist.

    Raises:
        ValueError: if file exists but contains invalid JSON or shape.
    """
    p = Path(store_path)
    if not p.exists():
        return {}
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"failed to read store: {exc}") from exc
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"corrupted store: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("corrupted store: top-level must be object")
    result: dict[str, str] = {}
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError("corrupted store: keys and values must be strings")
        result[k] = v
    return result


def _save_store(store_path: str | Path, data: dict[str, str]) -> None:
    """Persist store to JSON file.

    Args:
        store_path: path to JSON file.
        data: mapping to save.

    Raises:
        ValueError: if write fails.
    """
    p = Path(store_path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
        p.write_text(text + "\n", encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"failed to write store: {exc}") from exc


def _validate_name(name: str) -> str:
    """Validate secret name and return stripped form.

    Raises:
        ValueError: if name is not str or empty after strip.
    """
    if not isinstance(name, str):
        raise ValueError("name must be a string")
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("name must not be empty")
    return cleaned


def _validate_value(value: str) -> str:
    """Validate secret value.

    Raises:
        ValueError: if value is not str.
    """
    if not isinstance(value, str):
        raise ValueError("value must be a string")
    return value


def set_secret(
    store_path: str | Path,
    name: str,
    value: str,
    key: str | bytes,
) -> None:
    """Store a secret encrypted with Fernet.

    Creates store file and parent directories if needed. Overwrites existing
    entry with same name.

    Args:
        store_path: path to JSON store file.
        name: secret name, non-empty after stripping.
        value: secret value as string (may be empty, kept as-is).
        key: Fernet key as str or bytes.

    Raises:
        ValueError: if name/value/key invalid or I/O fails.
    """
    clean_name = _validate_name(name)
    _validate_value(value)
    f = _get_fernet(key)
    token = f.encrypt(value.encode("utf-8")).decode("utf-8")
    data = _load_store(store_path)
    data[clean_name] = token
    _save_store(store_path, data)


def get_secret(
    store_path: str | Path,
    name: str,
    key: str | bytes,
) -> str | None:
    """Retrieve and decrypt a secret.

    Args:
        store_path: path to JSON store file.
        name: secret name to look up.
        key: Fernet key to decrypt.

    Returns:
        Decrypted value if found, else None if store missing or name absent.

    Raises:
        ValueError: if name/key invalid or decryption fails (wrong key/corrupted).
    """
    clean_name = _validate_name(name)
    f = _get_fernet(key)
    data = _load_store(store_path)
    token = data.get(clean_name)
    if token is None:
        return None
    try:
        plaintext = f.decrypt(token.encode("utf-8"))
    except InvalidToken as exc:
        raise ValueError("decryption failed: invalid key or corrupted data") from exc
    except Exception as exc:
        raise ValueError(f"decryption failed: {exc}") from exc
    return plaintext.decode("utf-8")


def delete_secret(
    store_path: str | Path,
    name: str,
) -> None:
    """Delete a secret by name.

    Note: does not require decryption key — only removes the entry.

    Args:
        store_path: path to JSON store file.
        name: secret name to delete.

    Raises:
        ValueError: if name invalid or secret not found.
    """
    clean_name = _validate_name(name)
    data = _load_store(store_path)
    if clean_name not in data:
        raise ValueError(f"secret not found: {clean_name}")
    del data[clean_name]
    _save_store(store_path, data)


def list_secrets(
    store_path: str | Path,
) -> list[str]:
    """List all secret names sorted alphabetically.

    Does not require decryption key — returns names only.

    Args:
        store_path: path to JSON store file.

    Returns:
        Sorted list of secret names, empty if store missing or empty.
    """
    data = _load_store(store_path)
    return sorted(data.keys())
