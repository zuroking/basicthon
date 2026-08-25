"""final_integration — CLI + SQLite + REST API (basicthon #20).

Reuses patterns copy-pasted from projects 04 (todo CLI), 11 (SQLite
notes) and 16 (FastAPI CRUD) per G-08 / GRILL2-08 — snapshot, no
imports across projects.
"""

from final_integration.api import app, get_host, get_port
from final_integration.storage import (
    Task,
    add_task,
    complete_task,
    create_db,
    delete_task,
    get_db_path,
    get_task,
    list_tasks,
)

__all__ = [
    "Task",
    "add_task",
    "app",
    "complete_task",
    "create_db",
    "delete_task",
    "get_db_path",
    "get_host",
    "get_port",
    "get_task",
    "list_tasks",
]
