"""Tests for secret_manager.manager — covers every public function."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from secret_manager.manager import (
    delete_secret,
    generate_key,
    get_key_from_env,
    get_secret,
    list_secrets,
    set_secret,
)

# ---- generate_key ----


def test_generate_key_format() -> None:
    key = generate_key()
    assert isinstance(key, str)
    assert len(key) == 44
    # must be urlsafe base64 and valid Fernet key
    f = Fernet(key.encode("utf-8"))
    token = f.encrypt(b"hello")
    assert f.decrypt(token) == b"hello"


def test_generate_key_unique() -> None:
    k1 = generate_key()
    k2 = generate_key()
    assert k1 != k2


def test_generate_key_usable_for_set_get(tmp_path: Path) -> None:
    store = tmp_path / "secrets.json"
    key = generate_key()
    set_secret(store, "a", "val", key)
    assert get_secret(store, "a", key) == "val"


def test_generate_key_bytes_variant(tmp_path: Path) -> None:
    store = tmp_path / "secrets.json"
    key_str = generate_key()
    key_bytes = key_str.encode("utf-8")
    set_secret(store, "k", "v", key_bytes)
    assert get_secret(store, "k", key_bytes) == "v"
    # cross: set with str, get with bytes
    store2 = tmp_path / "s2.json"
    set_secret(store2, "x", "y", key_str)
    assert get_secret(store2, "x", key_bytes) == "y"


# ---- get_key_from_env ----


def test_get_key_from_env_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_MANAGER_KEY", "test-key-123")
    assert get_key_from_env() == "test-key-123"


def test_get_key_from_env_strips(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_MANAGER_KEY", "  spaced  ")
    assert get_key_from_env() == "spaced"


def test_get_key_from_env_custom_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_KEY", "custom123")
    assert get_key_from_env("MY_KEY") == "custom123"


def test_get_key_from_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECRET_MANAGER_KEY", raising=False)
    with pytest.raises(ValueError, match="not set"):
        get_key_from_env()


def test_get_key_from_env_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_MANAGER_KEY", "   ")
    with pytest.raises(ValueError, match="not set"):
        get_key_from_env()


def test_get_key_from_env_invalid_var_name() -> None:
    with pytest.raises(ValueError):
        get_key_from_env("")
    with pytest.raises(ValueError):
        get_key_from_env("   ")
    with pytest.raises(ValueError):
        get_key_from_env(123)  # type: ignore[arg-type]


# ---- set_secret ----


def test_set_secret_basic(tmp_path: Path) -> None:
    store = tmp_path / "secrets.json"
    key = generate_key()
    set_secret(store, "api_key", "s3cr3t", key)
    assert store.exists()
    data = json.loads(store.read_text(encoding="utf-8"))
    assert "api_key" in data
    # value is encrypted, not plaintext
    assert data["api_key"] != "s3cr3t"
    assert isinstance(data["api_key"], str)
    assert get_secret(store, "api_key", key) == "s3cr3t"


def test_set_secret_overwrites(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "k", "v1", key)
    set_secret(store, "k", "v2", key)
    assert get_secret(store, "k", key) == "v2"
    assert list_secrets(store) == ["k"]


def test_set_secret_strips_name(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "  spaced  ", "val", key)
    assert get_secret(store, "spaced", key) == "val"
    assert list_secrets(store) == ["spaced"]


def test_set_secret_value_may_be_empty(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "empty", "", key)
    assert get_secret(store, "empty", key) == ""


def test_set_secret_creates_parent_dirs(tmp_path: Path) -> None:
    store = tmp_path / "a" / "b" / "secrets.json"
    key = generate_key()
    set_secret(store, "k", "v", key)
    assert store.exists()
    assert get_secret(store, "k", key) == "v"


def test_set_secret_string_path(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(str(store), "k", "v", key)
    assert get_secret(str(store), "k", key) == "v"


def test_set_secret_invalid_name(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    with pytest.raises(ValueError, match="name must not be empty"):
        set_secret(store, "", "v", key)
    with pytest.raises(ValueError):
        set_secret(store, "   ", "v", key)
    with pytest.raises(ValueError):
        set_secret(store, 123, "v", key)  # type: ignore[arg-type]


def test_set_secret_invalid_value(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    with pytest.raises(ValueError, match="value must be a string"):
        set_secret(store, "k", 123, key)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        set_secret(store, "k", None, key)  # type: ignore[arg-type]


def test_set_secret_invalid_key(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    with pytest.raises(ValueError, match="invalid Fernet key"):
        set_secret(store, "k", "v", "bad-key")
    with pytest.raises(ValueError):
        set_secret(store, "k", "v", b"bad")
    with pytest.raises(ValueError):
        set_secret(store, "k", "v", 123)  # type: ignore[arg-type]


def test_set_secret_encrypted_not_plaintext(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "k", "hello", key)
    text = store.read_text(encoding="utf-8")
    assert "hello" not in text


def test_set_secret_tokens_differ_for_same_value(tmp_path: Path) -> None:
    # Fernet includes IV/timestamp, so two encryptions differ
    store1 = tmp_path / "s1.json"
    store2 = tmp_path / "s2.json"
    key = generate_key()
    set_secret(store1, "k", "same", key)
    set_secret(store2, "k", "same", key)
    t1 = json.loads(store1.read_text(encoding="utf-8"))["k"]
    t2 = json.loads(store2.read_text(encoding="utf-8"))["k"]
    assert t1 != t2
    assert get_secret(store1, "k", key) == "same"
    assert get_secret(store2, "k", key) == "same"


# ---- get_secret ----


def test_get_secret_found_and_not_found(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    assert get_secret(store, "k", key) is None  # missing file
    set_secret(store, "k", "v", key)
    assert get_secret(store, "k", key) == "v"
    assert get_secret(store, "missing", key) is None


def test_get_secret_wrong_key_raises(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key1 = generate_key()
    key2 = generate_key()
    set_secret(store, "k", "secret", key1)
    with pytest.raises(ValueError, match="decryption failed"):
        get_secret(store, "k", key2)


def test_get_secret_corrupted_store(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    store.write_text("not json", encoding="utf-8")
    key = generate_key()
    with pytest.raises(ValueError, match="corrupted store"):
        get_secret(store, "k", key)


def test_get_secret_empty_file_returns_none(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    store.write_text("", encoding="utf-8")
    key = generate_key()
    assert get_secret(store, "k", key) is None


def test_get_secret_invalid_store_shape(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    store.write_text('["not", "object"]', encoding="utf-8")
    key = generate_key()
    with pytest.raises(ValueError, match="top-level must be object"):
        get_secret(store, "k", key)


def test_get_secret_invalid_key_shape(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    # manually write bad token type
    store.write_text(json.dumps({"k": 123}), encoding="utf-8")
    with pytest.raises(ValueError, match="must be strings"):
        get_secret(store, "k", key)


def test_get_secret_trims_name(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "k", "v", key)
    assert get_secret(store, "  k  ", key) == "v"


def test_get_secret_invalid_name(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "k", "v", key)
    with pytest.raises(ValueError):
        get_secret(store, "", key)
    with pytest.raises(ValueError):
        get_secret(store, 123, key)  # type: ignore[arg-type]


def test_get_secret_invalid_key_type(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "k", "v", key)
    with pytest.raises(ValueError):
        get_secret(store, "k", 123)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        get_secret(store, "k", "bad-key")


def test_get_secret_string_path(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(str(store), "k", "v", key)
    assert get_secret(str(store), "k", key) == "v"


# ---- delete_secret ----


def test_delete_secret_basic(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "a", "1", key)
    set_secret(store, "b", "2", key)
    delete_secret(store, "a")
    assert get_secret(store, "a", key) is None
    assert get_secret(store, "b", key) == "2"
    assert list_secrets(store) == ["b"]


def test_delete_secret_trims_name(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "k", "v", key)
    delete_secret(store, "  k  ")
    assert list_secrets(store) == []


def test_delete_secret_not_found(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "k", "v", key)
    with pytest.raises(ValueError, match="secret not found"):
        delete_secret(store, "missing")
    # missing file
    store2 = tmp_path / "missing.json"
    with pytest.raises(ValueError, match="secret not found"):
        delete_secret(store2, "any")


def test_delete_secret_invalid_name(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    with pytest.raises(ValueError):
        delete_secret(store, "")
    with pytest.raises(ValueError):
        delete_secret(store, 123)  # type: ignore[arg-type]


def test_delete_secret_string_path(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "k", "v", key)
    delete_secret(str(store), "k")
    assert list_secrets(store) == []


def test_delete_secret_corrupted_store(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    store.write_text("bad json", encoding="utf-8")
    with pytest.raises(ValueError, match="corrupted store"):
        delete_secret(store, "k")


# ---- list_secrets ----


def test_list_secrets_empty(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    assert list_secrets(store) == []
    # after creating empty via write
    store.write_text("{}", encoding="utf-8")
    assert list_secrets(store) == []


def test_list_secrets_sorted(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "zulu", "1", key)
    set_secret(store, "alpha", "2", key)
    set_secret(store, "mike", "3", key)
    assert list_secrets(store) == ["alpha", "mike", "zulu"]


def test_list_secrets_missing_file(tmp_path: Path) -> None:
    store = tmp_path / "missing.json"
    assert list_secrets(store) == []


def test_list_secrets_string_path(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(str(store), "k", "v", key)
    assert list_secrets(str(store)) == ["k"]


def test_list_secrets_after_delete(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "a", "1", key)
    set_secret(store, "b", "2", key)
    set_secret(store, "c", "3", key)
    delete_secret(store, "b")
    assert list_secrets(store) == ["a", "c"]


def test_list_secrets_corrupted(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    store.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="corrupted store"):
        list_secrets(store)


def test_list_secrets_does_not_need_key(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "k1", "v1", key)
    set_secret(store, "k2", "v2", key)
    # list should work without key even though values are encrypted
    assert sorted(list_secrets(store)) == ["k1", "k2"]


def test_set_get_unicode(tmp_path: Path) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    set_secret(store, "greeting", "привет 🌟", key)
    assert get_secret(store, "greeting", key) == "привет 🌟"


def test_env_integration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = tmp_path / "s.json"
    key = generate_key()
    monkeypatch.setenv("SECRET_MANAGER_KEY", key)
    env_key = get_key_from_env()
    set_secret(store, "token", "abc123", env_key)
    assert get_secret(store, "token", get_key_from_env()) == "abc123"
    # ensure env var usage does not leak to list/delete requiring key
    assert list_secrets(store) == ["token"]
    delete_secret(store, "token")
    assert get_secret(store, "token", env_key) is None
