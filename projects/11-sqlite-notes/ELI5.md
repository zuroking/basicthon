# ELI5 — SQLite Notes

Imagine a tiny filing cabinet with one drawer called `notes`.

- The drawer has cards with `id` (number), `title`, `content`, and `created_at` (when it was made). `id` grows 1,2,3 automatically.
- `create_db("notes.db")` builds the cabinet and the drawer if they don't exist. Calling it again does nothing — safe.
- `add_note("Shopping", "buy milk")` puts a new card in, returns its number `1`. Title can't be empty.
- `get_note(1)` pulls card 1 out; if no card, you get `None`.
- `list_notes()` dumps all cards sorted by number.
- `update_note(1, title="New")` rewrites fields on card 1; if card missing, shouts `ValueError`.
- `delete_note(1)` tears card 1 out; if missing, shouts.
- `search_notes("shop")` looks inside `title` and `content` for the word `shop` (case-insensitive, like `LIKE %shop%`), returns matching cards sorted.

Rules a child can follow:

- Title after trimming spaces must not be empty; content may be empty.
- Every function checks `?` placeholders — never glue strings into SQL.
- Tests use a temporary cabinet (`tmp_path / "notes.db"`) — real SQLite file, no fake.

