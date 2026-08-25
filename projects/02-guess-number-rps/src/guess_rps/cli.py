"""CLI for guess number and RPS games (excluded from coverage criterion)."""

from __future__ import annotations

import argparse
import sys

from guess_rps.game import check_guess, random_rps_choice, random_secret, rps_result


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="guess-rps",
        description="Угадай число и камень-ножницы-бумага",
    )
    parser.add_argument(
        "--mode",
        choices=["guess", "rps"],
        default="guess",
        help="режим игры (по умолчанию guess)",
    )
    parser.add_argument(
        "--low",
        type=int,
        default=1,
        help="нижняя граница для guess (по умолчанию 1)",
    )
    parser.add_argument(
        "--high",
        type=int,
        default=100,
        help="верхняя граница для guess (по умолчанию 100)",
    )
    return parser.parse_args(argv)


def run_guess(low: int, high: int) -> None:
    """Interactive guess game."""
    secret = random_secret(low, high)
    print(f"Я загадал число от {low} до {high}. Попробуй угадать! (q для выхода)")
    attempts = 0
    while True:
        raw = input("Ваше число: ").strip()
        if raw.lower() in {"q", "quit", "exit"}:
            print(f"Было загадано {secret}. Пока!")
            break
        try:
            guess = int(raw)
        except ValueError:
            print("Введите целое число.")
            continue
        attempts += 1
        res = check_guess(secret, guess)
        if res == "correct":
            print(f"Верно! За {attempts} попыток.")
            break
        if res == "higher":
            print("Больше!")
        else:
            print("Меньше!")


def run_rps() -> None:
    """Interactive RPS game."""
    print("Камень-ножницы-бумага! Введите rock/paper/scissors (q для выхода)")
    while True:
        raw = input("Ваш ход: ").strip().lower()
        if raw in {"q", "quit", "exit"}:
            print("Пока!")
            break
        if raw not in {"rock", "paper", "scissors"}:
            print("Допустимо: rock, paper, scissors")
            continue
        comp = random_rps_choice()
        result = rps_result(raw, comp)
        print(f"Компьютер: {comp} -> {result}")
        if result == "win":
            print("Вы выиграли!")
        elif result == "lose":
            print("Вы проиграли.")
        else:
            print("Ничья.")


def main(argv: list[str] | None = None) -> None:
    """Entry point."""
    args = parse_args(argv)
    if args.mode == "guess":
        if args.low > args.high:
            print("ошибка: low > high", file=sys.stderr)
            sys.exit(1)
        run_guess(args.low, args.high)
    else:
        run_rps()


if __name__ == "__main__":
    main()
