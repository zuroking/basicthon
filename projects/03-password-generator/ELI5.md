# ELI5 — Password Generator

Imagine you have a big bag of letters.

- Lowercase `a-z` are always in the bag.
- You can decide to add uppercase `A-Z`, digits `0-9`, and symbols like `!@#`.

To make a password, you close your eyes and pick a random letter from the bag, `length` times. We use a special dice called `secrets` that is really unpredictable — better than a usual dice for secrets.

- If you ask for a password shorter than 4, we say "no, too short".
- If you say "no upper, no digits, no symbols" — you still get lowercase, so the bag is never empty.
- You can't cheat by using the unsafe `eval()` — we don't need it; we just pick letters.

There's also a strength checker:

- Short or only one kind of letter (like `aaaaaaa`) → `weak`.
- Longer (8+) and at least 2 kinds (like `abc12345`) → `medium`.
- Really long (12+) and 3+ kinds, or 8+ with all 4 kinds (like `aB3!5678`) → `strong`.

Run `python -m password_generator --length 12 --symbols` and you get a fresh password every time.
