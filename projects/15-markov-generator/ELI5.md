# ELI5 — Markov Chain Text Generator

Imagine a word-predicting parrot:

- You feed it text: `"hello world hello there world hello"`. It chops into words `["hello", "world", "hello", "there", ...]` and builds a table with `collections.defaultdict(list)`: for `order=1`, `("hello",) → ["world", "there"]`, `("world",) → ["hello"]`, because after `hello` you saw `world` once and `there` once.
- `order=2` remembers two words: `("hello", "world") → ["hello"]`, `("world", "hello") → ["there"]`. Bigger `order` remembers more history, like a longer memory.
- `generate(chain, length=10, seed=42)` asks the parrot to speak. It picks a starting state (`("hello",)` or random), then repeatedly looks at last `order` words, picks a random next word from the list with `random.Random(seed).choice`, and appends. With `seed=42` it always picks the same "random" words — deterministic, so tests can check.
- If parrot sees `("there",)` and table has no entry for it, it stops early (dead-end) — `break`, return what it has.
- `start=("hello",)` forces start: parrot must begin with `hello`, but `("hello",)` must exist in table and length must match order, else `ValueError`.

Rules a child can follow:

- `build_chain(text, order)` needs `text` a string, `order` 1..5 (not `True`), split on any whitespace; `""` or `"   "` or fewer words than `order+1` → empty table `{}`.
- `generate(chain, length, seed, start)` needs non-empty table with same tuple length, values non-empty string lists, `length` 1..1000, `seed` int if given, `start` tuple of correct length existing in table.
- Tests use `seed` to be deterministic — no randomness surprise: `generate(chain, length=5, seed=0)` always same, so you can `assert` the string.
- This is a toy parrot. Real LLMs use billions of parameters and look at huge context; this looks at 1–5 words and picks from what it saw, but it teaches `collections` + `random` + deterministic testing.
