"""Light CLI tests — not required for coverage but ensures CLI works."""

from __future__ import annotations

from cli_calculator.cli import parse_args, run_expression


def test_parse_args_expression() -> None:
    args = parse_args(["2 + 2"])
    assert args.expression == "2 + 2"
    assert args.expr_opt is None


def test_parse_args_expr_opt() -> None:
    args = parse_args(["--expr", "3*3"])
    assert args.expr_opt == "3*3"


def test_parse_args_empty() -> None:
    args = parse_args([])
    assert args.expression is None
    assert args.expr_opt is None


def test_run_expression_success(capsys: object) -> None:
    # capsys is pytest fixture; we type as object to keep mypy happy for Foundations
    code = run_expression("2 + 3")
    assert code == 0


def test_run_expression_error() -> None:
    code = run_expression("1 / 0")
    assert code == 1
    code2 = run_expression("bad syntax !!!")
    assert code2 == 1
