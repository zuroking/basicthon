"""Core logic for the CLI calculator.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): every public function here has at least one test.
CLI parsing lives in cli.py and is intentionally excluded from that criterion.
"""

from __future__ import annotations

import ast
import operator
from typing import Any, Callable


def add(a: float, b: float) -> float:
    """Return a + b."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Return a - b."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Return a * b."""
    return a * b


def divide(a: float, b: float) -> float:
    """Return a / b.

    Raises:
        ZeroDivisionError: if b is zero.
    """
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return a / b


def power(a: float, b: float) -> float:
    """Return a ** b."""
    return float(a**b)  # type: ignore[no-any-return]


# Mapping of AST operator nodes to actual functions.
_BINARY_OPS: dict[type[ast.operator], Callable[..., Any]] = {  # type: ignore[assignment]
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}

_UNARY_OPS: dict[type[ast.unaryop], Callable[..., Any]] = {  # type: ignore[assignment]
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_node(node: ast.AST) -> float:
    """Recursively evaluate a safe AST node."""
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"unsupported constant type: {type(node.value).__name__}")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BINARY_OPS:
            raise ValueError(f"unsupported binary operator: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if op_type is ast.Div and right == 0:
            raise ZeroDivisionError("division by zero")
        if op_type is ast.FloorDiv and right == 0:
            raise ZeroDivisionError("integer division by zero")
        if op_type is ast.Mod and right == 0:
            raise ZeroDivisionError("modulo by zero")
        return float(_BINARY_OPS[op_type](left, right))  # type: ignore[no-any-return]
    if isinstance(node, ast.UnaryOp):
        unary_op_type = type(node.op)
        if unary_op_type not in _UNARY_OPS:
            raise ValueError(f"unsupported unary operator: {unary_op_type.__name__}")
        operand = _eval_node(node.operand)
        return float(_UNARY_OPS[unary_op_type](operand))  # type: ignore[no-any-return]
    # ast.Num is deprecated but keep for Python <3.11 compatibility in error message
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


def evaluate(expression: str) -> float:
    """Evaluate an arithmetic expression safely.

    Supported: numbers, + - * / // % **, parentheses, unary +/-
    Whitespace is ignored. Uses ast, never eval().

    Args:
        expression: string like "2 + 3 * (4 - 1)".

    Returns:
        Result as float.

    Raises:
        ValueError: on syntax error or unsupported construct.
        ZeroDivisionError: on division by zero.
    """
    if not isinstance(expression, str):
        raise ValueError("expression must be a string")
    stripped = expression.strip()
    if not stripped:
        raise ValueError("empty expression")
    try:
        tree = ast.parse(stripped, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"invalid syntax: {exc.msg}") from exc
    return _eval_node(tree)
