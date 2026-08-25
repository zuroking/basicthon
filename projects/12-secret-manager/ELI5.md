# ELI5 — Secret Manager

Imagine a diary with a lockbox:

- You have a magic key (`SECRET_MANAGER_KEY`, 44 letters). You make it with `generate_key()`. Keep it outside the diary — in your pocket (environment variable).
- The diary is a JSON file (`secrets.json`). Inside are cards: `{"api_token": "gAAAA...=="}`. The value is not plain text — it's scrambled with the magic key.
- `set_secret("api_token", "s3cr3t", key)` — takes your word `s3cr3t`, scrambles it with the key, puts card `api_token` in the diary. If card exists, it overwrites.
- `get_secret("api_token", key)` — finds the card, unscrambles with the same key, returns `s3cr3t`. Wrong key → shouts `ValueError`. No card → `None`.
- `delete_secret("api_token")` — tears the card out. No key needed, just name. If no card, shouts.
- `list_secrets()` — reads all card names sorted, no key needed (names are not secret, values are).

Rules a child can follow:

- Name after trimming spaces must not be empty; value may be empty.
- Key must be a valid Fernet key (44-char string); bad key → `ValueError`.
- Diary is just JSON — if you open it, you see only scrambled tokens, never plain words.
- Tests use a temporary diary (`tmp_path / "secrets.json"`) — real file, real scramble, no network.
- This is a toy lockbox. Real vaults hide keys in hardware, rotate keys, lock memory, and handle many users — this one does none of that.
