"""Tests for file_organizer.organizer — covers every public function."""

# G-13 / GRILL2-05: every public function has at least one test.

from __future__ import annotations

from pathlib import Path

import pytest

from file_organizer.organizer import get_category, organize

# ---- get_category ----


def test_get_category_images() -> None:
    assert get_category("photo.jpg") == "images"
    assert get_category("photo.JPEG") == "images"
    assert get_category("icon.png") == "images"
    assert get_category("anim.gif") == "images"
    assert get_category("image.webp") == "images"
    assert get_category(Path("a/b/c.svg")) == "images"
    assert get_category("picture.BMP") == "images"
    assert get_category("photo.tiff") == "images"


def test_get_category_documents() -> None:
    assert get_category("report.pdf") == "documents"
    assert get_category("doc.docx") == "documents"
    assert get_category("notes.txt") == "documents"
    assert get_category("readme.md") == "documents"
    assert get_category("data.csv") == "documents"
    assert get_category("sheet.xlsx") == "documents"
    assert get_category("slides.pptx") == "documents"


def test_get_category_archives() -> None:
    assert get_category("archive.zip") == "archives"
    assert get_category("backup.tar") == "archives"
    assert get_category("compressed.gz") == "archives"
    assert get_category("data.7z") == "archives"
    assert get_category("bundle.tgz") == "archives"


def test_get_category_audio() -> None:
    assert get_category("song.mp3") == "audio"
    assert get_category("sound.wav") == "audio"
    assert get_category("track.flac") == "audio"
    assert get_category("audio.ogg") == "audio"


def test_get_category_video() -> None:
    assert get_category("movie.mp4") == "video"
    assert get_category("clip.avi") == "video"
    assert get_category("film.mkv") == "video"
    assert get_category("video.webm") == "video"


def test_get_category_code() -> None:
    assert get_category("script.py") == "code"
    assert get_category("app.js") == "code"
    assert get_category("index.html") == "code"
    assert get_category("style.css") == "code"
    assert get_category("config.json") == "code"
    assert get_category("config.yaml") == "code"
    assert get_category("settings.toml") == "code"


def test_get_category_others_unknown() -> None:
    assert get_category("unknown.xyz") == "others"
    assert get_category("file.unknown") == "others"


def test_get_category_no_extension() -> None:
    assert get_category("README") == "others"
    assert get_category("Makefile") == "others"
    assert get_category(Path("no_ext_file")) == "others"


def test_get_category_case_insensitive() -> None:
    assert get_category("PHOTO.JPG") == "images"
    assert get_category("Doc.PDF") == "documents"
    assert get_category("Script.PY") == "code"


def test_get_category_path_objects() -> None:
    assert get_category(Path("a/b/photo.jpg")) == "images"
    assert get_category(Path("/tmp/doc.pdf")) == "documents"
    assert get_category(Path("C:/Users/test/file.mp3")) == "audio"


def test_get_category_hidden_and_double_extension() -> None:
    # suffix is last extension only
    assert get_category("archive.tar.gz") == "archives"
    assert get_category(".hidden") == "others"
    assert get_category(".hidden.txt") == "documents"


# ---- organize ----


def test_organize_basic(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "photo.jpg").write_text("img")
    (src / "doc.pdf").write_text("pdf")
    (src / "song.mp3").write_text("audio")
    (src / "script.py").write_text("code")
    (src / "README").write_text("no ext")

    result = organize(src, dst)

    assert result["images"] == ["photo.jpg"]
    assert result["documents"] == ["doc.pdf"]
    assert result["audio"] == ["song.mp3"]
    assert result["code"] == ["script.py"]
    assert result["others"] == ["README"]

    # files moved
    assert not (src / "photo.jpg").exists()
    assert (dst / "images" / "photo.jpg").exists()
    assert (dst / "documents" / "doc.pdf").exists()
    assert (dst / "audio" / "song.mp3").exists()
    assert (dst / "code" / "script.py").exists()
    assert (dst / "others" / "README").exists()

    # source empty now (only maybe dirs remain but no files)
    assert list(src.iterdir()) == []


def test_organize_dry_run(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "a.jpg").write_text("x")
    (src / "b.txt").write_text("y")

    result = organize(src, dst, dry_run=True)

    assert "images" in result
    assert "documents" in result
    # not moved
    assert (src / "a.jpg").exists()
    assert (src / "b.txt").exists()
    # dest not created or empty
    assert not (dst / "images" / "a.jpg").exists()
    # dry_run should not create category dirs
    assert not (dst / "images").exists()
    assert not (dst / "documents").exists()


def test_organize_collision_rename(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    (dst / "images").mkdir()
    (dst / "images" / "photo.jpg").write_text("existing")
    (src / "photo.jpg").write_text("new")

    result = organize(src, dst)

    assert result["images"] == ["photo_1.jpg"]
    assert (dst / "images" / "photo.jpg").exists()
    assert (dst / "images" / "photo_1.jpg").exists()
    assert not (src / "photo.jpg").exists()
    assert (dst / "images" / "photo_1.jpg").read_text() == "new"


def test_organize_collision_multiple(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    (dst / "documents").mkdir(parents=True)
    (dst / "documents" / "note.txt").write_text("0")
    (dst / "documents" / "note_1.txt").write_text("1")
    (src / "note.txt").write_text("new")

    result = organize(src, dst)

    assert result["documents"] == ["note_2.txt"]
    assert (dst / "documents" / "note_2.txt").exists()


def test_organize_empty_source(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()

    result = organize(src, dst)

    assert result == {}
    assert dst.exists()


def test_organize_skips_directories(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "subdir").mkdir()
    (src / "subdir" / "inner.jpg").write_text("inner")
    (src / "top.png").write_text("top")

    result = organize(src, dst)

    assert result == {"images": ["top.png"]}
    assert (dst / "images" / "top.png").exists()
    # subdir remains, inner not moved
    assert (src / "subdir").exists()
    assert (src / "subdir" / "inner.jpg").exists()


def test_organize_in_place(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.jpg").write_text("img")
    (src / "b.pdf").write_text("pdf")

    result = organize(src, src)

    assert "images" in result
    assert "documents" in result
    assert (src / "images" / "a.jpg").exists()
    assert (src / "documents" / "b.pdf").exists()
    assert not (src / "a.jpg").exists()


def test_organize_string_paths(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "file.py").write_text("x")

    result = organize(str(src), str(dst))

    assert result["code"] == ["file.py"]
    assert (dst / "code" / "file.py").exists()


def test_organize_creates_dest(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "nested" / "dst"
    src.mkdir()
    (src / "song.mp3").write_text("x")

    result = organize(src, dst)

    assert dst.exists()
    assert (dst / "audio" / "song.mp3").exists()
    assert result["audio"] == ["song.mp3"]


def test_organize_case_insensitive_ext(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "PHOTO.JPG").write_text("x")
    (src / "Doc.PDF").write_text("y")

    result = organize(src, dst)

    assert "images" in result
    assert "documents" in result


def test_organize_missing_source(tmp_path: Path) -> None:
    src = tmp_path / "no_such"
    dst = tmp_path / "dst"
    with pytest.raises(FileNotFoundError):
        organize(src, dst)


def test_organize_source_not_dir(tmp_path: Path) -> None:
    src = tmp_path / "file.txt"
    src.write_text("x")
    dst = tmp_path / "dst"
    with pytest.raises(NotADirectoryError):
        organize(src, dst)


def test_organize_dest_is_file(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("x")
    dst = tmp_path / "dst_file"
    dst.write_text("not a dir")
    with pytest.raises(NotADirectoryError):
        organize(src, dst)


def test_organize_dry_run_collision(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    (dst / "code").mkdir()
    (dst / "code" / "app.py").write_text("old")
    (src / "app.py").write_text("new")

    result = organize(src, dst, dry_run=True)

    assert result["code"] == ["app_1.py"]
    # original files untouched
    assert (src / "app.py").exists()
    assert (dst / "code" / "app.py").exists()
    assert not (dst / "code" / "app_1.py").exists()


def test_organize_multiple_categories_counts(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    # 2 images, 1 video, 1 others
    (src / "a.jpg").write_text("x")
    (src / "b.png").write_text("x")
    (src / "c.mp4").write_text("x")
    (src / "d").write_text("x")

    result = organize(src, dst)

    assert len(result["images"]) == 2
    assert len(result["video"]) == 1
    assert len(result["others"]) == 1
    assert sum(len(v) for v in result.values()) == 4
