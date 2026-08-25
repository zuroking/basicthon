# ELI5 — Contacts OOP

Imagine a paper phone book.

- `Contact` is one card: `name` on top, `phone` in the middle, `email` at bottom. Before you put the card in the book, you check: name not empty, phone has 5-15 digits and only `+ - ( ) .` and spaces, email has `@` and `.`.
- `ContactBook` is the whole box of cards. It files cards by `name.lower()` so `Alice` and `alice` are the same slot — no duplicates.

What you can do:

- `add` — put a new card in the box. If name already there → error.
- `get` — pull card by name (`alice` finds `Alice`). If not there → `None`.
- `update` — change phone or email on existing card. If not there → error.
- `delete` — throw card away. If not there → error.
- `search` — shake the box, keep cards where query is inside `name` or `email` or `phone` (case-insensitive). Empty query → nothing.
- `list_contacts` — pour all cards on table sorted by name (`alice, Bob, Charlie`).

That's it — validate one card, manage many cards, CLI just saves cards to `contacts.json` and prints them.
