# ARCHITECTURE — 17 FastAPI JWT Auth

> Required per ARCHITECTURE.md §6 criterion (≥2 decisions from {crypto primitive, auth scheme, secret storage, DB schema, retry/backoff}) — this project has 3: JWT algorithm choice, secret storage, token lifetime.

## 1. Decisions

### 1.1 JWT algorithm — HS256 (HMAC-SHA256) via PyJWT

**Chosen:** `HS256` with `PyJWT==2.8.0` — `jwt.encode({"sub": username, "exp": now+expire}, secret, algorithm="HS256")` and `jwt.decode(token, secret, algorithms=["HS256"])`. Payload minimal: `sub` (username) + `exp` (UTC). Secret is a 32-byte hex string generated via `secrets.token_hex(32)`, stored in env, documented in `.env.example` as `SECRET_KEY=change-me-to-a-long-random-secret-32-bytes`.

**Why HS256:**

- **Beginner-visible:** symmetric HMAC is one secret, one function, no key-pair generation. `PyJWT` does `base64(JSON)+HMAC` in one call; easy to inspect `eyJ...` structure (header.payload.signature) in tests via `jwt.decode` and to show tampering detection.
- **Stdlib insufficient:** `hashlib` has `hmac` but no JWT structure; building JWT manually requires correct base64url, header JSON, `exp` handling, and constant-time compare — easy to get wrong. `PyJWT` bundles this correctly and validates `exp` automatically.
- **Single alg constraint:** `get_algorithm` only allows `HS256`; any `ALGORITHM=RS256` raises `ValueError("unsupported algorithm, only HS256 allowed")`. This keeps the toy explicit — no RS256 key generation, no JWKS fetching, no `cryptography` dependency for RSA.

**Alternatives rejected:**

- **RS256 / ES256 (asymmetric):** requires private/public key pair, PEM handling, `cryptography` for key generation, and key distribution. Overkill for single-process in-memory toy; HS256 teaches the same `sub`+`exp` flow with less setup. Could be upgrade path if project needed service-to-service verification with separate signer/verifier.
- **Manual HMAC with `hashlib` + custom token format:** loses JWT ecosystem compatibility and `exp` standard; custom format would need extra docs for `Bearer` header integration. JWT is industry standard for `Authorization: Bearer`.
- **`python-jose`:** also valid, but `PyJWT` is smaller, has fewer transitive deps, and its API (`encode`/`decode` with `ExpiredSignatureError`/`InvalidTokenError`) maps directly to `ValueError("token expired"/"invalid token")` conversion used here.
- **No library / DB session tokens:** opaque random tokens with server-side store would require DB/Redis and lookup on every request — more state, less instructive for stateless JWT lesson.

**Dependency justification:** `PyJWT==2.8.0` pinned in `requirements.txt` (G-17). `pyproject.toml:dependencies = []` per GRILL2-02. Stdlib alone cannot produce standard JWT with `exp` verification without error-prone hand-rolling.

### 1.2 Secret storage — env var with dev fallback

**Chosen:** Secret lives outside code. Resolution: `get_secret_key(var_name="SECRET_KEY")` reads `os.environ.get(var_name)`, strips, returns value if present, else `"dev-secret-key-change-me"` (dev-only default). `get_algorithm` and `get_token_expire` follow same pattern. CLI never reads `SECRET_KEY` directly — only `auth.py` helpers do, tested via `monkeypatch`. `.env.example` documents `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `HOST`/`PORT`/`DATABASE_URL` per GRILL2-06, with generation hint `python -c "import secrets; print(secrets.token_hex(32))"`.

**Why env var:**

- 12-factor: secret not in repo, not in JSON/DB, only env/.env (gitignored). Teaches never to hardcode `SECRET_KEY = "mykey"` in `app.py`.
- `.env.example` provides contract without real secret, satisfying GRILL2-06 and allowing tests to use `monkeypatch.setenv("SECRET_KEY", "test-secret-123")` without real file.
- Dev fallback keeps `pytest -v` green without env setup, but is clearly unsafe — README and `ARCHITECTURE.md` §3 mark it as dev-only, not for prod.

**Alternatives rejected:**

- **Hard-coded secret in `app.py`:** would be committed, visible in repo, violates G-12 (no secrets in tests) and teaches bad habit.
- **`input()` prompt at startup:** not scriptable, breaks `TestClient` and `uvicorn` auto-reload; env is scriptable and CI-friendly.
- **JSON/YAML config file with secret:** file would need gitignore, permissions, and parsing; env is simpler for beginner and aligns with project #16 `DATABASE_URL`/`PORT` handling.
- **Key derivation from password (`PBKDF2`):** adds password UX and salt storage; out of scope for minimal JWT lesson. Could be added if project required user-chosen master password obfuscation.

### 1.3 Token lifetime — short-lived access token (30m) with `exp`

**Chosen:** `create_access_token(username, secret_key=None, algorithm=None, expires_minutes=None)` builds `expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)` where `minutes` from `get_token_expire()` (default `30`, allowed `1..1440`). Payload `{"sub": username, "exp": expire}`. `decode_token` calls `jwt.decode(..., options={"verify_exp": True})` implicitly via `PyJWT` and converts `ExpiredSignatureError -> ValueError("token expired")`, `InvalidTokenError -> ValueError("invalid token")`, missing `sub -> ValueError("invalid token payload")`. No refresh token — single access token.

**Why 30 minutes:**

- **Beginner demo:** long enough to test `GET /me` without immediate expiry, short enough to demonstrate `exp` verification. Tests create intentionally expired tokens via direct `jwt.encode({"sub":...,"exp": now-1min})` to verify `401 "token expired"`.
- **HS256 + `exp` only:** minimal claims to avoid complexity (`iat`, `jti`, `aud`, `iss` omitted). Keeps `create_access_token` signature small and testable.

**Alternatives rejected:**

- **No expiry (permanent token):** insecure — leaked token never expires; violates JWT best practice and removes opportunity to teach `exp`.
- **Very short expiry (<1m) or long expiry (>1 day):** short would flake tests (clock skew), long hides expiry logic. `1..1440` bounds keep it reasonable.
- **Refresh token flow (access + refresh):** requires second token, rotation, revocation list or DB, and `/refresh` endpoint — doubles scope. Out of scope for beginner isolated project; could be extension after #17.
- **Sliding window / `iat` + server-side blocklist:** needs storage for revoked tokens (Redis/DB), contradicts stateless JWT lesson and in-memory simplicity.

### 1.4 Password hashing — bcrypt (separate decision, supporting)

**Chosen:** `bcrypt==4.0.1` — `hash_password` via `bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()`, `verify_password` via `bcrypt.checkpw`. Username validation via Pydantic `^[a-zA-Z0-9_-]+$` + strip validator; password `6..64` chars. Hash is stored per-user in `_users: dict[str,str]`; plaintext never stored.

**Why bcrypt:**

- **Adaptive cost:** `gensalt()` includes cost factor, slow by design, resists brute force — same lesson as Argon2id in #12 but lighter dep. `passlib` would add extra abstraction; direct `bcrypt` is explicit for beginner.
- **Salt included:** hash string contains salt, no separate storage needed — keeps `_users` value as single string.

## 2. Module boundaries

- `models.py` — Pydantic schemas only: `UserCreate` (with `field_validator` strip before pattern), `UserLogin`, `User`, `Token`, `TokenData`. No logic, no `os`/`bcrypt`/`jwt`.
- `auth.py` — pure core logic: `os` + `bcrypt` + `jwt` + `datetime`. Contains all env helpers (`get_secret_key`, `get_algorithm`, `get_token_expire`, `get_database_url`), password helpers (`hash_password`, `verify_password`), JWT helpers (`create_access_token`, `decode_token`), user store (`_users`, `register_user`, `authenticate_user`, `get_user`, `reset_store`). No `fastapi`, no `HTTPException`, no `argparse`. Every public function is G-13-covered.
- `app.py` — thin FastAPI wrapper: `FastAPI()` with `GET /`, `GET /health`, `POST /register` (400 on duplicate), `POST /login` (401 on bad creds, 422 on Pydantic), `GET /me` via `Depends(get_current_user)` parsing `Authorization: Bearer <token>` and raising `401` with `WWW-Authenticate: Bearer`. Env helpers `get_host`/`get_port` (consistent with #16) live here for CLI. Imports `auth` but never duplicates hashing/JWT logic.
- `cli.py` — CLI-only, excluded from coverage: `argparse` `--host`/`--port`/`--reload`, `_resolve_host`/`_resolve_port` with env fallback, `uvicorn.run("fastapi_jwt.app:app", ...)`.
- `__init__.py` — re-exports core and app public API.
- `__main__.py` — `python -m fastapi_jwt`.

## 3. Why not for production (§9)

This JWT auth is explicitly educational (see README). Must not be used for real auth because:

1. **Dev fallback secret:** `dev-secret-key-change-me` is hard-coded fallback if `$SECRET_KEY` not set; real deployments must require a strong random key, no fallback, and rotate.
2. **Single HS256 key, no rotation:** one `SECRET_KEY` for all tokens; no `kid` header, no JWKS, no key versioning; compromised key invalidates all tokens at once but no rotation path.
3. **In-memory user store:** `_users: dict[str,str]` cleared on restart; no persistence, no replication, no audit log; concurrent writes not locked (single-process toy, unlike #12's `secret_manager` with file locking).
4. **No refresh / revocation:** leaked access token valid until `exp` (30m); no blocklist, no `/logout` invalidation; stolen token cannot be revoked early.
5. **No HTTPS / Secure cookie:** tokens returned as JSON `access_token` and expected in `Authorization` header; no `Secure`/`HttpOnly` cookie, no `SameSite`, no TLS enforcement — vulnerable to XSS/Network sniffing if not over HTTPS.
6. **Bcrypt cost default:** `gensalt()` default cost 12 is okay for demo but not tuned; prod would choose Argon2id or higher cost and use `passlib` with constant-time policies.
7. **No rate limiting / brute force protection:** `POST /login` can be spammed; no captcha, no lockout, no delay.

A production `fastapi-jwt` (separate repo) would use env-required secret with rotation (JWKS), persistent DB with migrations, refresh tokens with revocation, HTTPS-only Secure cookies, Argon2id, rate limiting, and audit logging — all deliberately omitted here to keep this project copy-paste-isolated and beginner-readable.

## 4. Error model

- `ValueError` for user errors in `auth.py`: empty username, invalid `var_name`, duplicate `username already exists`, `password must be a string`, `invalid token`/`token expired`/`invalid token payload`, `unsupported algorithm`, `expire must be between...`. These are converted to `HTTPException` in `app.py`: `400` for duplicate registration, `401` for bad login/expired/invalid token/missing `Bearer`, `422` for Pydantic validation or `ValueError` from `authenticate_user`.
- `get_user("alice")` returns `User(username="alice")` or `None` for not found — mirrors `sqlite_notes.get_note` returning `None`, easy to branch.
- `authenticate_user` returns `User | None` — `None` means wrong password or unknown user, mapped to `401 "incorrect username or password"`.
- `decode_token` raises `ValueError` for all JWT failures — never leaks `jwt` internals to caller; `get_current_user` converts to `401` with `WWW-Authenticate: Bearer`.
- I/O errors not present (no file/DB), but `get_secret_key`/`get_token_expire` validate `var_name` eagerly.

## 5. Verification

Isolation: copy folder anywhere, `pip install -e . && pip install -r requirements.txt` suffices. Tests: `pytest -v` with `TestClient` + `monkeypatch` for env, no network, no real `SECRET_KEY`; `reset_store` autouse fixture gives deterministic `alice` per test. Lint/type: `ruff check`, `black --check`, `mypy --strict src` per §8 (projects 11–20 strict). `.env.example` present per §4/GRILL2-06. `pyproject.toml:dependencies = []`, runtime deps only via `requirements.txt` per GRILL2-02.
