# ARCHITECTURE — 12 Secret Manager

> Required per ARCHITECTURE.md §6 criterion (≥2 decisions from {crypto primitive, storage scheme, secret key handling, DB schema, retry/backoff}) — this project has all three of the first.

## 1. Decisions

### 1.1 Crypto primitive — Fernet (cryptography)

**Chosen:** `cryptography.fernet.Fernet` — AES-128 in CBC mode + PKCS7 + HMAC-SHA256 for authentication, with timestamp and IV per token. High-level, misuse-resistant. Key is 32 random bytes urlsafe-base64-encoded (44 chars).

**Why not alternatives:**

- **Raw `hashlib`/std `secrets` + `base64`**: stdlib has no authenticated encryption primitive. Using `secrets` for passwords (project #03) is fine, but encrypting values needs confidentiality + integrity. Building AES manually from `hashlib` is insecure and out of scope for beginners.
- **Manual AES-GCM with `Crypto`/`pyaes`**: lower-level, requires correct nonce handling, tag verification, and key derivation. Easy to misuse (nonce reuse, missing auth). Fernet bundles these correctly in one call `Fernet(key).encrypt(plaintext)`.
- **`cryptography` lower-level `AESGCM` / `ChaCha20Poly1305`**: also secure, but require caller to manage nonce and store tag/nonce alongside ciphertext. Fernet stores all needed metadata inside the token string, simplifying the JSON storage to `name -> token`.
- **External KMS / `keyring`**: outside learning goal; requires OS integration and network.

**Dependency justification:** `cryptography==42.0.8` pinned in `requirements.txt` (GRILL2-12). `pyproject.toml:dependencies = []`; runtime deps only via `requirements.txt` per GRILL2-02. Stdlib alone is intentionally insufficient — no stdlib primitive provides authenticated symmetric encryption suitable for secret storage without third-party help.

### 1.2 Storage scheme — JSON file with encrypted values

**Chosen:** Single JSON file (`secrets.json` by default, configurable via `--store` or `$SECRET_STORE_PATH`). Structure: `dict[str, str]` where keys are secret names (stripped, non-empty) and values are Fernet token strings (urlsafe base64, `gAAAA...`). File is written with `json.dumps(indent=2, sort_keys=True)` and parent dirs created via `Path.parent.mkdir(parents=True)`.

**Why JSON file:**

- **Beginner-visible:** human-readable, stdlib `json` + `pathlib` only, no DB dependency (contrast with project #11 SQLite). Easy to inspect that plaintext never appears on disk.
- **Isolation:** copy folder anywhere, `tmp_path` tests use real files, no server.
- **Atomicity tradeoff accepted:** for learning, simplicity > durability. We do `write_text` replacing whole file; no WAL, no file locking, no `fsync`. Sufficient for single-process toy usage.

**Alternatives rejected:**

- **SQLite (as in #11):** adds SQL overhead for a simple `name -> blob` map. Columns would still hold encrypted blobs; no query benefit beyond `LIKE`. JSON is lighter for this stage.
- **Dotenv / plain env file:** stores plaintext; loses ability to list/delete programmatically and version store file.
- **Encrypted SQLite / SQLCipher:** heavier, needs extra deps, obscures the "tokens in JSON" lesson.
- **Per-secret files:** many files, harder to list atomically, more inode churn.

**Corruption handling:** `_load_store` returns `{}` if file missing or empty (idempotent GET/LIST). Raises `ValueError("corrupted store: ...")` if JSON invalid, top-level not object, or values not `str`. This surfaces tampering clearly.

### 1.3 Key handling — env var with CLI fallback

**Chosen:** Master key lives outside code. Resolution order in CLI: `--key` arg > `$SECRET_MANAGER_KEY` > error with hint to `.env.example` / `generate-key`. Library exposes `generate_key() -> str` (`Fernet.generate_key().decode()`) and `get_key_from_env(var_name="SECRET_MANAGER_KEY") -> str` which strips, validates `var_name`, and raises `ValueError` if missing/empty. Manager functions accept `key: str | bytes` and validate via `_get_fernet` (`Fernet(key_bytes)` — raises `ValueError("invalid Fernet key")` on failure).

**Why env var:**

- Teaches 12-factor: secrets not in repo, not in JSON, only the token file is committed-ignored.
- `.env.example` documents the contract without containing real key, satisfying GRILL2-06. Contains `SECRET_MANAGER_KEY=your-44-char...` plus comment with generation command and optional `SECRET_STORE_PATH`.
- CLI fallback keeps ergonomics: `secret-manager set foo bar --key $KEY` works even without env.

**Alternatives rejected:**

- **Key inside JSON file:** defeats purpose — ciphertext and key together.
- **Hard-coded key or `input()` prompt:** not scriptable, encourages committing keys.
- **Key derivation from password via PBKDF2/Argon2:** adds password UX and KDF parameters; out of scope for minimal vault. Could be future extension but would need salt storage and iteration tuning.
- **Bytes-only key:** `str` is more ergonomic for env var; we accept `str | bytes` and normalize via `.encode("utf-8")` to support both.

## 2. Module boundaries

- `manager.py` — pure logic: `pathlib` + `json` + `Fernet` + `os` (only for `get_key_from_env`). No `argparse`, no `print`, no `sys.exit`. All public functions validated and typed; private helpers `_get_fernet`, `_load_store`, `_save_store`, `_validate_name` are `_<name>` and not covered by G-13.
- `cli.py` — thin I/O wrapper excluded from coverage: `argparse` subparsers (`generate-key/set/get/delete/list`), `_resolve_key`/`_resolve_store` helpers, exit codes, error messages to `stderr`. Imports `manager` but never duplicates crypto logic.
- `__init__.py` — re-exports `generate_key`, `get_key_from_env`, `set_secret`, `get_secret`, `delete_secret`, `list_secrets`.
- `__main__.py` — `python -m secret_manager`.

## 3. Why not for production (§9)

This vault is explicitly educational (see README banner). Must not be used for real secrets because:

1. **Key in env is still exposed:** `os.environ` visible to process list, core dumps, logs; no memory locking / zeroisation.
2. **No key rotation / versioning:** tokens are not re-encrypted when key changes; old copies remain decryptable only with old key; no envelope encryption.
3. **File permissions not hardened:** JSON file created with default umask, no `0600` enforcement, no OS keychain/HSM.
4. **No atomicity or concurrency control:** concurrent `set_secret` can clobber; no file lock, no `fsync`, no backup.
5. **Single master key, single file:** no scoping, no audit log, no TTL, no access control per secret.
6. **Tokens lack associated metadata:** no creation time, no version, no KDF context; Fernet timestamp is not used for expiry.
7. **No secure deletion:** overwriting JSON does not wipe old plaintext from disk/memory.

A production `secure-secrets-vault` (portfolio #8, separate repo) would use OS keychain or HSM, per-secret encryption with key hierarchy, `0600` files with `fsync` + locking or SQLite WAL, rotation and audit, and memory protection — all deliberately omitted here to keep this project copy-paste-isolated and beginner-readable.

## 4. Error model

- `ValueError` for user errors: empty name, non-`str` value, invalid Fernet key, missing env var, secret not found on `delete`, corrupted JSON, `InvalidToken` on `get` (wrong key or tampered token).
- `get_secret` returns `None` for "not found" (missing file or missing name) — mirrors `sqlite_notes.get_note` returning `None`, easy to branch on without exceptions.
- `list_secrets` returns `[]` for missing/empty store — no exception.
- I/O errors (`OSError` on read/write) wrapped as `ValueError` with context to keep CLI surface uniform.

## 5. Verification

Isolation: copy folder anywhere, `pip install -e . && pip install -r requirements.txt` suffices. Tests: `pytest -v` with `tmp_path` files and `monkeypatch` for env, no network, no real API keys. Lint/type: `ruff check`, `black --check`, `mypy --strict src` per §8 (projects 11–20 strict). `.env.example` present per §4/GRILL2-06.
