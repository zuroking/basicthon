# ELI5 — CLI Calculator

Imagine a calculator app, but you type the whole math sentence at once.

- You write `2 + 3 * 4` and it answers `14` (it knows `*` goes before `+`).
- You can use brackets: `(2 + 3) * 4 = 20`.
- If you write `1 / 0`, it doesn't crash — it says "division by zero".
- If you type nonsense like `2 +`, it says "invalid syntax".

Under the hood we don't use the dangerous `eval()` (which could run any code). Instead we read your sentence into a little tree (`ast`) and only allow numbers and `+ - * / // % **` — nothing else can sneak in.

Run `python -m cli_calculator` with no arguments and you get a tiny chat: type `>>` and it answers until you type `exit`.

That's it — a safe, typed, tested calculator you can copy-paste as one folder.
