# ELI5 — Final Integration (CLI + SQLite + API)

Imagine one notebook (a `tasks.db` file) and **three doors** into it:

- Door 1 is the **terminal**: `final-integration add`, `list`, `done 1` — you type, rows change.
- Door 2 is the **web API**: `POST /tasks`, `GET /tasks` — programs talk to the same notebook over HTTP.
- Door 3 is your own Python code: `add_task(db, "hi")`.

All three doors open the same notebook — write with one door, peek through another: it's already there. That's the whole trick: one `storage.py` knows the notebook's rules (strip titles, no empty tasks), and both doors just call it.

- The notebook never forgets — close everything, reopen tomorrow, tasks still there. That's SQLite magic: a whole database in one file.
- The API door has a bouncer (Pydantic): a task without a title gets bounced with `422`. Deleting answers `204` — "done, nothing to say".
- This project didn't invent anything new on purpose: the CLI part came from project #04, the database from #11, the web part from #16 — copied and glued together to show that each earlier skill was a puzzle piece.

Rules a child can follow:

- Title must not be empty or longer than 100 letters.
- Asking for a task that isn't there → "not found" (404), never a crash.
- Tests use a throwaway notebook in a temp folder — your real tasks are never touched.
