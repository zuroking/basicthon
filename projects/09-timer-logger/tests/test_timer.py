"""Tests for timer_logger.timer — covers every public function."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from timer_logger.timer import (
    Timer,
    clear_logs,
    format_elapsed,
    log_elapsed,
    log_message,
    read_logs,
)

# ---- Timer start/stop/elapsed ----


def test_timer_start_stop_with_mock() -> None:
    with patch("timer_logger.timer.time.perf_counter", side_effect=[100.0, 102.5]):
        t = Timer(label="test")
        t.start()
        assert t.is_running is True
        elapsed = t.stop()
        assert elapsed == pytest.approx(2.5)
        assert t.is_running is False
        # elapsed property supports both access styles
        assert float(t.elapsed) == pytest.approx(2.5)
        assert t.elapsed() == pytest.approx(2.5)  # type: ignore[operator]


def test_timer_elapsed_while_running() -> None:
    with patch(
        "timer_logger.timer.time.perf_counter", side_effect=[100.0, 101.0, 101.0, 103.0]
    ):
        t = Timer()
        t.start()  # 100.0
        # elapsed while running should compute 101.0 - 100.0 = 1.0
        assert float(t.elapsed) == pytest.approx(1.0)
        assert t.elapsed() == pytest.approx(1.0)  # type: ignore[operator]
        # stop at 103.0 -> total 3.0
        assert t.stop() == pytest.approx(3.0)


def test_timer_elapsed_before_start() -> None:
    t = Timer()
    assert float(t.elapsed) == 0.0
    assert t.elapsed() == pytest.approx(0.0)  # type: ignore[operator]


def test_timer_double_start_raises() -> None:
    with patch("timer_logger.timer.time.perf_counter", return_value=100.0):
        t = Timer()
        t.start()
        with pytest.raises(RuntimeError, match="already running"):
            t.start()
        # cleanup
        with patch("timer_logger.timer.time.perf_counter", return_value=101.0):
            t.stop()


def test_timer_stop_without_start_raises() -> None:
    t = Timer()
    with pytest.raises(RuntimeError, match="not running"):
        t.stop()


def test_timer_stop_twice_raises() -> None:
    with patch("timer_logger.timer.time.perf_counter", side_effect=[100.0, 101.0]):
        t = Timer()
        t.start()
        t.stop()
        with pytest.raises(RuntimeError, match="not running"):
            t.stop()


def test_timer_is_running_property() -> None:
    t = Timer()
    assert t.is_running is False
    with patch("timer_logger.timer.time.perf_counter", return_value=1.0):
        t.start()
        assert t.is_running is True
    with patch("timer_logger.timer.time.perf_counter", return_value=2.0):
        t.stop()
        assert t.is_running is False


def test_timer_reset() -> None:
    with patch("timer_logger.timer.time.perf_counter", side_effect=[10.0, 12.0]):
        t = Timer()
        t.start()
        t.stop()
        assert float(t.elapsed) == pytest.approx(2.0)
        t.reset()
        assert float(t.elapsed) == 0.0
        assert t.is_running is False
        # after reset can start again
        with patch("timer_logger.timer.time.perf_counter", side_effect=[20.0, 23.0]):
            t.start()
            assert t.stop() == pytest.approx(3.0)


def test_timer_reset_while_running() -> None:
    with patch("timer_logger.timer.time.perf_counter", return_value=5.0):
        t = Timer()
        t.start()
        assert t.is_running is True
        t.reset()
        assert t.is_running is False
        assert float(t.elapsed) == 0.0
        with pytest.raises(RuntimeError):
            t.stop()


def test_timer_repr() -> None:
    t = Timer(label="mylabel")
    r = repr(t)
    assert "Timer" in r
    assert "mylabel" in r
    assert "elapsed" in r

    with patch("timer_logger.timer.time.perf_counter", side_effect=[0.0, 1.5]):
        t.start()
        t.stop()
        r2 = repr(t)
        assert "1.500000" in r2 or "1.5" in r2


def test_timer_context_manager_with_mock() -> None:
    with patch("timer_logger.timer.time.perf_counter", side_effect=[100.0, 105.0]):
        with Timer(label="ctx") as t:
            assert t.is_running is True
            # elapsed while inside should be computed
            with patch("timer_logger.timer.time.perf_counter", return_value=102.0):
                assert float(t.elapsed) == pytest.approx(2.0)
        # after exit, stopped
        assert t.is_running is False
        assert float(t.elapsed) == pytest.approx(5.0)


def test_timer_context_manager_exception_still_stops() -> None:
    with patch("timer_logger.timer.time.perf_counter", side_effect=[10.0, 12.0]):
        t = Timer()
        try:
            with t:
                assert t.is_running is True
                raise ValueError("boom")
        except ValueError:
            pass
        assert t.is_running is False
        assert float(t.elapsed) == pytest.approx(2.0)


def test_timer_context_manager_with_log_file(tmp_path: Path) -> None:
    log = tmp_path / "timer.log"
    with patch("timer_logger.timer.time.perf_counter", side_effect=[1.0, 3.0]):
        with Timer(label="logged", log_file=log) as t:
            pass
        assert t.is_running is False
    # file should exist and contain label and elapsed
    content = log.read_text(encoding="utf-8")
    assert "logged" in content
    assert "2.000000" in content
    # read_logs helper should see it
    lines = read_logs(log)
    assert len(lines) == 1
    assert "logged" in lines[0]


def test_timer_stop_logs_to_file(tmp_path: Path) -> None:
    log = tmp_path / "subdir" / "a.log"
    with patch("timer_logger.timer.time.perf_counter", side_effect=[10.0, 11.5]):
        t = Timer(label="mytask", log_file=log)
        t.start()
        elapsed = t.stop()
        assert elapsed == pytest.approx(1.5)
    assert log.exists()
    text = log.read_text(encoding="utf-8")
    assert "mytask" in text
    assert "1.500000" in text


def test_timer_log_file_as_string(tmp_path: Path) -> None:
    log = tmp_path / "str.log"
    with patch("timer_logger.timer.time.perf_counter", side_effect=[0.0, 2.0]):
        t = Timer(label="s", log_file=str(log))
        t.start()
        t.stop()
    assert log.exists()


def test_timer_without_log_file_does_not_create_file(tmp_path: Path) -> None:
    log = tmp_path / "should_not_exist.log"
    with patch("timer_logger.timer.time.perf_counter", side_effect=[0.0, 1.0]):
        t = Timer(label="no_log")
        t.start()
        t.stop()
    assert not log.exists()


def test_timer_label_none_default(tmp_path: Path) -> None:
    log = tmp_path / "default.log"
    with patch("timer_logger.timer.time.perf_counter", side_effect=[0.0, 1.0]):
        t = Timer(log_file=log)
        t.start()
        t.stop()
    assert "Timer" in log.read_text(encoding="utf-8")


# ---- format_elapsed ----


def test_format_elapsed_basic() -> None:
    assert format_elapsed(0) == "0.000s"
    assert format_elapsed(0.001) == "0.001s"
    assert format_elapsed(1.234) == "1.234s"
    assert format_elapsed(59.999) == "59.999s"


def test_format_elapsed_minutes() -> None:
    assert format_elapsed(60) == "1m 0.000s"
    assert format_elapsed(61.5) == "1m 1.500s"
    assert format_elapsed(90.123) == "1m 30.123s"
    assert format_elapsed(3599.9) == "59m 59.900s"


def test_format_elapsed_hours() -> None:
    assert format_elapsed(3600) == "1h 0m 0.000s"
    assert format_elapsed(3661.5) == "1h 1m 1.500s"
    assert format_elapsed(7325.678) == "2h 2m 5.678s"


def test_format_elapsed_negative_raises() -> None:
    with pytest.raises(ValueError):
        format_elapsed(-1)
    with pytest.raises(ValueError):
        format_elapsed(-0.001)


def test_format_elapsed_non_finite_raises() -> None:
    with pytest.raises(ValueError):
        format_elapsed(float("inf"))
    with pytest.raises(ValueError):
        format_elapsed(float("-inf"))
    with pytest.raises(ValueError):
        format_elapsed(float("nan"))


def test_format_elapsed_int_input() -> None:
    assert format_elapsed(5) == "5.000s"
    assert format_elapsed(120) == "2m 0.000s"


def test_format_elapsed_invalid_type() -> None:
    with pytest.raises(ValueError):
        format_elapsed("abc")  # type: ignore[arg-type]


# ---- log_message ----


def test_log_message_basic(tmp_path: Path) -> None:
    log = tmp_path / "msg.log"
    log_message("hello", log)
    lines = read_logs(log)
    assert len(lines) == 1
    assert "hello" in lines[0]
    # second message appends
    log_message("world", log)
    lines = read_logs(log)
    assert len(lines) == 2
    assert "world" in lines[1]


def test_log_message_string_path(tmp_path: Path) -> None:
    log = tmp_path / "str.log"
    log_message("hi", str(log))
    assert "hi" in read_logs(log)[0]


def test_log_message_creates_parent_dirs(tmp_path: Path) -> None:
    log = tmp_path / "a" / "b" / "c.log"
    log_message("deep", log)
    assert log.exists()
    assert "deep" in log.read_text(encoding="utf-8")


def test_log_message_is_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(IsADirectoryError):
        log_message("hi", tmp_path)


def test_log_message_invalid_message_type(tmp_path: Path) -> None:
    log = tmp_path / "x.log"
    with pytest.raises(ValueError):
        log_message(123, log)  # type: ignore[arg-type]


# ---- log_elapsed ----


def test_log_elapsed_basic(tmp_path: Path) -> None:
    log = tmp_path / "elapsed.log"
    log_elapsed("task", 1.5, log)
    lines = read_logs(log)
    assert len(lines) == 1
    assert "task" in lines[0]
    assert "1.500s" in lines[0]


def test_log_elapsed_string_path(tmp_path: Path) -> None:
    log = tmp_path / "s.log"
    log_elapsed("lbl", 60, str(log))
    assert "1m 0.000s" in read_logs(str(log))[0]


def test_log_elapsed_empty_label_raises(tmp_path: Path) -> None:
    log = tmp_path / "x.log"
    with pytest.raises(ValueError):
        log_elapsed("", 1.0, log)
    with pytest.raises(ValueError):
        log_elapsed("   ", 1.0, log)


def test_log_elapsed_invalid_seconds_raises(tmp_path: Path) -> None:
    log = tmp_path / "x.log"
    with pytest.raises(ValueError):
        log_elapsed("t", -1, log)
    with pytest.raises(ValueError):
        log_elapsed("t", float("inf"), log)


def test_log_elapsed_is_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(IsADirectoryError):
        log_elapsed("t", 1.0, tmp_path)


# ---- read_logs ----


def test_read_logs_missing_returns_empty(tmp_path: Path) -> None:
    assert read_logs(tmp_path / "nope.log") == []


def test_read_logs_is_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(IsADirectoryError):
        read_logs(tmp_path)


def test_read_logs_content(tmp_path: Path) -> None:
    log = tmp_path / "a.log"
    log.write_text("line1\nline2\n", encoding="utf-8")
    assert read_logs(log) == ["line1", "line2"]
    # string path
    assert read_logs(str(log)) == ["line1", "line2"]


def test_read_logs_empty_file(tmp_path: Path) -> None:
    log = tmp_path / "empty.log"
    log.write_text("", encoding="utf-8")
    assert read_logs(log) == []


# ---- clear_logs ----


def test_clear_logs_basic(tmp_path: Path) -> None:
    log = tmp_path / "c.log"
    log.write_text("hello\nworld\n", encoding="utf-8")
    assert len(read_logs(log)) == 2
    clear_logs(log)
    assert read_logs(log) == []
    assert log.exists()
    assert log.read_text(encoding="utf-8") == ""


def test_clear_logs_creates_file(tmp_path: Path) -> None:
    log = tmp_path / "new" / "c.log"
    clear_logs(log)
    assert log.exists()
    assert read_logs(log) == []
    # string path
    clear_logs(str(log))
    assert read_logs(log) == []


def test_clear_logs_is_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(IsADirectoryError):
        clear_logs(tmp_path)


def test_clear_logs_idempotent(tmp_path: Path) -> None:
    log = tmp_path / "id.log"
    clear_logs(log)
    clear_logs(log)
    assert read_logs(log) == []
