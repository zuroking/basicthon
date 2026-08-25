"""Core logic for grades analyzer from CSV.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): every public function here has at least one test.
CLI parsing lives in cli.py and is intentionally excluded from that criterion.

CSV format: header row must contain ``name`` and ``grade`` columns
(``grade`` is required, ``name`` is optional for analytics). Additional
columns (e.g., ``subject``) are preserved in parsed dicts but ignored by
statistics functions. Grades are parsed as ``float`` via ``float()``.

Uses only :mod:`csv` and :mod:`pathlib` from the standard library.
"""

from __future__ import annotations

import csv
from pathlib import Path


def parse_csv(path: str | Path) -> list[dict[str, str]]:
    """Parse CSV file and return list of row dicts.

    Expects header row with at least ``grade`` column. Preserves all columns
    as strings. Empty file or missing header raises ``ValueError``.

    Args:
        path: filesystem path to CSV file.

    Returns:
        List of dicts where each dict maps column name to string value.

    Raises:
        FileNotFoundError: if file does not exist.
        ValueError: if file is empty, missing header, or ``grade`` column absent.
    """
    p = Path(path)
    with p.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or missing header")
        if "grade" not in reader.fieldnames:
            raise ValueError("CSV must contain 'grade' column")
        rows: list[dict[str, str]] = []
        for raw_row in reader:
            cleaned: dict[str, str] = {}
            for key, value in raw_row.items():
                if key is None:
                    continue
                cleaned[key] = value if value is not None else ""
            rows.append(cleaned)
        return rows


def _extract_grades(records: list[dict[str, str]]) -> list[float]:
    """Extract numeric grades from records.

    Args:
        records: list of dicts as returned by :func:`parse_csv`.

    Returns:
        List of grades as floats.

    Raises:
        ValueError: if ``grade`` missing, empty, or not numeric.
    """
    grades: list[float] = []
    for rec in records:
        if "grade" not in rec:
            raise ValueError("record missing 'grade' field")
        raw = rec["grade"]
        # allow int/float already but normalize via str -> float
        text = str(raw).strip()
        if text == "":
            raise ValueError("grade value is empty")
        try:
            val = float(text)
        except ValueError as exc:
            raise ValueError(f"invalid grade value: {raw!r}") from exc
        grades.append(val)
    return grades


def average(records: list[dict[str, str]]) -> float:
    """Compute average grade.

    Args:
        records: list of row dicts with ``grade`` field.

    Returns:
        Average as float. Returns ``0.0`` for empty list.
    """
    grades = _extract_grades(records)
    if not grades:
        return 0.0
    return sum(grades) / len(grades)


def median(records: list[dict[str, str]]) -> float:
    """Compute median grade.

    Args:
        records: list of row dicts with ``grade`` field.

    Returns:
        Median as float. Returns ``0.0`` for empty list.
    """
    grades = _extract_grades(records)
    if not grades:
        return 0.0
    sorted_grades = sorted(grades)
    n = len(sorted_grades)
    mid = n // 2
    if n % 2 == 1:
        return float(sorted_grades[mid])
    return (sorted_grades[mid - 1] + sorted_grades[mid]) / 2.0


def min_grade(records: list[dict[str, str]]) -> float:
    """Return minimum grade.

    Args:
        records: list of row dicts with ``grade`` field.

    Returns:
        Minimum grade as float.

    Raises:
        ValueError: if records is empty.
    """
    grades = _extract_grades(records)
    if not grades:
        raise ValueError("no grades to compute min")
    return min(grades)


def max_grade(records: list[dict[str, str]]) -> float:
    """Return maximum grade.

    Args:
        records: list of row dicts with ``grade`` field.

    Returns:
        Maximum grade as float.

    Raises:
        ValueError: if records is empty.
    """
    grades = _extract_grades(records)
    if not grades:
        raise ValueError("no grades to compute max")
    return max(grades)


def top_n(records: list[dict[str, str]], n: int = 3) -> list[dict[str, str]]:
    """Return top N records sorted descending by grade.

    Stable sort preserves original order for equal grades.

    Args:
        records: list of row dicts with ``grade`` field.
        n: number of top records to return, must be > 0.

    Returns:
        New list with at most ``n`` records, highest grades first.

    Raises:
        ValueError: if ``n`` is not a positive integer.
    """
    if not isinstance(n, int):
        raise ValueError("n must be an integer")
    if n <= 0:
        raise ValueError("n must be positive")
    # validate grades are numeric before sorting (raises ValueError if invalid)
    _extract_grades(records)

    def grade_key(rec: dict[str, str]) -> float:
        return float(str(rec["grade"]).strip())

    sorted_records = sorted(records, key=grade_key, reverse=True)
    return sorted_records[:n]


def grade_distribution(records: list[dict[str, str]]) -> dict[str, int]:
    """Bucket grades into letter ranges A/B/C/D/F.

    Buckets:
        A: 90-100+
        B: 80-89
        C: 70-79
        D: 60-69
        F: <60

    Args:
        records: list of row dicts with ``grade`` field.

    Returns:
        Dict with keys ``A``, ``B``, ``C``, ``D``, ``F`` and counts.
        Empty input returns all zeros.
    """
    buckets: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for grade in _extract_grades(records):
        if grade >= 90:
            buckets["A"] += 1
        elif grade >= 80:
            buckets["B"] += 1
        elif grade >= 70:
            buckets["C"] += 1
        elif grade >= 60:
            buckets["D"] += 1
        else:
            buckets["F"] += 1
    return buckets
