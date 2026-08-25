# Learning Path

> Repository-level document. Russian version: [LEARNING-PATH_ru.md](LEARNING-PATH_ru.md).
> Short version of the project table — in the root [README](../README.md);
> the full progression contract — in [ARCHITECTURE.md](../ARCHITECTURE.md) §6.

## The core principle: a staircase, not a showcase

The project order is neither alphabetical nor generically "easy to hard" —
it is built on explicit dependencies: almost every project uses concepts
from one or two predecessors. Going in order, new material always builds on
familiar ground. Skipping ahead means catching up on missed concepts on the fly.

Three rules for walking the path:

1. **Don't skip Foundations, even if it feels slow.** Projects 01–05 look
   simple, but that's where the habits form: reading someone else's code top
   to bottom, running tests before editing, separating logic from I/O.
2. **Break the code on purpose.** After finishing a project, change something
   (a validation limit, an error message) and see which tests fail. It is the
   best comprehension check there is.
3. **Come back.** Project 20 assembles patterns from 04, 11 and 16 — if those
   have faded by then, re-walking the early projects takes half an hour.

## Level 1 — Foundations (01–05): language and files

**What it gives:** confident work with pure Python, no libraries — functions,
dictionaries, files, error handling.

| # | Project | What you learn |
|---|---|---|
| 01 | CLI calculator | Pure functions, safe parsing via `ast`, REPL loops |
| 02 | Guess number + RPS | Game loops, input validation, randomness |
| 03 | Password generator | `secrets` vs `random`, character policies |
| 04 | To-do CLI | JSON persistence, dataclasses, CRUD thinking |
| 05 | Grades analyzer | CSV, aggregate statistics |

**Why file I/O before networking:** files are just dictionaries that survive
between program runs; a network call adds three new entities at once
(protocol, timeouts, connection errors) without teaching anything new about
data itself. First data learns to outlive the process — then it starts
arriving from outside.

**Links within the level:** 01 builds the pure-function habit → 02 wraps it
in a game loop → 03 adds command-line flags → 04 persists state between runs
(first persistence) → 05 reads other people's data (CSV instead of your own
JSON).

## Level 2 — Structures & Patterns (06–10): code structure

**What it gives:** objects, filesystem work, understanding how the tools you
use actually work.

| # | Project | What you learn |
|---|---|---|
| 06 | Contacts (OOP) | Classes, encapsulation, `__eq__`/`__hash__` |
| 07 | File organizer | `pathlib`, dry-run before destructive operations |
| 08 | Duplicate finder | Hashing, optimized tree traversal |
| 09 | Timer/logger | Monotonic clocks, structured logs |
| 10 | Mini test framework | Discovery, assertions, reporting — from the inside |

**Why OOP only at project six:** until this point dicts and functions were
enough. The class appears as an answer to a real need ("a contact record with
behavior"), not as an abstract textbook chapter. Exceptions are likewise
introduced late — as a design tool rather than a nuisance.

**Links:** 06 moves CRUD from 04 onto object rails → 07–08 apply file skills
from 04–05 to the real filesystem → 09 adds time measurement → 10 explains
the magic of pytest you have been using for ten projects — by building its
little sibling.

## Level 3 — Data & Algorithms (11–15): data and the outside world

**What it gives:** real storage, cryptographic concepts, first HTTP.
From this level `mypy --strict` is mandatory.

| # | Project | What you learn |
|---|---|---|
| 11 | SQLite notes | Raw SQL, parameterized queries, row mapping |
| 12 | Secret manager ⚠️ | Fernet, env-based keys (educational implementation!) |
| 13 | Currency converter | httpx, network mocks, offline cache |
| 14 | Weather CLI | Retry/backoff, timeouts, graceful degradation |
| 15 | Markov generator | Markov chains, deterministic tests of randomness |

**Why database before HTTP:** a database answers "how do I store reliably" —
the natural continuation of the JSON-file pain from project 04. HTTP answers
"how do I fetch data from outside" — but working with it still uses the same
dicts and structures from 11. Reliable storage first, external sources second.

**Links:** 11 carries persistence from 04 into SQL → 12 layers encryption on
top of the same file habits → 13–14 teach talking to the network while tests
stay offline → 15 shows an algorithm built on dictionary skills from 06.

⚠️ Project 12 is a deliberate simplification: see [SECURITY.md](../SECURITY.md).

## Level 4 — Systems & Integration (16–20): real systems

**What it gives:** servers, auth, bots, LLMs and the capstone assembling three
layers over one store.

| # | Project | What you learn |
|---|---|---|
| 16 | FastAPI CRUD | REST semantics, Pydantic, TestClient, the 204 rule |
| 17 | FastAPI JWT ⚠️ | bcrypt, token issue/verify, Bearer headers |
| 18 | Telegram bot | External APIs, long polling, offset cursors |
| 19 | Ollama chatbot | Local LLM, conversation history, context trimming |
| 20 | Final integration | CLI + SQLite + API over one storage layer |

**Why a web framework only now:** in 16 the CRUD core is written first as
plain functions over a dict — only then come thin route wrappers. The
framework here is not the foundation but the last layer; the beginner sees
this with their own eyes.

**Links:** 16 wraps CRUD skills from 04–11 into HTTP → 17 adds auth on top of
the same models → 18 applies HTTP experience from 13–14 to two-way dialogue
→ 19 reuses client patterns from 18 with a different endpoint → 20 explicitly
glues 04 + 11 + 16 (copy-paste snapshot per G-08) into one application.

⚠️ Project 17 (and auth patterns in 16/18–20) are educational simplifications:
see [SECURITY.md](../SECURITY.md).

## Pacing and checkpoints

- Realistic pace: 60–100 focused evenings for the whole staircase.
- Self-assessment checkpoints: after 05 you can write a small program with a
  file "from scratch"; after 10 — read unfamiliar OOP code without fear;
  after 15 — design a storage layer and a network client; after 20 — explain
  the layers of a real application.
- Status and pytest summaries per project — in [PROGRESS.md](PROGRESS.md);
  the methodology projects were built and reviewed with — in
  [METHODOLOGY.md](METHODOLOGY.md).
