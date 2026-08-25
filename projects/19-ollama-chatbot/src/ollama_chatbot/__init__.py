"""ollama_chatbot — chat over a local Ollama LLM (basicthon #19)."""

from ollama_chatbot.chat import (
    MAX_HISTORY_MESSAGES,
    add_turn,
    build_messages,
    extract_reply,
    get_base_url,
    get_model,
    get_system_prompt,
)
from ollama_chatbot.ollama_api import OllamaClient, build_chat_url

__all__ = [
    "MAX_HISTORY_MESSAGES",
    "OllamaClient",
    "add_turn",
    "build_chat_url",
    "build_messages",
    "extract_reply",
    "get_base_url",
    "get_model",
    "get_system_prompt",
]
