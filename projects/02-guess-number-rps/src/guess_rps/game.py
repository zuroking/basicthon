"""Core logic for guess number and RPS games."""

from __future__ import annotations

import random

VALID_RPS = ("rock", "paper", "scissors")
WIN_MAP: dict[str, str] = {
    "rock": "scissors",
    "scissors": "paper",
    "paper": "rock",
}


def check_guess(secret: int, guess: int) -> str:
    """Compare guess with secret.

    Returns:
        "correct" if equal, "higher" if secret > guess, "lower" otherwise.
    """
    if guess == secret:
        return "correct"
    if guess < secret:
        return "higher"
    return "lower"


def rps_result(player: str, computer: str) -> str:
    """Determine RPS outcome.

    Args:
        player: one of rock/paper/scissors (case-insensitive).
        computer: one of rock/paper/scissors.

    Returns:
        "win", "lose" or "draw".

    Raises:
        ValueError: on invalid choice.
    """
    p = player.lower().strip()
    c = computer.lower().strip()
    if p not in VALID_RPS:
        raise ValueError(f"invalid player choice: {player!r}")
    if c not in VALID_RPS:
        raise ValueError(f"invalid computer choice: {computer!r}")
    if p == c:
        return "draw"
    if WIN_MAP[p] == c:
        return "win"
    return "lose"


def random_secret(low: int = 1, high: int = 100) -> int:
    """Return random secret in [low, high]."""
    if low > high:
        raise ValueError("low must be <= high")
    return random.randint(low, high)


def random_rps_choice() -> str:
    """Return random RPS choice."""
    return random.choice(VALID_RPS)
