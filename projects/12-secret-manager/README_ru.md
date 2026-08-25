# 12 — Менеджер секретов

Изолированный учебный проект из серии `basicthon` (Data & Algorithms).

**Что изучаем (lock scope):** шифрованное хранение секретов с выбором крипто-примитива, файловой схемой хранения и хранением ключа в переменных окружения. Проект в три этапа: minimal — `generate_key`/`set_secret`/`get_secret` на Fernet поверх JSON-файла; improved — `delete_secret`/`list_secrets`/`get_key_from_env` плюс `.env.example` и валидация; production-like — типизация, тесты, `ruff/black/mypy --strict`, CLI на `argparse` с тестами на `tmp_path`.

> **Только для обучения — не для продакшена.** Почему этот игрушечный сейф нельзя использовать для реальных секретов — см. `ARCHITECTURE_ru.md` (нет ротации, нет защиты памяти, один JSON-файл, ключ в env).

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` содержит `cryptography==42.0.8` (пиннинг, выбор примитива — см. ARCHITECTURE.md).

## Использование

Сгенерируйте ключ и экспортируйте (или добавьте в `.env`):

```bash
python -m secret_manager generate-key
# 7f...==  (44 символа)

# Linux/macOS
export SECRET_MANAGER_KEY="ваш-ключ=="
# Windows PowerShell
$env:SECRET_MANAGER_KEY="ваш-ключ=="

# или передавайте явно
python -m secret_manager set --key "ваш-ключ==" api_token s3cr3t
```

Хранение и получение (по умолчанию `./secrets.json`):

```bash
python -m secret_manager set api_token s3cr3t
# set [api_token]

python -m secret_manager get api_token
# s3cr3t

python -m secret_manager list
# api_token

python -m secret_manager delete api_token
# deleted [api_token]

# свой файл
python -m secret_manager --store /tmp/my.json set my_key my_value
python -m secret_manager --store /tmp/my.json list
python -m secret_manager --store /tmp/my.json get my_key
```

После `pip install -e .`:

```bash
secret-manager generate-key
secret-manager set db_password hunter2
secret-manager get db_password
secret-manager list
secret-manager delete db_password
```

Как библиотека:

```python
from pathlib import Path
from secret_manager import generate_key, set_secret, get_secret, list_secrets, delete_secret

store = Path("secrets.json")
key = generate_key()  # или get_key_from_env()

set_secret(store, "api_token", "s3cr3t", key)
print(get_secret(store, "api_token", key))
# s3cr3t

print(list_secrets(store))
# ['api_token']

delete_secret(store, "api_token")
print(get_secret(store, "api_token", key))
# None
```

С ключом из окружения:

```python
import os
from secret_manager import get_key_from_env, set_secret, get_secret
from pathlib import Path

os.environ["SECRET_MANAGER_KEY"] = generate_key()
key = get_key_from_env()  # читает SECRET_MANAGER_KEY
store = Path("secrets.json")
set_secret(store, "k", "v", key)
```

Детали:

- `generate_key() -> str` — `Fernet.generate_key().decode("utf-8")` (44 символа urlsafe base64).
- `get_key_from_env(var_name="SECRET_MANAGER_KEY") -> str` — читает `os.environ`, стрипует, бросает `ValueError` если пусто/нет; валидирует `var_name`.
- `set_secret(store_path, name, value, key) -> None` — `name` после `strip` не пустой, `value` — `str`, `key` — валидный Fernet `str|bytes`, создаёт директории, шифрует `Fernet.encrypt`, хранит `{name.strip(): token}` в JSON.
- `get_secret(store_path, name, key) -> str | None` — `None` если файла нет или имени нет, иначе `decrypt` или `ValueError` при неверном ключе/порче.
- `delete_secret(store_path, name) -> None` — без ключа, `ValueError` если не найдено.
- `list_secrets(store_path) -> list[str]` — отсортированный список имён, `[]` если файла нет, без ключа.

Пример файла (`secrets.json`):

```json
{
  "api_token": "gAAAAABh...=="
}
```

Значения — токены Fernet, никогда открытый текст.

## Этапы

**Minimal:** `generate_key` через `Fernet.generate_key`, `_get_fernet` с валидацией, `_load_store`/`_save_store` через `pathlib`+`json`, `set_secret` с `encrypt`, `get_secret` с `decrypt` и `InvalidToken` → `ValueError`. Валидация `name.strip()`.

**Improved:** `delete_secret` с проверкой существования, `list_secrets` отсортирован, `get_key_from_env` с `os.environ`, `.env.example` с `SECRET_MANAGER_KEY`/`SECRET_STORE_PATH`, создание родительских папок, обработка пустого файла, детект порчи JSON, проверка формы JSON, поддержка `bytes`-ключа, уникальность токенов.

**Production-like:** Type hints на всех публичных функциях, `ruff`/`black`/`mypy --strict` без ошибок (strict для 11–20 по §8 ARCHITECTURE.md), `pytest` зелёный для каждой публичной функции в `src/secret_manager/manager.py` (кроме `cli.py` по §5) с `tmp_path`, CLI на `argparse` с `--store`/`--key` (фолбэк на env), подкоманды `generate-key/set/get/delete/list`, точка входа `python -m secret_manager`, `.env.example` по GRILL2-06 §4.

## API

```python
from secret_manager import generate_key, get_key_from_env, set_secret, get_secret, delete_secret, list_secrets

generate_key() -> str
get_key_from_env(var_name: str = "SECRET_MANAGER_KEY") -> str
set_secret(store_path: str | Path, name: str, value: str, key: str | bytes) -> None
get_secret(store_path: str | Path, name: str, key: str | bytes) -> str | None
delete_secret(store_path: str | Path, name: str) -> None
list_secrets(store_path: str | Path) -> list[str]
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## Заметка от ZuroKing

> Новички думают, что "зашифровать" — это `base64` или `xor`. Покажите разрыв: Fernet даёт *аутентифицированное* шифрование — AES-CBC + HMAC одним вызовом, с ключом вне кода. Держите границу жёстко: `manager.py` знает только `pathlib` + `json` + `Fernet`, никакого `argparse` и `print`. Храните в JSON только токены, никогда открытый текст, валидируйте ключ через `Fernet(key)` и превращайте `InvalidToken` в понятный `ValueError`. Тогда CLI остаётся склейкой `parse_args` → `manager` → `print`, а тесты честны с `tmp_path` — реальные файлы, реальная криптография, без моков и сети. И честно пометьте: это учебный сейф, не сейф для реальных паролей.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.
