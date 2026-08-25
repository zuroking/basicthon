"""Tests for duplicate_finder.finder — covers every public function."""

# G-13 / GRILL2-05: every public function has at least one test.

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from duplicate_finder.finder import find_duplicates, hash_file

# ---- hash_file ----


def test_hash_file_basic(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("hello")
    expected = hashlib.sha256(b"hello").hexdigest()
    assert hash_file(f) == expected


def test_hash_file_string_path(tmp_path: Path) -> None:
    f = tmp_path / "b.txt"
    f.write_text("world")
    expected = hashlib.sha256(b"world").hexdigest()
    assert hash_file(str(f)) == expected


def test_hash_file_empty(tmp_path: Path) -> None:
    f = tmp_path / "empty.txt"
    f.write_bytes(b"")
    expected = hashlib.sha256(b"").hexdigest()
    assert hash_file(f) == expected
    assert expected == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )


def test_hash_file_binary(tmp_path: Path) -> None:
    f = tmp_path / "bin.dat"
    data = bytes(range(256))
    f.write_bytes(data)
    expected = hashlib.sha256(data).hexdigest()
    assert hash_file(f) == expected


def test_hash_file_chunked(tmp_path: Path) -> None:
    f = tmp_path / "large.bin"
    data = b"a" * 20000
    f.write_bytes(data)
    expected = hashlib.sha256(data).hexdigest()
    # small chunk size forces multiple reads
    assert hash_file(f, chunk_size=1024) == expected
    assert hash_file(f, chunk_size=1) == expected
    assert hash_file(f, chunk_size=8192) == expected


def test_hash_file_same_content_same_hash(tmp_path: Path) -> None:
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f1.write_text("duplicate")
    f2.write_text("duplicate")
    assert hash_file(f1) == hash_file(f2)


def test_hash_file_different_content_different_hash(tmp_path: Path) -> None:
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f1.write_text("content one")
    f2.write_text("content two")
    assert hash_file(f1) != hash_file(f2)


def test_hash_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        hash_file(tmp_path / "nope.txt")


def test_hash_file_is_directory(tmp_path: Path) -> None:
    with pytest.raises(IsADirectoryError):
        hash_file(tmp_path)


def test_hash_file_invalid_chunk_size(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("x")
    with pytest.raises(ValueError):
        hash_file(f, chunk_size=0)
    with pytest.raises(ValueError):
        hash_file(f, chunk_size=-1)


def test_hash_file_path_object(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    f = sub / "nested.txt"
    f.write_text("nested")
    expected = hashlib.sha256(b"nested").hexdigest()
    assert hash_file(Path(f)) == expected


# ---- find_duplicates ----


def test_find_duplicates_basic(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("same")
    (tmp_path / "b.txt").write_text("same")
    (tmp_path / "c.txt").write_text("different")

    result = find_duplicates(tmp_path)

    assert len(result) == 1
    # only one group
    group = next(iter(result.values()))
    assert len(group) == 2
    names = sorted(p.name for p in group)
    assert names == ["a.txt", "b.txt"]
    # hash is correct
    expected_hash = hashlib.sha256(b"same").hexdigest()
    assert expected_hash in result


def test_find_duplicates_no_duplicates(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("one")
    (tmp_path / "b.txt").write_text("two")
    (tmp_path / "c.txt").write_text("three")

    result = find_duplicates(tmp_path)
    assert result == {}


def test_find_duplicates_empty_dir(tmp_path: Path) -> None:
    result = find_duplicates(tmp_path)
    assert result == {}


def test_find_duplicates_three_way(tmp_path: Path) -> None:
    for name in ["a.txt", "b.txt", "c.txt"]:
        (tmp_path / name).write_text("identical")
    (tmp_path / "unique.txt").write_text("unique")

    result = find_duplicates(tmp_path)
    assert len(result) == 1
    group = next(iter(result.values()))
    assert len(group) == 3
    assert sorted(p.name for p in group) == ["a.txt", "b.txt", "c.txt"]


def test_find_duplicates_multiple_groups(tmp_path: Path) -> None:
    (tmp_path / "a1.txt").write_text("group1")
    (tmp_path / "a2.txt").write_text("group1")
    (tmp_path / "b1.txt").write_text("group2")
    (tmp_path / "b2.txt").write_text("group2")
    (tmp_path / "solo.txt").write_text("solo")

    result = find_duplicates(tmp_path)
    assert len(result) == 2
    all_names = sorted(p.name for paths in result.values() for p in paths)
    assert all_names == ["a1.txt", "a2.txt", "b1.txt", "b2.txt"]
    for paths in result.values():
        assert len(paths) == 2


def test_find_duplicates_recursive(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "top.txt").write_text("dup")
    (sub / "nested.txt").write_text("dup")
    (sub / "other.txt").write_text("other")

    # recursive should find cross-directory duplicates
    result_recursive = find_duplicates(tmp_path, recursive=True)
    assert len(result_recursive) == 1
    group = next(iter(result_recursive.values()))
    assert len(group) == 2

    # non-recursive should not see nested file
    result_flat = find_duplicates(tmp_path, recursive=False)
    assert result_flat == {}


def test_find_duplicates_non_recursive_same_dir(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("same")
    (tmp_path / "b.txt").write_text("same")
    result = find_duplicates(tmp_path, recursive=False)
    assert len(result) == 1
    group = next(iter(result.values()))
    assert len(group) == 2


def test_find_duplicates_nested_only(tmp_path: Path) -> None:
    sub1 = tmp_path / "sub1"
    sub2 = tmp_path / "sub2"
    sub1.mkdir()
    sub2.mkdir()
    (sub1 / "file.txt").write_text("hello")
    (sub2 / "file.txt").write_text("hello")

    result = find_duplicates(tmp_path, recursive=True)
    assert len(result) == 1
    group = next(iter(result.values()))
    assert len(group) == 2


def test_find_duplicates_ignores_empty_vs_non_empty(tmp_path: Path) -> None:
    (tmp_path / "empty1.txt").write_bytes(b"")
    (tmp_path / "empty2.txt").write_bytes(b"")
    (tmp_path / "nonempty.txt").write_text("x")

    result = find_duplicates(tmp_path)
    assert len(result) == 1
    empty_hash = hashlib.sha256(b"").hexdigest()
    assert empty_hash in result
    assert len(result[empty_hash]) == 2


def test_find_duplicates_string_path(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("data")
    (tmp_path / "b.txt").write_text("data")

    result = find_duplicates(str(tmp_path))
    assert len(result) == 1


def test_find_duplicates_sorted_output(tmp_path: Path) -> None:
    (tmp_path / "z.txt").write_text("same")
    (tmp_path / "a.txt").write_text("same")
    (tmp_path / "m.txt").write_text("same")

    result = find_duplicates(tmp_path)
    group = next(iter(result.values()))
    # group should be sorted by path string
    assert group == sorted(group)
    assert [p.name for p in group] == ["a.txt", "m.txt", "z.txt"]


def test_find_duplicates_binary_files(tmp_path: Path) -> None:
    data = bytes(range(256))
    (tmp_path / "a.bin").write_bytes(data)
    (tmp_path / "b.bin").write_bytes(data)
    (tmp_path / "c.bin").write_bytes(b"different")

    result = find_duplicates(tmp_path)
    assert len(result) == 1
    expected_hash = hashlib.sha256(data).hexdigest()
    assert expected_hash in result
    assert len(result[expected_hash]) == 2


def test_find_duplicates_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        find_duplicates(tmp_path / "missing")


def test_find_duplicates_not_a_directory(tmp_path: Path) -> None:
    f = tmp_path / "file.txt"
    f.write_text("x")
    with pytest.raises(NotADirectoryError):
        find_duplicates(f)


def test_find_duplicates_ignores_directories(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "a.txt").write_text("content")
    (tmp_path / "b.txt").write_text("content")

    result = find_duplicates(tmp_path, recursive=False)
    # should still find duplicates despite presence of subdir
    assert len(result) == 1
    group = next(iter(result.values()))
    assert len(group) == 2


def test_find_duplicates_large_file(tmp_path: Path) -> None:
    data = b"x" * 50000
    (tmp_path / "large1.bin").write_bytes(data)
    (tmp_path / "large2.bin").write_bytes(data)

    result = find_duplicates(tmp_path)
    assert len(result) == 1
    expected_hash = hashlib.sha256(data).hexdigest()
    assert expected_hash in result
