# ELI5 — FastAPI + JWT Auth

Представь клуб с охранником:

- Список гостей — `dict[username, hashed_password]` по имени `_users`. На странице `alice` лежит `bcrypt`-хэш её пароля, а не сам пароль.
- `register_user(UserCreate(username="alice", password="secret123"))` проверяет имя `3..32` `a-zA-Z0-9_-`, пароль `6..64`, делает `strip`, проверяет что не занято, хеширует `bcrypt.hashpw` + `gensalt()`, кладёт `alice -> "$2b$12$..."`, возвращает `User(username="alice")`.
- `authenticate_user("alice", "secret123")` ищет хэш, проверяет `bcrypt.checkpw`; если совпало — возвращает `User`, иначе `None`.
- `create_access_token("alice")` делает пропуск: `{"sub":"alice", "exp": now+30min}` подписывает HMAC-SHA256 ключом `SECRET_KEY` → `eyJ...`. `decode_token(token)` проверяет подпись и срок, возвращает `alice` или бросает `ValueError("token expired"/"invalid token")`.
- FastAPI — дверь: `POST /register` → зовёт `register_user` или `400` если занято; `POST /login` → `authenticate_user`, если ок — `{"access_token":"eyJ...", "token_type":"bearer"}`, иначе `401`; `GET /me` нужен заголовок `Authorization: Bearer <token>` → охранник декодит токен, проверяет что пользователь есть, отдаёт `{"username":"alice"}` или `401`.
- Настройки вне кода: `get_secret_key()` читает `$SECRET_KEY` (`dev-secret-key-change-me` если пусто — только для тестов/dev), `get_algorithm()` → `HS256`, `get_token_expire()` читает `$ACCESS_TOKEN_EXPIRE_MINUTES` (`30`). Документированы в `.env.example`, чтобы не хардкодить секрет.
- Тесты не запускают сервер: `from fastapi.testclient import TestClient; client = TestClient(app); client.post("/register", ...)`. `autouse` фикстура зовёт `reset_store` перед каждым тестом, поэтому `alice` всегда как новая.

Правила для ребёнка:

- `username` после `strip` `3..32`, только буквы/цифры/`_`/`-`; `password` `6..64`; пусто — ошибка.
- Дубликат `alice` → `ValueError` → API `400`.
- Неверный пароль или неизвестный пользователь → `None` → API `401`.
- Токен требует префикс `Bearer `; без токена/битый/просроченный/подделанный → `401` с `WWW-Authenticate: Bearer`.
- Секрет и время жизни — в env, не в коде; `HS256` — единственный алгоритм в этой игрушке; реальные приложения используют ротацию ключей и HTTPS.
- Это игрушечный список в памяти. Реальные хранят в БД, хешируют Argon2id, ставят Secure cookie, ротируют ключи — но поток тот же.
