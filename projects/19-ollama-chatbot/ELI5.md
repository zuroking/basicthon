# ELI5 — Chat Bot over Local LLM (Ollama)

Imagine a pen pal who lives inside your computer:

- Your whole conversation is just a **list of notes**: "user said X", "assistant said Y". Nothing fancier — `add_turn` glues one note to the list.
- Before sending, `build_messages` adds a sticky note on top — the system prompt ("be brief, be helpful") and cuts old notes so the letter doesn't get too heavy (last 20 only).
- The mailman is `OllamaClient.chat`: it walks the letter to the Ollama program running on your own computer (`http://localhost:11434/api/chat`) and brings back the reply. If your computer's mailman can't find Ollama, you get a clear error, not magic silence.
- `extract_reply` unwraps the envelope: it knows the answer hides at `response["message"]["content"]`.
- The pen pal is a **local** LLM like tinyllama — no internet cloud, your words never leave your machine. That's why you must run `ollama serve` first.
- Tests are pretend letters: instead of a real pen pal, a fake writes canned answers — no model download, no waiting.

Rules a child can follow:

- Empty message → error, not a wasted trip.
- History is trimmed to 20 notes so memory stays small.
- Server down or slow → clear `RuntimeError`, not a crash.
- `/exit` or Ctrl+C ends the chat politely.

Real assistants add streaming, memory files and tools — but this loop is their skeleton.
