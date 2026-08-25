"""Tests for fastapi_jwt — covers every public function (G-13)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from fastapi_jwt.app import app, get_host, get_port
from fastapi_jwt.auth import (
    authenticate_user,
    create_access_token,
    decode_token,
    get_algorithm,
    get_database_url,
    get_secret_key,
    get_token_expire,
    get_user,
    hash_password,
    register_user,
    reset_store,
    verify_password,
)
from fastapi_jwt.models import UserCreate

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_store()
    # ensure clean env for auth helpers
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("ALGORITHM", raising=False)
    monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    yield
    reset_store()


# ---- env helpers ----


def test_get_secret_key_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    assert get_secret_key() == "dev-secret-key-change-me"


def test_get_secret_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "my-secret-123")
    assert get_secret_key() == "my-secret-123"
    monkeypatch.setenv("SECRET_KEY", "  spaced  ")
    assert get_secret_key() == "spaced"


def test_get_secret_key_empty_returns_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SECRET_KEY", "   ")
    assert get_secret_key() == "dev-secret-key-change-me"


def test_get_secret_key_custom_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_KEY", "abc")
    assert get_secret_key("MY_KEY") == "abc"


def test_get_secret_key_invalid() -> None:
    with pytest.raises(ValueError, match="var_name must be"):
        get_secret_key("")
    with pytest.raises(ValueError):
        get_secret_key(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        get_secret_key("   ")


def test_get_algorithm_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALGORITHM", raising=False)
    assert get_algorithm() == "HS256"


def test_get_algorithm_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALGORITHM", "HS256")
    assert get_algorithm() == "HS256"


def test_get_algorithm_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALGORITHM", "RS256")
    with pytest.raises(ValueError, match="unsupported algorithm"):
        get_algorithm()


def test_get_algorithm_invalid_var() -> None:
    with pytest.raises(ValueError):
        get_algorithm("")
    with pytest.raises(ValueError):
        get_algorithm(123)  # type: ignore[arg-type]


def test_get_token_expire_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)
    assert get_token_expire() == 30


def test_get_token_expire_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    assert get_token_expire() == 60
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "  15  ")
    assert get_token_expire() == 15


def test_get_token_expire_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "bad")
    with pytest.raises(ValueError, match="expire must be an integer"):
        get_token_expire()
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "0")
    with pytest.raises(ValueError, match="expire must be between"):
        get_token_expire()
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "2000")
    with pytest.raises(ValueError):
        get_token_expire()


def test_get_token_expire_custom_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_EXPIRE", "10")
    assert get_token_expire("MY_EXPIRE") == 10


def test_get_token_expire_invalid_var() -> None:
    with pytest.raises(ValueError):
        get_token_expire("")
    with pytest.raises(ValueError):
        get_token_expire(123)  # type: ignore[arg-type]


def test_get_database_url_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert get_database_url() == "memory"


def test_get_database_url_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./custom.db")
    assert get_database_url() == "sqlite:///./custom.db"


def test_get_database_url_invalid() -> None:
    with pytest.raises(ValueError, match="var_name must be"):
        get_database_url("")
    with pytest.raises(ValueError):
        get_database_url(123)  # type: ignore[arg-type]


def test_get_host_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOST", raising=False)
    assert get_host() == "127.0.0.1"


def test_get_host_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOST", "0.0.0.0")
    assert get_host() == "0.0.0.0"


def test_get_host_invalid() -> None:
    with pytest.raises(ValueError):
        get_host("")
    with pytest.raises(ValueError):
        get_host(123)  # type: ignore[arg-type]


def test_get_port_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PORT", raising=False)
    assert get_port() == 8000


def test_get_port_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PORT", "9000")
    assert get_port() == 9000


def test_get_port_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PORT", "bad")
    with pytest.raises(ValueError, match="port must be an integer"):
        get_port()
    monkeypatch.setenv("PORT", "0")
    with pytest.raises(ValueError):
        get_port()


def test_get_port_invalid_var() -> None:
    with pytest.raises(ValueError):
        get_port("")
    with pytest.raises(ValueError):
        get_port(123)  # type: ignore[arg-type]


# ---- password hashing ----


def test_hash_and_verify() -> None:
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_hash_password_invalid() -> None:
    with pytest.raises(ValueError):
        hash_password("")  # type: ignore[arg-type] # empty not allowed via function
    with pytest.raises(ValueError):
        hash_password(123)  # type: ignore[arg-type]


def test_verify_password_invalid() -> None:
    with pytest.raises(ValueError):
        verify_password(123, "hash")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        verify_password("plain", 123)  # type: ignore[arg-type]
    # invalid hash string returns False, not raise
    assert verify_password("plain", "not-a-bcrypt-hash") is False


# ---- JWT ----


def test_create_and_decode_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "test-secret-123")
    token = create_access_token("alice")
    assert isinstance(token, str)
    username = decode_token(token)
    assert username == "alice"


def test_create_token_strips_username(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "test-secret-123")
    token = create_access_token("  bob  ")
    assert decode_token(token) == "bob"


def test_create_token_invalid_username() -> None:
    with pytest.raises(ValueError):
        create_access_token("")
    with pytest.raises(ValueError):
        create_access_token("   ")
    with pytest.raises(ValueError):
        create_access_token(123)  # type: ignore[arg-type]


def test_create_token_custom_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    token = create_access_token("alice", secret_key="custom-secret")
    assert decode_token(token, secret_key="custom-secret") == "alice"
    with pytest.raises(ValueError, match="invalid token"):
        decode_token(token, secret_key="wrong-secret")


def test_decode_token_invalid() -> None:
    with pytest.raises(ValueError):
        decode_token("")
    with pytest.raises(ValueError):
        decode_token("   ")
    with pytest.raises(ValueError):
        decode_token(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invalid token"):
        decode_token("not.a.token")


def test_decode_token_expired(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "test-secret-123")
    # create token that already expired by using negative expire via direct jwt
    secret = "test-secret-123"
    payload = {
        "sub": "alice",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    token: str = jwt.encode(payload, secret, algorithm="HS256")
    with pytest.raises(ValueError, match="token expired"):
        decode_token(token)


def test_decode_token_missing_sub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "test-secret-123")
    secret = "test-secret-123"
    payload = {"exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
    token: str = jwt.encode(payload, secret, algorithm="HS256")
    with pytest.raises(ValueError, match="invalid token payload"):
        decode_token(token)


# ---- core user functions ----


def test_register_and_get_user() -> None:
    user = register_user(UserCreate(username="alice", password="secret123"))
    assert user.username == "alice"
    fetched = get_user("alice")
    assert fetched is not None
    assert fetched.username == "alice"
    assert get_user("bob") is None


def test_register_duplicate() -> None:
    register_user(UserCreate(username="alice", password="secret123"))
    with pytest.raises(ValueError, match="already exists"):
        register_user(UserCreate(username="alice", password="other123"))


def test_register_strips_username() -> None:
    user = register_user(UserCreate(username="  bob  ", password="secret123"))
    assert user.username == "bob"
    assert get_user("bob") is not None


def test_register_invalid() -> None:
    with pytest.raises(ValueError):
        register_user("bad")  # type: ignore[arg-type]
    # Pydantic will reject short username, but core also validates
    with pytest.raises(ValueError):
        register_user(UserCreate(username="  ", password="secret123"))  # type: ignore[arg-type]


def test_get_user_invalid() -> None:
    with pytest.raises(ValueError):
        get_user("")
    with pytest.raises(ValueError):
        get_user(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        get_user("   ")


def test_authenticate_user_success() -> None:
    register_user(UserCreate(username="alice", password="secret123"))
    user = authenticate_user("alice", "secret123")
    assert user is not None
    assert user.username == "alice"


def test_authenticate_user_wrong_password() -> None:
    register_user(UserCreate(username="alice", password="secret123"))
    assert authenticate_user("alice", "wrong") is None
    assert authenticate_user("bob", "secret123") is None


def test_authenticate_strips_username() -> None:
    register_user(UserCreate(username="alice", password="secret123"))
    assert authenticate_user("  alice  ", "secret123") is not None


def test_authenticate_invalid() -> None:
    with pytest.raises(ValueError):
        authenticate_user(123, "pass")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        authenticate_user("alice", 123)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        authenticate_user("   ", "secret123")


def test_reset_store() -> None:
    register_user(UserCreate(username="alice", password="secret123"))
    assert get_user("alice") is not None
    reset_store()
    assert get_user("alice") is None
    # can register again after reset
    register_user(UserCreate(username="alice", password="secret123"))
    assert get_user("alice") is not None


# ---- API via TestClient ----


def test_health() -> None:
    assert client.get("/").status_code == 200
    assert client.get("/").json() == {"status": "ok"}
    assert client.get("/health").status_code == 200


def test_api_register_success() -> None:
    resp = client.post("/register", json={"username": "alice", "password": "secret123"})
    assert resp.status_code == 201
    assert resp.json() == {"username": "alice"}
    # duplicate
    resp2 = client.post(
        "/register", json={"username": "alice", "password": "secret123"}
    )
    assert resp2.status_code == 400


def test_api_register_validation() -> None:
    resp = client.post("/register", json={"username": "ab", "password": "short"})
    assert resp.status_code == 422
    resp2 = client.post("/register", json={"username": "bad@", "password": "secret123"})
    assert resp2.status_code == 422
    resp3 = client.post("/register", json={"username": "alice", "password": "123"})
    assert resp3.status_code == 422


def test_api_login_success() -> None:
    client.post("/register", json={"username": "alice", "password": "secret123"})
    resp = client.post("/login", json={"username": "alice", "password": "secret123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # token should be valid
    username = decode_token(data["access_token"])
    assert username == "alice"


def test_api_login_wrong_password() -> None:
    client.post("/register", json={"username": "alice", "password": "secret123"})
    resp = client.post("/login", json={"username": "alice", "password": "wrong123"})
    assert resp.status_code == 401
    resp2 = client.post("/login", json={"username": "bob", "password": "secret123"})
    assert resp2.status_code == 401


def test_api_login_validation() -> None:
    resp = client.post("/login", json={"username": "ab", "password": "secret123"})
    assert resp.status_code == 422


def test_api_me_success() -> None:
    client.post("/register", json={"username": "alice", "password": "secret123"})
    login = client.post("/login", json={"username": "alice", "password": "secret123"})
    token = login.json()["access_token"]
    resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == {"username": "alice"}


def test_api_me_no_token() -> None:
    resp = client.get("/me")
    assert resp.status_code == 401
    resp2 = client.get("/me", headers={"Authorization": "Bearer invalid"})
    assert resp2.status_code == 401
    resp3 = client.get("/me", headers={"Authorization": "Basic abc"})
    assert resp3.status_code == 401
    resp4 = client.get("/me", headers={"Authorization": "Bearer "})
    assert resp4.status_code == 401


def test_api_me_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "test-secret-123")
    client.post("/register", json={"username": "alice", "password": "secret123"})
    # create expired token directly
    secret = "test-secret-123"
    payload = {
        "sub": "alice",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    token: str = jwt.encode(payload, secret, algorithm="HS256")
    resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"]


def test_api_me_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "test-secret-123")
    token = create_access_token("ghost")
    resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "user not found" in resp.json()["detail"]


def test_api_me_wrong_secret() -> None:
    client.post("/register", json={"username": "alice", "password": "secret123"})
    client.post("/login", json={"username": "alice", "password": "secret123"})
    # tamper token by decoding with wrong secret via direct create
    tampered = jwt.encode(
        {"sub": "alice", "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        "wrong-secret",
        algorithm="HS256",
    )
    resp = client.get("/me", headers={"Authorization": f"Bearer {tampered}"})
    assert resp.status_code == 401


def test_os_environ_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "env-secret-123")
    assert get_secret_key() == "env-secret-123"
    monkeypatch.setenv("ALGORITHM", "HS256")
    assert get_algorithm() == "HS256"
    monkeypatch.delenv("SECRET_KEY", raising=False)
    assert get_secret_key() == "dev-secret-key-change-me"
