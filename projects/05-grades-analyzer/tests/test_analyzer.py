"""Tests for grades_analyzer.analyzer — covers every public function (G-13/GRILL2-05).

Uses tmp_path for CSV creation as required.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from grades_analyzer.analyzer import (
    average,
    grade_distribution,
    max_grade,
    median,
    min_grade,
    parse_csv,
    top_n,
)


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    """Helper to write CSV for tests."""
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---- parse_csv ----


def test_parse_csv_valid(tmp_path: Path) -> None:
    path = tmp_path / "grades.csv"
    _write_csv(
        path,
        [
            {"name": "Alice", "grade": "95"},
            {"name": "Bob", "grade": "82"},
            {"name": "Cara", "grade": "67"},
        ],
        fieldnames=["name", "grade"],
    )
    rows = parse_csv(path)
    assert len(rows) == 3
    assert rows[0] == {"name": "Alice", "grade": "95"}
    assert rows[1]["grade"] == "82"
    # str path variant
    assert parse_csv(str(path)) == rows


def test_parse_csv_extra_column_preserved(tmp_path: Path) -> None:
    path = tmp_path / "grades.csv"
    _write_csv(
        path,
        [{"name": "Ann", "grade": "90", "subject": "math"}],
        fieldnames=["name", "grade", "subject"],
    )
    rows = parse_csv(path)
    assert rows[0]["subject"] == "math"


def test_parse_csv_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "nope.csv"
    with pytest.raises(FileNotFoundError):
        parse_csv(path)


def test_parse_csv_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty or missing header"):
        parse_csv(path)


def test_parse_csv_only_header(tmp_path: Path) -> None:
    path = tmp_path / "header_only.csv"
    path.write_text("name,grade\n", encoding="utf-8")
    rows = parse_csv(path)
    assert rows == []


def test_parse_csv_missing_grade_column(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    _write_csv(
        path,
        [{"name": "Alice", "score": "90"}],
        fieldnames=["name", "score"],
    )
    with pytest.raises(ValueError, match="must contain 'grade'"):
        parse_csv(path)


def test_parse_csv_header_case_sensitive(tmp_path: Path) -> None:
    path = tmp_path / "case.csv"
    path.write_text("Name,Grade\nAlice,90\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must contain 'grade'"):
        parse_csv(path)


# ---- average ----


def test_average_empty() -> None:
    assert average([]) == 0.0


def test_average_single(tmp_path: Path) -> None:
    path = tmp_path / "single.csv"
    _write_csv(path, [{"name": "A", "grade": "80"}], fieldnames=["name", "grade"])
    rows = parse_csv(path)
    assert average(rows) == 80.0


def test_average_multiple(tmp_path: Path) -> None:
    path = tmp_path / "grades.csv"
    _write_csv(
        path,
        [
            {"name": "A", "grade": "90"},
            {"name": "B", "grade": "80"},
            {"name": "C", "grade": "70"},
        ],
        fieldnames=["name", "grade"],
    )
    rows = parse_csv(path)
    assert average(rows) == pytest.approx(80.0)


def test_average_float_grades() -> None:
    rows = [{"grade": "85.5"}, {"grade": "90.5"}]
    assert average(rows) == pytest.approx(88.0)


def test_average_invalid_grade_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    _write_csv(
        path,
        [{"name": "A", "grade": "not-a-number"}],
        fieldnames=["name", "grade"],
    )
    rows = parse_csv(path)
    with pytest.raises(ValueError, match="invalid grade"):
        average(rows)


def test_average_missing_grade_field() -> None:
    with pytest.raises(ValueError, match="missing 'grade'"):
        average([{"name": "Alice"}])  # type: ignore[arg-type]  # intentionally missing grade


# ---- median ----


def test_median_empty() -> None:
    assert median([]) == 0.0


def test_median_odd(tmp_path: Path) -> None:
    path = tmp_path / "grades.csv"
    _write_csv(
        path,
        [
            {"name": "A", "grade": "90"},
            {"name": "B", "grade": "70"},
            {"name": "C", "grade": "80"},
        ],
        fieldnames=["name", "grade"],
    )
    rows = parse_csv(path)
    # sorted 70,80,90 -> median 80
    assert median(rows) == 80.0


def test_median_even() -> None:
    rows = [{"grade": "80"}, {"grade": "90"}, {"grade": "70"}, {"grade": "60"}]
    # sorted 60,70,80,90 -> median (70+80)/2 =75
    assert median(rows) == 75.0


def test_median_single() -> None:
    assert median([{"grade": "88"}]) == 88.0


def test_median_unsorted_input(tmp_path: Path) -> None:
    path = tmp_path / "grades.csv"
    _write_csv(
        path,
        [{"name": "B", "grade": "100"}, {"name": "A", "grade": "60"}],
        fieldnames=["name", "grade"],
    )
    rows = parse_csv(path)
    assert median(rows) == 80.0


# ---- min_grade / max_grade ----


def test_min_grade_normal(tmp_path: Path) -> None:
    path = tmp_path / "grades.csv"
    _write_csv(
        path,
        [
            {"name": "A", "grade": "95"},
            {"name": "B", "grade": "60"},
            {"name": "C", "grade": "80"},
        ],
        fieldnames=["name", "grade"],
    )
    rows = parse_csv(path)
    assert min_grade(rows) == 60.0
    assert max_grade(rows) == 95.0


def test_min_max_single() -> None:
    rows = [{"grade": "77"}]
    assert min_grade(rows) == 77.0
    assert max_grade(rows) == 77.0


def test_min_grade_empty_raises() -> None:
    with pytest.raises(ValueError, match="no grades"):
        min_grade([])


def test_max_grade_empty_raises() -> None:
    with pytest.raises(ValueError, match="no grades"):
        max_grade([])


def test_min_grade_float_string() -> None:
    rows = [{"grade": "  82.5 "}, {"grade": "90"}]
    assert min_grade(rows) == 82.5


# ---- top_n ----


def test_top_n_normal(tmp_path: Path) -> None:
    path = tmp_path / "grades.csv"
    _write_csv(
        path,
        [
            {"name": "Alice", "grade": "95"},
            {"name": "Bob", "grade": "82"},
            {"name": "Cara", "grade": "91"},
            {"name": "Dan", "grade": "70"},
        ],
        fieldnames=["name", "grade"],
    )
    rows = parse_csv(path)
    top = top_n(rows, n=2)
    assert len(top) == 2
    assert top[0]["name"] == "Alice"
    assert top[1]["name"] == "Cara"
    # ensure sorted descending
    assert float(top[0]["grade"]) >= float(top[1]["grade"])


def test_top_n_default_is_3() -> None:
    rows = [{"name": "A", "grade": "90"}, {"name": "B", "grade": "80"}]
    assert len(top_n(rows)) == 2


def test_top_n_larger_than_len() -> None:
    rows = [{"grade": "90"}, {"grade": "80"}]
    assert len(top_n(rows, n=10)) == 2


def test_top_n_stable_for_equal_grades(tmp_path: Path) -> None:
    path = tmp_path / "grades.csv"
    _write_csv(
        path,
        [
            {"name": "A", "grade": "90"},
            {"name": "B", "grade": "90"},
            {"name": "C", "grade": "80"},
        ],
        fieldnames=["name", "grade"],
    )
    rows = parse_csv(path)
    top = top_n(rows, n=2)
    # stable: original order for equal grades
    assert top[0]["name"] == "A"
    assert top[1]["name"] == "B"


def test_top_n_invalid_n_zero() -> None:
    with pytest.raises(ValueError, match="positive"):
        top_n([{"grade": "90"}], n=0)


def test_top_n_invalid_n_negative() -> None:
    with pytest.raises(ValueError, match="positive"):
        top_n([{"grade": "90"}], n=-1)


def test_top_n_invalid_n_type() -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        top_n([{"grade": "90"}], n="2")  # type: ignore[arg-type]


def test_top_n_empty_returns_empty() -> None:
    assert top_n([], n=3) == []


def test_top_n_with_float_grades() -> None:
    rows = [{"name": "A", "grade": "90.5"}, {"name": "B", "grade": "90.1"}]
    top = top_n(rows, n=1)
    assert top[0]["name"] == "A"


# ---- grade_distribution ----


def test_grade_distribution_empty() -> None:
    assert grade_distribution([]) == {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}


def test_grade_distribution_mixed(tmp_path: Path) -> None:
    path = tmp_path / "grades.csv"
    _write_csv(
        path,
        [
            {"name": "A", "grade": "95"},  # A
            {"name": "B", "grade": "85"},  # B
            {"name": "C", "grade": "75"},  # C
            {"name": "D", "grade": "65"},  # D
            {"name": "E", "grade": "55"},  # F
            {"name": "F", "grade": "90"},  # A boundary
            {"name": "G", "grade": "80"},  # B boundary
        ],
        fieldnames=["name", "grade"],
    )
    rows = parse_csv(path)
    dist = grade_distribution(rows)
    assert dist == {"A": 2, "B": 2, "C": 1, "D": 1, "F": 1}


def test_grade_distribution_boundaries() -> None:
    rows = [
        {"grade": "90"},
        {"grade": "89.9"},
        {"grade": "80"},
        {"grade": "79.9"},
        {"grade": "70"},
        {"grade": "69.9"},
        {"grade": "60"},
        {"grade": "59.9"},
    ]
    dist = grade_distribution(rows)
    assert dist["A"] == 1  # 90
    assert dist["B"] == 2  # 89.9,80
    assert dist["C"] == 2  # 79.9,70
    assert dist["D"] == 2  # 69.9,60
    assert dist["F"] == 1  # 59.9


def test_grade_distribution_all_same(tmp_path: Path) -> None:
    path = tmp_path / "grades.csv"
    _write_csv(path, [{"name": "A", "grade": "100"}] * 3, fieldnames=["name", "grade"])
    rows = parse_csv(path)
    assert grade_distribution(rows) == {"A": 3, "B": 0, "C": 0, "D": 0, "F": 0}


# ---- integration ----


def test_integration_parse_and_stats(tmp_path: Path) -> None:
    path = tmp_path / "grades.csv"
    _write_csv(
        path,
        [
            {"name": "Alice", "grade": "95"},
            {"name": "Bob", "grade": "82"},
            {"name": "Cara", "grade": "91"},
            {"name": "Dan", "grade": "60"},
            {"name": "Eve", "grade": "58"},
        ],
        fieldnames=["name", "grade"],
    )
    rows = parse_csv(path)
    assert average(rows) == pytest.approx((95 + 82 + 91 + 60 + 58) / 5)
    assert median(rows) == 82.0  # sorted 58,60,82,91,95
    assert min_grade(rows) == 58.0
    assert max_grade(rows) == 95.0
    assert grade_distribution(rows) == {"A": 2, "B": 1, "C": 0, "D": 1, "F": 1}
    top = top_n(rows, n=2)
    assert [r["name"] for r in top] == ["Alice", "Cara"]
