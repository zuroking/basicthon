# 06 — Contacts OOP

Isolated beginner project from the `basicthon` series (Structures & Patterns).

**What you learn (lock scope):** OOP with classes, encapsulation via properties, validation, and in-memory CRUD with an `argparse` CLI. The project is built in three stages: minimal — `Contact` with `name/phone/email` validation; improved — `ContactBook` with `add/get/update/delete/search/list`; production-like — typed, tested, `ruff/black/mypy` clean, JSON-backed CLI.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` is stdlib-only for this project (`# stdlib only, no external dependencies`).

## Usage

Add, get, update, delete, search and list contacts (default file `contacts.json`):

```bash
python -m contacts add "Alice" "+7 999 123-45-67" "alice@example.com"
# added Alice

python -m contacts add "Bob" "123-456-7890" "bob@example.com"
# added Bob

python -m contacts list
# Alice | +7 999 123-45-67 | alice@example.com
# Bob | 123-456-7890 | bob@example.com

python -m contacts get "alice"
# Alice | +7 999 123-45-67 | alice@example.com

python -m contacts search "ali"
# Alice | +7 999 123-45-67 | alice@example.com

python -m contacts update "Alice" --phone "+7 999 000-11-22"
# updated Alice

python -m contacts delete "Bob"
# deleted Bob
```

Use custom file:

```bash
python -m contacts --file /tmp/my.json add "Cara" "5551234567" "cara@test.com"
python -m contacts --file /tmp/my.json list
```

Or use console script after `pip install -e .`:

```bash
contacts add "Dan" "1234567" "dan@example.com"
contacts list
```

Use as a library:

```python
from contacts import Contact, ContactBook

book = ContactBook()
book.add(Contact("Alice", "+7 999 123-45-67", "alice@example.com"))
book.add("Bob", "123-456-7890", "bob@example.com")

print(book.get("alice"))  # Contact(name='Alice', ...)
print(book.search("ali"))  # [Contact(...)]
print(book.list_contacts())  # sorted by name

book.update("Alice", phone="9999999")
book.delete("Bob")
print(len(book))  # 1
```

Extra validation rules:

- `name`: non-empty, stripped, 1-100 chars.
- `phone`: 5-15 digits, allowed chars `+ - ( ) .` and space.
- `email`: must match `^[^@\s]+@[^@\s]+\.[^@\s]+$`.

All lookups (`get/update/delete`) are case-insensitive on `name`. `search` is case-insensitive substring on `name/phone/email`. Duplicate `name` (case-insensitive) raises `ValueError`.

## Stages

**Minimal:** `Contact` class with `name/phone/email` properties, validation via `_validate_*` helpers, `__repr__/__eq__/to_dict/from_dict`, setters that re-validate. Raises `ValueError` on empty/invalid fields.

**Improved:** `ContactBook` with in-memory `dict[str, Contact]` keyed by lowercased name. Methods `add(contact|name, phone, email)`, `get(name) -> Contact | None`, `update(name, phone?, email?)`, `delete(name)`, `search(query) -> list[Contact]`, `list_contacts() -> list[Contact]` sorted + aliases `list_all` and `list`. Duplicate/invalid operations raise `ValueError`, `search` returns `[]` for empty query.

**Production-like:** Type hints on all public methods, `ruff`/`black`/`mypy` clean, `pytest` green for every public method in `src/contacts/contact.py` (excl. `cli.py` per ARCHITECTURE.md §5) with in-memory tests, `argparse` CLI with subcommands `add/get/update/delete/search/list`, `--file` for JSON persistence, `python -m contacts` entry point.

## API

```python
from contacts import Contact, ContactBook

Contact(name: str, phone: str, email: str)
# raises ValueError if validation fails
# properties: name, phone, email (setters validate)
# methods: to_dict() -> dict[str, str], from_dict(data) -> Contact
# __repr__, __str__, __eq__

ContactBook()
# book.add(contact: Contact | str, phone=None, email=None) -> Contact
#   add Contact instance OR add(name, phone, email)
#   raises ValueError if duplicate or invalid

# book.get(name: str) -> Contact | None
#   case-insensitive, None if not found, ValueError if name empty/not str

# book.update(name: str, phone: str | None = None, email: str | None = None) -> Contact
#   raises ValueError if not found or nothing to update

# book.delete(name: str) -> None
#   raises ValueError if not found

# book.search(query: str) -> list[Contact]
#   case-insensitive substring on name/phone/email, [] for empty query

# book.list_contacts() -> list[Contact]  # sorted by name
# book.list_all() -> list[Contact]       # alias
# book.list() -> list[Contact]           # alias via setattr
# len(book), "name" in book
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## ZuroKing's note

> OOP here is not about "more code" — it's about boundaries. `Contact` is the gate: every name/phone/email passes validation in one place, so `ContactBook` never sees dirty data. Keep the book stupid: dict keyed by `name.lower()`, no magic normalization, explicit `ValueError` on duplicates. Then your tests are simple: create a `ContactBook`, call six methods, assert. CLI is just glue — `Contact`/`ContactBook` → `json` → `print` — and that separation is the real lesson before you hit databases.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.
