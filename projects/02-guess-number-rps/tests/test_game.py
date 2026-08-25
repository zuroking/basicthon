"""Tests for guess_rps.game — covers every public function."""

from __future__ import annotations

import pytest

from guess_rps.game import check_guess, random_rps_choice, random_secret, rps_result


def test_check_guess() -> None:
    assert check_guess(10, 10) == "correct"
    assert check_guess(10, 5) == "higher"
    assert check_guess(10, 15) == "lower"
    assert check_guess(1, 0) == "higher"


def test_rps_result_win() -> None:
    assert rps_result("rock", "scissors") == "win"
    assert rps_result("scissors", "paper") == "win"
    assert rps_result("paper", "rock") == "win"


def test_rps_result_lose() -> None:
    assert rps_result("rock", "paper") == "lose"
    assert rps_result("paper", "scissors") == "lose"


def test_rps_result_draw() -> None:
    assert rps_result("rock", "rock") == "draw"
    assert rps_result("paper", "paper") == "draw"


def test_rps_result_case_insensitive() -> None:
    assert rps_result("Rock", "SCISSORS") == "win"
    assert rps_result(" PAPER ", "rock") == "win"


def test_rps_result_invalid() -> None:
    with pytest.raises(ValueError, match="invalid player"):
        rps_result("lizard", "rock")
    with pytest.raises(ValueError, match="invalid computer"):
        rps_result("rock", "spock")


def test_random_secret_range() -> None:
    for _ in range(20):
        v = random_secret(1, 5)
        assert 1 <= v <= 5
    with pytest.raises(ValueError, match="low must be"):
        random_secret(10, 1)


def test_random_rps_choice() -> None:
    for _ in range(20):
        assert random_rps_choice() in {"rock", "paper", "scissors"}
