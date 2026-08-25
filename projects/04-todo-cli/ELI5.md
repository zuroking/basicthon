# ELI5 — To-do CLI with JSON

Imagine a notebook for tasks.

- Each page is a `TodoItem`: it has a number `id`, a `title` like "Buy milk", and a checkbox `completed` (empty or checked).
- You have a box (a JSON file) where you keep all pages. `save_todos` puts the pages in the box, `load_todos` takes them out. If the box is empty or doesn't exist, you get zero pages.

What you can do:

- `add "Buy milk"` — we look at the biggest number in the pile, add 1, and create a new page with that number. Empty title like `"   "` is not allowed.
- `done 1` — find page 1 and check the box. If there is no page 1, we say "not found".
- `delete 1` — tear out page 1. If it's not there, "not found".
- `list` — show all pages; `list --all` shows everything, otherwise we show only unchecked pages. `list --json` prints the box as JSON so you can see raw data.

Why a file? So tasks survive when you close the program. The file is just a JSON array you can open in any editor:

```json
[{"id": 1, "title": "Buy milk", "completed": false}]
```

Run `python -m todo_cli add "Buy milk" && python -m todo_cli list --all` and you get your notebook.
