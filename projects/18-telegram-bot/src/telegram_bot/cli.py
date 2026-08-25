"""Polling loop and CLI for the Telegram bot (basicthon #18).

CLI-only file (argparse + I/O + the polling loop) — excluded from
coverage per G-13. The loop is deliberately simple: fetch updates,
reply to each, advance offset, repeat. Ctrl+C stops it cleanly.
"""

from __future__ import annotations

import argparse
import sys

from telegram_bot.api import TelegramClient, get_poll_timeout, next_offset
from telegram_bot.bot import handle_update


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="telegram-bot",
        description="Telegram echo bot (basicthon #18) — long polling.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="process one batch of updates then exit",
    )
    return parser.parse_args(argv)


def run_loop(client: TelegramClient, once: bool = False) -> None:
    """Run the polling loop until interrupted.

    Args:
        client: configured TelegramClient.
        once: process a single batch then return (used in examples).
    """
    timeout = get_poll_timeout()
    offset: int | None = 0
    print("Bot started, Ctrl+C to stop.")
    try:
        while offset is not None:
            updates = client.get_updates(offset, timeout)
            for update in updates:
                reply = handle_update(update)
                if reply is not None:
                    chat_id, text = reply
                    client.send_message(chat_id, text)
            next_off = next_offset(updates)
            if once:
                return
            if next_off is not None:
                offset = next_off
            elif offset == 0:
                # first empty batch: switch to server-side "new only"
                offset = 0
    except KeyboardInterrupt:
        print("Stopped.")


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m telegram_bot``."""
    args = parse_args(argv)
    try:
        client = TelegramClient()
        me = client.get_me()
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    username = me.get("username", "unknown")
    print(f"Authorized as @{username}")
    run_loop(client, once=bool(getattr(args, "once", False)))
