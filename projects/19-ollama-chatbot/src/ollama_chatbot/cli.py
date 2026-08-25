"""REPL and CLI for the Ollama chatbot (basicthon #19).

CLI-only file (argparse + stdin/stdout loop) — excluded from
coverage per G-13. Requires a running local Ollama server:
``ollama serve`` plus ``ollama pull tinyllama``.
"""

from __future__ import annotations

import argparse
import sys

from ollama_chatbot.chat import (
    add_turn,
    build_messages,
    extract_reply,
    get_system_prompt,
)
from ollama_chatbot.ollama_api import OllamaClient


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="ollama-chatbot",
        description="Chat with a local Ollama model (basicthon #19).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="model name (or $CHAT_MODEL, default tinyllama)",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Ollama base URL (or $OLLAMA_BASE_URL)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for console_scripts and ``python -m ollama_chatbot``."""
    args = parse_args(argv)
    try:
        client = OllamaClient(
            base_url=getattr(args, "url", None), model=getattr(args, "model", None)
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    system_prompt = get_system_prompt()
    history: list[dict[str, str]] = []
    print(f"Chatting with '{client.model}' at {client.base_url}")
    print("Type your message; /exit or Ctrl+C to quit.")
    while True:
        try:
            user_line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            return
        if not user_line:
            continue
        if user_line == "/exit":
            print("Bye!")
            return

        history = add_turn(history, "user", user_line)
        payload = build_messages(history, system_prompt)
        try:
            response = client.chat(payload)
            reply = extract_reply(response)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            print("Is the server running?  ollama serve && ollama pull " + client.model)
            return
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return
        history = add_turn(history, "assistant", reply)
        print(f"bot> {reply}")
