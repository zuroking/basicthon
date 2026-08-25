# ARCHITECTURE — 17 FastAPI JWT Auth

> Требуется по ARCHITECTURE.md §6 (≥2 решения из {крипто-примитив, схема аутентификации, хранение секрета, схема БД, retry}) — в проекте 3: выбор алгоритма JWT, хранение секрета, время жизни токена.

## 1. Решения

### 1.1 Алгоритм JWT — HS256 (HMAC-SHA256) через PyJWT

**Выбрано:** `HS256` с `PyJWT==2.8.0` — `jwt.encode({"sub": username, "exp": now+expire}, secret, algorithm="HS256")` и `jwt.decode(token, secret, algorithms=["HS256"])`. Payload минимальный: `sub` + `exp` (UTC). Секрет — 32-байтная hex строка `secrets.token_hex(32)`, хранится в env, документирован в `.env.example` как `SECRET_KEY=change-me-to-a-long-random-secret-32-bytes`.

**Почему HS256:**

- Наглядно для новичка: один секрет, одна функция, без генерации пары ключей. `PyJWT` делает `base64(JSON)+HMAC` одним вызовом; легко показать структуру `eyJ...` и проверку подделки через `jwt.decode`.
- Stdlib недостаточно: `hashlib` имеет `hmac`, но нет структуры JWT; ручной JWT требует base64url, JSON заголовка, `exp`, constant-time сравнение — легко ошибиться. `PyJWT` делает это корректно и проверяет `exp` автоматически.
- Один алгоритм: `get_algorithm` разрешает только `HS256`; `ALGORITHM=RS256` → `ValueError`. Так игрушка остаётся явной — без генерации RSA, без JWKS.

**Отклонённые альтернативы:**

- **RS256/ES256:** нужна пара ключей, PEM, `cryptography`, распределение ключей — избыточно для однопроцессной игрушки.
- **Ручной HMAC + кастомный формат:** теряет совместимость с `Authorization: Bearer` и стандартом `exp`.
- **`python-jose`:** тоже подходит, но `PyJWT` меньше, меньше зависимостей, API напрямую мапится в `ValueError`.
- **Сессионные токены без JWT:** требуют БД/Redis и lookup — больше состояния.

### 1.2 Хранение секрета — env с dev-фолбэком

**Выбрано:** `get_secret_key(var_name="SECRET_KEY")` читает `os.environ`, возвращает значение или `"dev-secret-key-change-me"` (только для dev/тестов). `get_algorithm`/`get_token_expire` аналогично. CLI не читает `SECRET_KEY` напрямую — только `auth.py`. `.env.example` документирует `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `HOST`/`PORT`/`DATABASE_URL` по GRILL2-06, с подсказкой `python -c "import secrets; print(secrets.token_hex(32))"`.

**Почему env:**

- 12-factor: секрет не в репозитории, только в env/.env (gitignored). Учит не хардкодить `SECRET_KEY`.
- `.env.example` даёт контракт без реального секрета, позволяет `monkeypatch.setenv` в тестах.
- Dev-фолбэк делает `pytest -v` зелёным без настройки env, но помечен как небезопасный.

**Отклонено:** хардкод, `input()`, JSON/YAML, KDF из пароля.

### 1.3 Время жизни — короткоживущий access-токен (30м) с `exp`

**Выбрано:** `create_access_token(..., expires_minutes=None)` строит `expire = now(timezone.utc) + timedelta(minutes=minutes)` где `minutes` из `get_token_expire()` (default `30`, `1..1440`). `decode_token` ловит `ExpiredSignatureError -> ValueError("token expired")`, `InvalidTokenError -> ValueError("invalid token")`. Без refresh-токена.

**Почему 30 минут:** достаточно для демо `GET /me`, мало для утечки; тесты создают просроченный токен через прямой `jwt.encode` с `now-1min` и проверяют `401`.

**Отклонено:** без срока (вечный), слишком короткий/длинный, refresh flow (требует второй токен, ротацию, DB), блоклист.

### 1.4 Хеширование паролей — bcrypt

**Выбрано:** `bcrypt==4.0.1` — `hash_password` via `bcrypt.hashpw(... gensalt()).decode()`, `verify_password` via `checkpw`. Username `^[a-zA-Z0-9_-]+$` + strip-валидатор; пароль `6..64`. Хэш хранится в `_users`.

**Почему bcrypt:** адаптивная стоимость, соль внутри хэша, явно для новичка. `passlib` добавил бы абстракцию.

## 2. Границы модулей

- `models.py` — только схемы `UserCreate` (с `field_validator` strip), `UserLogin`, `User`, `Token`; без логики.
- `auth.py` — ядро: `os`+`bcrypt`+`jwt`+`datetime`; все env-хелперы, пароли, JWT, хранилище. Нет `fastapi`.
- `app.py` — тонкая обёртка FastAPI: `GET /`, `GET /health`, `POST /register` (400), `POST /login` (401/422), `GET /me` via `Depends(get_current_user)` с парсингом `Authorization: Bearer`. `get_host`/`get_port` как в #16.
- `cli.py` — только `argparse` + `uvicorn`, excluded from coverage.
- `__init__.py` — re-export, `__main__.py` — `python -m fastapi_jwt`.

## 3. Почему не для продакшена (§9)

Учебная реализация:

1. Dev-фолбэк секрет; прод требует обязательный сильный ключ и ротацию, без фолбэка.
2. Один HS256 ключ без `kid`/JWKS; компрометация → всё сразу.
3. In-memory `dict`, теряется при рестарте, без блокировок.
4. Нет refresh/revocation; утёкший токен жив до `exp`.
5. Нет HTTPS/Secure cookie; токен в JSON и `Authorization`, уязвим к XSS.
6. Bcrypt cost default; прод — Argon2id.
7. Нет rate limiting на `/login`.

Прод-версия — отдельный репозиторий с JWKS, БД, refresh, HTTPS, Argon2id, rate limit.

## 4. Модель ошибок

- `ValueError` в `auth.py` для всех пользовательских ошибок, конвертируются в `HTTPException` в `app.py`: `400` дубликат, `401` для логина/токена, `422` для Pydantic.
- `get_user` → `User | None`, `authenticate_user` → `User | None`.
- `decode_token` бросает `ValueError` для всех JWT-ошибок.

## 5. Проверка

Изоляция: `pip install -e . && pip install -r requirements.txt`. Тесты: `pytest -v` с `TestClient` + `monkeypatch`, без сети, `reset_store` autouse. Lint/type: `ruff check`, `black --check`, `mypy --strict src` (11–20 strict). `.env.example` присутствует.
