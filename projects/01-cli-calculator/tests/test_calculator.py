"""Tests for calculator — covers every public function (G-13/GRILL2-05)."""

from __future__ import annotations

import pytest

from cli_calculator.calculator import add, divide, evaluate, multiply, power, subtract


def test_add() -> None:
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0.1, 0.2) == pytest.approx(0.3)


def test_subtract() -> None:
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5
    assert subtract(-1, -1) == 0


def test_multiply() -> None:
    assert multiply(3, 4) == 12
    assert multiply(-2, 3) == -6
    assert multiply(0, 100) == 0


def test_divide() -> None:
    assert divide(6, 3) == 2
    assert divide(5, 2) == 2.5
    assert divide(-6, 2) == -3


def test_divide_by_zero() -> None:
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        divide(1, 0)


def test_power() -> None:
    assert power(2, 3) == 8
    assert power(5, 0) == 1
    assert power(9, 0.5) == pytest.approx(3.0)


def test_evaluate_simple() -> None:
    assert evaluate("2 + 3") == 5
    assert evaluate("5 - 2") == 3
    assert evaluate("3 * 4") == 12
    assert evaluate("6 / 3") == 2


def test_evaluate_precedence() -> None:
    assert evaluate("2 + 3 * 4") == 14
    assert evaluate("(2 + 3) * 4") == 20
    assert evaluate("2 * 3 + 4 * 5") == 26


def test_evaluate_with_spaces_and_floats() -> None:
    assert evaluate("  2.5 + 0.5 ") == 3.0
    assert evaluate("10 / 4") == 2.5


def test_evaluate_unary() -> None:
    assert evaluate("-3 + 5") == 2
    assert evaluate("+-2") == -2
    assert evaluate("--2") == 2
    assert evaluate("-(2 + 3)") == -5


def test_evaluate_power_mod_floor() -> None:
    assert evaluate("2 ** 3") == 8
    assert evaluate("10 % 3") == 1
    assert evaluate("7 // 2") == 3


def test_evaluate_division_by_zero() -> None:
    with pytest.raises(ZeroDivisionError):
        evaluate("1 / 0")
    with pytest.raises(ZeroDivisionError):
        evaluate("5 // 0")
    with pytest.raises(ZeroDivisionError):
        evaluate("5 % 0")


def test_evaluate_errors() -> None:
    with pytest.raises(ValueError, match="empty expression"):
        evaluate("   ")
    with pytest.raises(ValueError, match="empty expression"):
        evaluate("")
    with pytest.raises(ValueError, match="must be a string"):
        evaluate(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invalid syntax"):
        evaluate("2 +")
    with pytest.raises(ValueError, match="unsupported"):
        evaluate("__import__('os').system('echo bad')")
    with pytest.raises(ValueError, match="unsupported"):
        evaluate("2 & 3")


def test_evaluate_nested_parens() -> None:
    assert evaluate("((1 + 2) * (3 + 4)) / 7") == pytest.approx(3.0)
    assert evaluate("2 ** (1 + 1)") == 4
