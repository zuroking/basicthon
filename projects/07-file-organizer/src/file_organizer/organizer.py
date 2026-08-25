"""Core logic for file organizer.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): every public function here has at least one test.
CLI parsing lives in cli.py and is intentionally excluded from that criterion.

Uses only stdlib (pathlib, shutil).
"""

from __future__ import annotations

import shutil
from pathlib import Path

CATEGORY_MAP: dict[str, set[str]] = {
    "images": {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".svg",
        ".webp",
        ".tiff",
        ".tif",
        ".ico",
        ".heic",
    },
    "documents": {
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".rtf",
        ".odt",
        ".tex",
        ".md",
        ".epub",
        ".csv",
        ".xls",
        ".xlsx",
        ".ods",
        ".ppt",
        ".pptx",
        ".odp",
    },
    "archives": {
        ".zip",
        ".tar",
        ".gz",
        ".tgz",
        ".rar",
        ".7z",
        ".bz2",
        ".xz",
    },
    "audio": {
        ".mp3",
        ".wav",
        ".flac",
        ".aac",
        ".ogg",
        ".m4a",
        ".wma",
        ".aiff",
    },
    "video": {
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".mpeg",
        ".mpg",
    },
    "code": {
        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".java",
        ".c",
        ".cpp",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".sh",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
    },
}

# Reverse lookup extension -> category, built once for fast categorization.
_EXTENSION_TO_CATEGORY: dict[str, str] = {
    ext: category for category, exts in CATEGORY_MAP.items() for ext in exts
}


def get_category(filename: str | Path) -> str:
    """Return category name for a filename based on its extension.

    Case-insensitive. Files without extension or with unknown extension
    return ``"others"``. The input may be a plain filename, a relative
    path or an absolute :class:`pathlib.Path`; only the suffix is used.

    Args:
        filename: file name or path whose extension determines the category.

    Returns:
        Category string, e.g. ``"images"``, ``"documents"``, ``"others"``.

    Examples:
        >>> get_category("photo.JPG")
        'images'
        >>> get_category("archive.tar.gz")
        'archives'
        >>> get_category("README")
        'others'
    """
    suffix = Path(filename).suffix.lower()
    if not suffix:
        return "others"
    return _EXTENSION_TO_CATEGORY.get(suffix, "others")


def _unique_dest(dest_path: Path) -> Path:
    """Return a non-colliding destination path.

    If ``dest_path`` does not exist it is returned as-is. Otherwise a
    numeric suffix ``_1``, ``_2`` … is inserted before the extension
    until an unused name is found.

    Args:
        dest_path: desired destination path.

    Returns:
        Path that does not currently exist.
    """
    if not dest_path.exists():
        return dest_path
    stem = dest_path.stem
    suffix = dest_path.suffix
    parent = dest_path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def organize(
    source: str | Path,
    dest: str | Path,
    *,
    dry_run: bool = False,
) -> dict[str, list[str]]:
    """Organize files from ``source`` into categorized subfolders in ``dest``.

    Scans ``source`` non-recursively (directories are skipped), categorizes
    each file via :func:`get_category`, creates ``dest/<category>/`` folders
    and moves files there. Name collisions in the destination are resolved
    by appending ``_1``, ``_2`` … before the extension.

    Args:
        source: source directory whose top-level files will be organized.
        dest: destination directory where ``<category>/`` subfolders
            are created. Created if it does not exist. May be the same
            as ``source`` to organize in-place.
        dry_run: if ``True`` only report what would be done, do not move
            files or create category folders.

    Returns:
        Mapping ``category -> list of filenames`` that were (or would be)
        moved. Only categories with at least one file appear. Lists
        contain the final file names (after collision renaming, if any).

    Raises:
        FileNotFoundError: if ``source`` does not exist.
        NotADirectoryError: if ``source`` is not a directory or ``dest``
            exists and is not a directory.
    """
    src = Path(source)
    dst = Path(dest)

    if not src.exists():
        raise FileNotFoundError(f"source does not exist: {src}")
    if not src.is_dir():
        raise NotADirectoryError(f"source is not a directory: {src}")
    if dst.exists() and not dst.is_dir():
        raise NotADirectoryError(f"dest is not a directory: {dst}")

    if not dry_run:
        dst.mkdir(parents=True, exist_ok=True)

    # Collect files before any moves, so creating dst subfolders does not
    # affect iteration and so source==dest works predictably.
    files = [p for p in src.iterdir() if p.is_file()]

    result: dict[str, list[str]] = {}

    for file_path in files:
        category = get_category(file_path.name)
        target_dir = dst / category

        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)

        # Compute destination file name, handling collisions only when
        # actually writing (or checking existing dest in dry_run).
        desired = target_dir / file_path.name
        if dry_run:
            # In dry-run we only check current filesystem collisions.
            final = _unique_dest(desired)
        else:
            final = _unique_dest(desired)

        result.setdefault(category, []).append(final.name)

        if not dry_run:
            shutil.move(str(file_path), str(final))

    return result
