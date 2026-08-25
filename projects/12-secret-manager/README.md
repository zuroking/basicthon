# 12 — Secret Manager

Isolated beginner project from the `basicthon` series (Data & Algorithms).

**What you learn (lock scope):** encrypted secret storage with a chosen crypto primitive, a file-based storage scheme, and key handling via environment variables. The project is built in three stages: minimal — `generate_key`/`set_secret`/`get_secret` with Fernet over a JSON file; improved — `delete_secret`/`list_secrets`/`get_key_from_env` plus `.env.example` and robust validation; production-like — typed, tested, `ruff/black/mypy --strict` clean, `argparse` CLI with `tmp_path`-based tests.

> **Educational only — not for production.** See `ARCHITECTURE.md` for why this toy vault must not store real secrets (no rotation, no hardened permissions, no HSM, single JSON file).

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` contains `cryptography==42.0.8` (pinned, see ARCHITECTURE.md for primitive choice).

## Usage

Generate a key and export it (or put into `.env`):

```bash
python -m secret_manager generate-key
# 7f...==  (44-char string)

# Linux/macOS
export SECRET_MANAGER_KEY="your-44-char-key=="
# Windows PowerShell
$env:SECRET_MANAGER_KEY="your-44-char-key=="

# Or pass explicitly
python -m secret_manager set --key "your-key==" api_token s3cr3t
```

Store and retrieve secrets (default store `./secrets.json`):

```bash
python -m secret_manager set api_token s3cr3t
# set [api_token]

python -m secret_manager get api_token
# s3cr3t

python -m secret_manager list
# api_token

python -m secret_manager delete api_token
# deleted [api_token]

# custom store path
python -m secret_manager --store /tmp/my.json set my_key my_value
python -m secret_manager --store /tmp/my.json list
python -m secret_manager --store /tmp/my.json get my_key
```

Or use console script after `pip install -e .`:

```bash
secret-manager generate-key
secret-manager set db_password hunter2
secret-manager get db_password
secret-manager list
secret-manager delete db_password
```

Use as a library:

```python
from pathlib import Path
from secret_manager import generate_key, set_secret, get_secret, list_secrets, delete_secret

store = Path("secrets.json")
key = generate_key()  # or get_key_from_env()

set_secret(store, "api_token", "s3cr3t", key)
print(get_secret(store, "api_token", key))
# s3cr3t

print(list_secrets(store))
# ['api_token']

delete_secret(store, "api_token")
print(get_secret(store, "api_token", key))
# None
```

With environment key:

```python
import os
from secret_manager import get_key_from_env, set_secret, get_secret
from pathlib import Path

os.environ["SECRET_MANAGER_KEY"] = generate_key()
key = get_key_from_env()  # reads SECRET_MANAGER_KEY, strips, validates
store = Path("secrets.json")
set_secret(store, "k", "v", key)
```

Details:

- `generate_key() -> str` returns `Fernet.generate_key().decode("utf-8")` (44-char urlsafe base64).
- `get_key_from_env(var_name="SECRET_MANAGER_KEY") -> str` reads `os.environ`, strips, raises `ValueError` if missing/empty; validates `var_name` itself.
- `set_secret(store_path, name, value, key) -> None` validates `name` non-empty after `strip`, `value` must be `str` (empty allowed), `key` must be valid Fernet key (`str`|`bytes`), creates parent dirs, encrypts `value` with `Fernet.encrypt`, stores `token.decode()` in JSON `{name.strip(): token}` with `sort_keys` and `indent=2`.
- `get_secret(store_path, name, key) -> str | None` validates `name`/`key`, loads JSON (empty dict if file missing/empty), returns `None` if `name` absent, else `Fernet.decrypt(token.encode()).decode()` or raises `ValueError` on `InvalidToken`/corruption.
- `delete_secret(store_path, name) -> None` validates `name`, raises `ValueError("secret not found: ...")` if absent, otherwise removes entry and rewrites JSON. Does not require key.
- `list_secrets(store_path) -> list[str]` returns sorted names, `[]` if file missing/empty, raises `ValueError` on corrupted JSON. Does not require key.

Storage file example (`secrets.json`):

```json
{
  "api_token": "gAAAAABh...=="
}
```

Values are Fernet tokens (urlsafe base64), never plaintext.

## Stages

**Minimal:** `generate_key` via `Fernet.generate_key`, `_get_fernet` validating key, `_load_store`/`_save_store` with `pathlib` + `json` (create parent dirs, `json.dumps(sort_keys=True, indent=2)`), `set_secret` encrypting `value.encode()` → `token.decode()`, `get_secret` decrypting with `InvalidToken` → `ValueError`. Validation `name.strip()` non-empty, `value` is `str`.

**Improved:** `delete_secret` with existence check and `ValueError` if not found, `list_secrets` sorted, `get_key_from_env` reading `os.environ` with strip/empty checks and custom `var_name`, `.env.example` documenting `SECRET_MANAGER_KEY` and `SECRET_STORE_PATH`, parent-dir creation for nested stores, empty-file handling (`""` → `{}`), corrupted JSON detection (`ValueError: corrupted store`), JSON shape validation (keys/values must be `str`), bytes-key support (`key: str | bytes`), token uniqueness (Fernet IV) test.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy --strict` clean (strict for 11–20 per ARCHITECTURE.md §8), `pytest` green for every public function in `src/secret_manager/manager.py` (excl. `cli.py` per §5) using `tmp_path` JSON stores and `monkeypatch` for env, `argparse` CLI with `--store`/`--key` (fallback to `$SECRET_MANAGER_KEY`/`$SECRET_STORE_PATH`), subcommands `generate-key/set/get/delete/list`, `python -m secret_manager` entry point, `.env.example` present per GRILL2-06 §4.

## API

```python
from secret_manager import generate_key, get_key_from_env, set_secret, get_secret, delete_secret, list_secrets
from pathlib import Path

generate_key() -> str
get_key_from_env(var_name: str = "SECRET_MANAGER_KEY") -> str
set_secret(store_path: str | Path, name: str, value: str, key: str | bytes) -> None
get_secret(store_path: str | Path, name: str, key: str | bytes) -> str | None
delete_secret(store_path: str | Path, name: str) -> None
list_secrets(store_path: str | Path) -> list[str]
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## ZuroKing's note

> Beginners think "encrypt" means `base64` or `xor`. Show them the gap: Fernet gives you *authenticated* encryption — AES-CBC plus HMAC in one call, with a key you can generate and store outside code. Keep the boundary sharp: `manager.py` knows only `pathlib` + `json` + `Fernet`, no `argparse`, no `print`. Let JSON hold only tokens, never plaintext, validate the key eagerly with `Fernet(key)` and turn every `InvalidToken` into a clear `ValueError`. Then your CLI is just `parse_args` → `set_secret`/`get_secret` → `print`, and tests stay honest with `tmp_path` — real files, real crypto, no mocks, no network. And mark it clearly: this is a teaching vault, not a vault for real passwords.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
