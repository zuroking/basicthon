"""Core logic for duplicate finder.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): every public function here has at least one test.
CLI parsing lives in cli.py and is intentionally excluded from that criterion.

Uses only stdlib (hashlib, pathlib).
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def hash_file(file_path: str | Path, chunk_size: int = 8192) -> str:
    """Return SHA-256 hex digest of a file.

    Reads the file in chunks to handle large files without loading
    them fully into memory.

    Args:
        file_path: path to the file to hash. Accepts ``str`` or ``Path``.
        chunk_size: number of bytes to read per iteration. Must be > 0.

    Returns:
        Hex-encoded SHA-256 hash string (64 characters).

    Raises:
        ValueError: if ``chunk_size`` is not a positive integer.
        FileNotFoundError: if ``file_path`` does not exist.
        IsADirectoryError: if ``file_path`` is a directory.
    """
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be > 0, got {chunk_size}")

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"file does not exist: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"path is a directory, not a file: {path}")

    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(
    directory: str | Path,
    recursive: bool = True,
) -> dict[str, list[Path]]:
    """Find duplicate files by content hash.

    Scans ``directory`` for files, hashes each file with :func:`hash_file`,
    and groups files that share the same hash. Only groups with more than
    one file are returned (i.e. actual duplicates).

    Args:
        directory: directory to scan for duplicates.
        recursive: if ``True`` scan subdirectories recursively via
            ``Path.rglob``; if ``False`` only top-level files are scanned
            via ``Path.iterdir``.

    Returns:
        Mapping ``hash -> list of Paths`` for duplicate groups only.
        Each list is sorted by path string and contains at least two entries.
        The returned dictionary is empty if no duplicates are found.
        Keys are SHA-256 hex digests.

    Raises:
        FileNotFoundError: if ``directory`` does not exist.
        NotADirectoryError: if ``directory`` exists but is not a directory.
    """
    root = Path(directory)

    if not root.exists():
        raise FileNotFoundError(f"directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"path is not a directory: {root}")

    # Collect files before hashing to avoid mixing traversal with I/O.
    if recursive:
        files = [p for p in root.rglob("*") if p.is_file()]
    else:
        files = [p for p in root.iterdir() if p.is_file()]

    # Group by hash.
    groups: dict[str, list[Path]] = {}
    for file_path in files:
        file_hash = hash_file(file_path)
        groups.setdefault(file_hash, []).append(file_path)

    # Keep only duplicates and sort each group for deterministic output.
    duplicates: dict[str, list[Path]] = {}
    for file_hash, paths in groups.items():
        if len(paths) > 1:
            duplicates[file_hash] = sorted(paths)

    return duplicates
