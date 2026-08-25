# ELI5 — Telegram Bot

Imagine a robot that reads your chat messages and writes back:

- The robot's brain is `handle_text`: you send `/echo hi` — it answers `hi`. You send anything else — it answers `"You said: ..."`. Empty message — it stays quiet (returns None).
- The robot's ears are `get_updates`: every few seconds it asks Telegram "anything new since update #100?" and gets a list of messages. The counter (`next_offset` = max id + 1) makes sure each message is read exactly once.
- The robot's mouth is `send_message(chat_id, text)`: sends the reply back to the right chat.
- The robot's ID card is `BOT_TOKEN` from @BotFather. Every request goes to `{api}/bot{token}/{method}`. It is a secret: lives in an environment variable, documented in `.env.example`, never printed or committed.
- If Telegram says "not ok" or the internet breaks, the pipe (`api.py`) raises `RuntimeError` — the brain never deals with network problems.
- Photos and stickers have no `text`, so the brain politely ignores them.
- Tests are a robot simulator: instead of real Telegram, a fake answers with canned responses — no internet, no token needed.

Rules a child can follow:

- `/start` greets, `/help` lists commands, `/echo X` repeats X.
- No text → no reply. Empty text → no reply.
- Token missing → clear error pointing to `.env.example`.
- One message can be answered many times only if your offset bookkeeping is broken; ours isn't.

Real bots add webhooks, keyboards, databases and rate limits — but this loop is their skeleton.
