# 17 — FastAPI + JWT Auth

Isolated beginner project from the `basicthon` series (Systems & Integration).

**What you learn (lock scope):** building a typed JWT auth layer on FastAPI, Pydantic validation, password hashing with `bcrypt`, token handling with `PyJWT`, and `TestClient` testing. The project is built in three stages: minimal — `User`/`UserCreate`/`Token` via `pydantic.BaseModel`, in-memory `dict[username, hashed_password]` with `register_user`/`authenticate_user`/`hash_password`/`verify_password`, JWT `create_access_token`/`decode_token` (HS256, `exp` claim), two public routes (`POST /register`, `POST /login`) plus `reset_store` for tests; improved — strict validation (username 3..32 `^[a-zA-Z0-9_-]+$`, password 6..64, strip), `bcrypt` hashing, env helpers `get_secret_key`/`get_algorithm`/`get_token_expire`/`get_host`/`get_port` via `os.environ` with `.env.example`, `HTTPException(400/401/422)` and `get_current_user` parsing `Authorization: Bearer <token>`; production-like — typed, tested, `ruff/black/mypy --strict` clean, `pytest` green for every public function in `src/fastapi_jwt/auth.py` and `src/fastapi_jwt/app.py` (excl. `cli.py` per §5), `argparse` CLI launching `uvicorn`.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` contains `fastapi==0.110.2`, `uvicorn==0.29.0`, `httpx==0.27.2`, `PyJWT==2.8.0`, `bcrypt==4.0.1` (pinned per G-17).

## Usage

Run the server:

```bash
python -m fastapi_jwt --port 8000
# or after install
fastapi-jwt --host 127.0.0.1 --port 8000
# with env (see .env.example)
SECRET_KEY="change-me-32-bytes" python -m fastapi_jwt
```

Generate a secret (do not hardcode — put in `.env` or env var):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
# then
export SECRET_KEY="your-hex-or-random-string"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"
fastapi-jwt
```

Use the API (server on `http://127.0.0.1:8000`):

```bash
# health
curl http://127.0.0.1:8000/
# {"status":"ok"}

# register
curl -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}'
# {"username":"alice"}

# login
curl -X POST http://127.0.0.1:8000/login -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}'
# {"access_token":"eyJ...","token_type":"bearer"}

# me (protected)
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/login -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl http://127.0.0.1:8000/me -H "Authorization: Bearer $TOKEN"
# {"username":"alice"}

# missing/invalid token
curl http://127.0.0.1:8000/me -v
# 401 {"detail":"not authenticated"}
```

Or as a library:

```python
from fastapi_jwt import register_user, authenticate_user, create_access_token, decode_token, reset_store, get_secret_key
from fastapi_jwt.models import UserCreate

reset_store()
user = register_user(UserCreate(username="alice", password="secret123"))
print(user)  # User(username='alice')

print(authenticate_user("alice", "secret123"))  # User(username='alice')
print(authenticate_user("alice", "wrong"))      # None

token = create_access_token("alice")
print(decode_token(token))  # alice

print(get_secret_key())  # "dev-secret-key-change-me" if $SECRET_KEY not set
```

TestClient example (no server needed):

```python
from fastapi.testclient import TestClient
from fastapi_jwt.app import app

client = TestClient(app)
client.post("/register", json={"username": "bob", "password": "secret123"})
r = client.post("/login", json={"username": "bob", "password": "secret123"})
token = r.json()["access_token"]
print(client.get("/me", headers={"Authorization": f"Bearer {token}"}).json())
# {"username":"bob"}
```

Details:

- `get_secret_key(var_name="SECRET_KEY") -> str` reads `os.environ`, strips, returns `dev-secret-key-change-me` if missing/empty; validates `var_name`.
- `get_algorithm(var_name="ALGORITHM") -> str` reads env, returns `HS256` if missing, only `HS256` allowed.
- `get_token_expire(var_name="ACCESS_TOKEN_EXPIRE_MINUTES") -> int` reads env, returns `30` if missing, 1..1440.
- `hash_password(password: str) -> str` hashes via `bcrypt.hashpw` + `gensalt()`, returns utf-8 string.
- `verify_password(plain: str, hashed: str) -> bool` checks via `bcrypt.checkpw`.
- `create_access_token(username: str, secret_key=None, algorithm=None, expires_minutes=None) -> str` creates JWT with `sub=username`, `exp=now+minutes` (HS256).
- `decode_token(token: str, secret_key=None, algorithm=None) -> str` verifies and returns `sub`, raises `ValueError("token expired"/"invalid token")`.
- `register_user(data: UserCreate) -> User` strips username, checks duplicate, hashes, stores, returns public `User`.
- `authenticate_user(username: str, password: str) -> User | None` verifies, returns `User` or `None`.
- `get_user(username: str) -> User | None`, `reset_store() -> None`.
- `get_host`/`get_port` same as #16 (env fallback).
- FastAPI routes: `GET /`, `GET /health` → `{"status":"ok"}`, `POST /register` (201 or 400), `POST /login` (200 or 401/422), `GET /me` (200 or 401, needs `Authorization: Bearer <token>`).
- Models: `UserCreate(username 3..32 regex, password 6..64)`, `UserLogin(same)`, `User(username)`, `Token(access_token, token_type="bearer")`.

## Stages

**Minimal:** `models.py` with `UserCreate`/`User`/`Token` via `BaseModel` + `Field`, `auth.py` with `_users: dict[str,str]`, `hash_password`/`verify_password` via `bcrypt`, `create_access_token`/`decode_token` via `PyJWT` (HS256, `exp`), `register_user`/`authenticate_user`/`get_user`/`reset_store`, `FastAPI()` with `POST /register`, `POST /login`, `GET /me` protected.

**Improved:** Strict validation (username regex, password length, strip, duplicate check, `ValueError` messages), `bcrypt` hashing, env helpers `get_secret_key`/`get_algorithm`/`get_token_expire`/`get_database_url`/`get_host`/`get_port` reading `os.environ` with defaults (`dev-secret-key-change-me`/`HS256`/`30`/`memory`/`127.0.0.1`/`8000`), port range 1..65535, expire 1..1440, only `HS256` allowed, `HTTPException(400/401/422)` with `WWW-Authenticate: Bearer`, `TestClient` with `autouse` `reset_store`.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy --strict` clean (strict for 11–20 per ARCHITECTURE.md §8), `pytest` green for every public function in `src/fastapi_jwt/auth.py` and `src/fastapi_jwt/app.py` (excl. `cli.py` per §5) with `TestClient` + direct calls + `monkeypatch` for env, `argparse` CLI launching `uvicorn.run("fastapi_jwt.app:app", ...)`, `python -m fastapi_jwt` entry point, `.env.example` present per GRILL2-06 §4, pinned deps per G-17.

## API

```python
from fastapi_jwt import User, UserCreate, UserLogin, Token
from fastapi_jwt.auth import hash_password, verify_password, create_access_token, decode_token, register_user, authenticate_user, get_user, reset_store, get_secret_key, get_algorithm, get_token_expire
from fastapi_jwt.app import get_host, get_port, app

hash_password(password: str) -> str
verify_password(plain: str, hashed: str) -> bool
create_access_token(username: str, secret_key=None, algorithm=None, expires_minutes=None) -> str
decode_token(token: str, secret_key=None, algorithm=None) -> str
register_user(data: UserCreate) -> User
authenticate_user(username: str, password: str) -> User | None
get_user(username: str) -> User | None
reset_store() -> None
get_secret_key(var_name="SECRET_KEY") -> str
get_algorithm(var_name="ALGORITHM") -> str
get_token_expire(var_name="ACCESS_TOKEN_EXPIRE_MINUTES") -> int

# FastAPI app: POST /register, POST /login, GET /me, GET /, GET /health
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## ZuroKing's note

> Auth looks like magic — "send password, get token, access protected route". Show the split: password is never stored — only `bcrypt` hash; `register_user` strips username, checks duplicate, hashes, stores; `create_access_token` encodes `{"sub": username, "exp": now+30m}` with HMAC-SHA256 using `SECRET_KEY`; `decode_token` verifies signature and expiry; `get_current_user` parses `Authorization: Bearer <token>`, decodes, looks up user. Keep boundaries sharp: `models.py` knows only `pydantic`, `auth.py` knows `bcrypt`+`jwt`+`os.environ`+`dict`, `app.py` knows only thin FastAPI wrappers + `HTTPException(401)` with `WWW-Authenticate: Bearer`. Use `reset_store` + `TestClient` so tests are deterministic — no server, no DB. And treat `SECRET_KEY` honestly: document in `.env.example`, never hardcode, generate via `secrets.token_hex(32)`, default dev key is for tests only.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.

See also: architecture notes in [ARCHITECTURE.md](ARCHITECTURE.md) — required per §6 (≥2 decisions).
