# ELI5 — Duplicate Finder

Imagine a teacher checking if two kids copied homework.

- `hash_file` is the fingerprint machine: reads file bytes chunk by chunk, feeds `sha256`, returns a 64-char fingerprint. Same content → same fingerprint, different content → different fingerprint.
- `find_duplicates(directory)` is the detective: walks through folder (or all subfolders if `recursive=True`), fingerprints every file, puts same fingerprints in one pile. Piles with `>1` file are duplicates.

Rules a child can follow:

- If file missing → error. If path is a folder → error.
- `recursive=True` looks everywhere (`rglob`), `False` only top-level (`iterdir`).
- Each duplicate pile is sorted so tests always see same order.
- Empty files have same fingerprint too — two empties are duplicates.
- CLI just prints `hash ...:` and file list, or "no duplicates found".
