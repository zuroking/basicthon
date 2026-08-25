# ELI5 — FastAPI + JWT Auth

Imagine a club with a bouncer:

- The guest list is `dict[username, hashed_password]` called `_users`. Page for `alice` holds `bcrypt` hash of her password, not the password itself.
- `register_user(UserCreate(username="alice", password="secret123"))` checks name `3..32` chars `a-zA-Z0-9_-`, password `6..64`, strips spaces, checks not taken, hashes with `bcrypt.hashpw` + `gensalt()`, stores `alice -> "$2b$12$..."`, returns `User(username="alice")`.
- `authenticate_user("alice", "secret123")` looks up hash, checks via `bcrypt.checkpw`; if ok returns `User`, else `None`.
- `create_access_token("alice")` makes a pass: `{"sub":"alice", "exp": now+30min}` signed with HMAC-SHA256 using `SECRET_KEY` → `eyJ...`. `decode_token(token)` verifies signature and expiry, returns `alice` or raises `ValueError("token expired"/"invalid token")`.
- FastAPI is the door: `POST /register` → calls `register_user` or `400` if taken; `POST /login` → calls `authenticate_user`, if ok returns `{"access_token":"eyJ...", "token_type":"bearer"}` else `401`; `GET /me` needs `Authorization: Bearer <token>` → bouncer decodes token, checks user exists, returns `{"username":"alice"}` or `401`.
- Settings live outside code: `get_secret_key()` reads `$SECRET_KEY` (`dev-secret-key-change-me` if missing — for tests/dev only), `get_algorithm()` returns `HS256`, `get_token_expire()` reads `$ACCESS_TOKEN_EXPIRE_MINUTES` (`30`). Documented in `.env.example` so you never hardcode real secret.
- Tests never start a real server: `from fastapi.testclient import TestClient; client = TestClient(app); client.post("/register", ...)`. An `autouse` fixture calls `reset_store` before each test, so `alice` always starts fresh.

Rules a child can follow:

- `username` stripped, `3..32`, only letters/digits/`_`/`-`; `password` `6..64`; empty after strip → error.
- Duplicate `alice` → `ValueError("already exists")` → API `400`.
- Wrong password or unknown user → `None` → API `401 incorrect username or password`.
- Token needs `Bearer ` prefix; missing/invalid/expired/tampered → `401` with `WWW-Authenticate: Bearer`.
- Secret key and lifetime live in env, not code; `HS256` is the only allowed algorithm in this toy; real apps would use stronger key rotation and HTTPS.
- This is a toy club list in memory. Real apps store users in a DB, hash with Argon2id, set Secure cookies, rotate keys — but the flow is identical.
