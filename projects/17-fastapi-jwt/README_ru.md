# 17 — FastAPI + JWT Auth

Изолированный учебный проект из серии `basicthon` (Systems & Integration).

**Что изучаем (lock scope):** построение типизированного JWT-слоя авторизации на FastAPI, валидацию Pydantic, хеширование `bcrypt` и работу с токенами `PyJWT`. Проект в три этапа: minimal — `User`/`UserCreate`/`Token` на `pydantic.BaseModel`, in-memory `dict[username, hashed_password]` с `register_user`/`authenticate_user`/`hash_password`/`verify_password`, JWT `create_access_token`/`decode_token` (HS256, `exp`), два публичных роута (`POST /register`, `POST /login`) + `reset_store` для тестов; improved — строгая валидация (username 3..32 `^[a-zA-Z0-9_-]+$`, пароль 6..64, strip), хеширование `bcrypt`, env-хелперы `get_secret_key`/`get_algorithm`/`get_token_expire`/`get_host`/`get_port` через `os.environ` с `.env.example`, `HTTPException(400/401/422)` и `get_current_user` с парсингом `Authorization: Bearer <token>`; production-like — типизация, тесты, `ruff/black/mypy --strict`, `pytest` зелёный для каждой публичной функции в `src/fastapi_jwt/auth.py` и `src/fastapi_jwt/app.py` (кроме `cli.py` по §5), `argparse` CLI с запуском `uvicorn`.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` содержит `fastapi==0.110.2`, `uvicorn==0.29.0`, `httpx==0.27.2`, `PyJWT==2.8.0`, `bcrypt==4.0.1` (пиннинг по G-17).

## Использование

Запуск сервера:

```bash
python -m fastapi_jwt --port 8000
# или после установки
fastapi-jwt --host 127.0.0.1 --port 8000
# с env (см. .env.example)
SECRET_KEY="change-me-32-bytes" python -m fastapi_jwt
```

Генерация секрета (не хардкодить — кладём в `.env` или env):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
# затем
export SECRET_KEY="your-hex-or-random-string"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"
fastapi-jwt
```

API (сервер на `http://127.0.0.1:8000`):

```bash
curl http://127.0.0.1:8000/
# {"status":"ok"}

curl -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}'
curl -X POST http://127.0.0.1:8000/login -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}'
# {"access_token":"eyJ...","token_type":"bearer"}

TOKEN=$(curl -s -X POST http://127.0.0.1:8000/login -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl http://127.0.0.1:8000/me -H "Authorization: Bearer $TOKEN"
```

Как библиотека:

```python
from fastapi_jwt import register_user, authenticate_user, create_access_token, decode_token, reset_store, get_secret_key
from fastapi_jwt.models import UserCreate

reset_store()
user = register_user(UserCreate(username="alice", password="secret123"))
print(authenticate_user("alice", "secret123"))  # User(username='alice')
print(authenticate_user("alice", "wrong"))      # None

token = create_access_token("alice")
print(decode_token(token))  # alice
```

TestClient без сервера:

```python
from fastapi.testclient import TestClient
from fastapi_jwt.app import app

client = TestClient(app)
client.post("/register", json={"username": "bob", "password": "secret123"})
r = client.post("/login", json={"username": "bob", "password": "secret123"})
token = r.json()["access_token"]
print(client.get("/me", headers={"Authorization": f"Bearer {token}"}).json())
```

Детали:

- `get_secret_key(var_name="SECRET_KEY") -> str` читает `os.environ`, `dev-secret-key-change-me` если пусто.
- `get_algorithm(var_name="ALGORITHM") -> str` → `HS256` если пусто, только `HS256` разрешён.
- `get_token_expire(var_name="ACCESS_TOKEN_EXPIRE_MINUTES") -> int` → `30` если пусто, 1..1440.
- `hash_password(password: str) -> str` via `bcrypt.hashpw` + `gensalt()`.
- `verify_password(plain: str, hashed: str) -> bool` via `bcrypt.checkpw`.
- `create_access_token(username: str, ...) -> str` создаёт JWT `sub`+`exp` HS256.
- `decode_token(token: str, ...) -> str` проверяет подпись и срок, возвращает `sub`.
- `register_user(data: UserCreate) -> User` — strip, проверка дубликата, хеш.
- `authenticate_user(username: str, password: str) -> User | None`.
- `get_user(username: str) -> User | None`, `reset_store() -> None`.
- `get_host`/`get_port` как в #16.
- Роуты: `GET /`, `GET /health` → `{"status":"ok"}`, `POST /register` (201/400), `POST /login` (200/401/422), `GET /me` (200/401).

## Этапы

**Minimal:** `models.py` с `UserCreate`/`User`/`Token` на `BaseModel` + `Field`, `auth.py` с `_users: dict[str,str]`, `hash_password`/`verify_password` via `bcrypt`, `create_access_token`/`decode_token` via `PyJWT` (HS256, `exp`), `register_user`/`authenticate_user`/`get_user`/`reset_store`, `FastAPI()` с `POST /register`, `POST /login`, `GET /me` protected.

**Improved:** Строгая валидация (username regex, пароль, strip, дубликат, `ValueError`), хеширование `bcrypt`, env-хелперы `get_secret_key`/`get_algorithm`/`get_token_expire`/`get_database_url`/`get_host`/`get_port` через `os.environ` с defaults, диапазон порта 1..65535, expire 1..1440, только `HS256`, `HTTPException(400/401/422)` с `WWW-Authenticate: Bearer`, `TestClient` с `autouse` `reset_store`.

**Production-like:** Type hints, `ruff/black/mypy --strict` (strict для 11–20 по §8), `pytest` зелёный для каждой публичной функции в `auth.py` и `app.py` (кроме `cli.py`), `argparse` CLI с `uvicorn.run("fastapi_jwt.app:app", ...)`, `python -m fastapi_jwt`, `.env.example` по GRILL2-06, пиннинг по G-17.

## API

```python
from fastapi_jwt import User, UserCreate, UserLogin, Token
from fastapi_jwt.auth import hash_password, verify_password, create_access_token, decode_token, register_user, authenticate_user, get_user, reset_store, get_secret_key, get_algorithm, get_token_expire
from fastapi_jwt.app import get_host, get_port, app
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## Заметка от ZuroKing

> Auth — это не магия. Покажите раскол: `register_user` делает strip, проверяет дубликат, хеширует `bcrypt` и кладёт; `create_access_token` кодирует `{"sub": username, "exp": now+30m}` HMAC-SHA256 ключом `SECRET_KEY`; `decode_token` проверяет подпись и срок; `get_current_user` парсит `Authorization: Bearer <token>`, декодит и ищет пользователя. Держите границы: `models.py` знает только `pydantic`, `auth.py` — `bcrypt`+`jwt`+`os.environ`+`dict`, `app.py` — тонкие обёртки + `HTTPException(401)` с `WWW-Authenticate: Bearer`. Тесты — через `reset_store` + `TestClient`, детерминированы, без сети и БД. И относитесь к `SECRET_KEY` честно: документируйте в `.env.example`, никогда не хардкодьте, генерируйте `secrets.token_hex(32)`, dev-ключ — только для тестов.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.

См. также: архитектура в [ARCHITECTURE.md](ARCHITECTURE.md) — требуется по §6 (≥2 решения).
