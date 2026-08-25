"""secret_manager — educational encrypted secret storage (basicthon #12)."""

from secret_manager.manager import (
    delete_secret,
    generate_key,
    get_key_from_env,
    get_secret,
    list_secrets,
    set_secret,
)

__all__ = [
    "delete_secret",
    "generate_key",
    "get_key_from_env",
    "get_secret",
    "list_secrets",
    "set_secret",
]
