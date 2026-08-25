# ELI5 — File Organizer

Imagine a messy desk drawer.

- You dump everything on the table: photos, notes, music, movies.
- `get_category` is the label maker: looks at extension (`.jpg` → `images`, `.pdf` → `documents`, `.zip` → `archives`, no label → `others`).
- `organize(source, dest)` is sorting hands: picks each file from `source`, asks label maker, puts it into `dest/images/` or `dest/documents/` etc.

Rules a child can follow:

- If file already in drawer (`dest/images/photo.jpg` exists), add `_1` → `photo_1.jpg`, then `_2`.
- Folders on the desk are ignored — only files are sorted.
- `dry_run=True` means point and say "I would put this there" but don't touch.

That's it — label, move, rename if needed, skip folders. CLI just prints `photo.jpg -> images/` so you see what happened.
