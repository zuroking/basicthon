# basicthon

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Projects](https://img.shields.io/badge/projects-20-informational)
![Tests](https://img.shields.io/badge/tests-655%20passing-brightgreen)
![Level](https://img.shields.io/badge/level-beginner--friendly-green)

**Languages:** **English** · [Русский](README_ru.md)

Twenty isolated, self-contained Python projects for beginners, ordered along a
rising difficulty curve — from a four-function calculator to an app that
combines a CLI, SQLite and a REST API in one folder. Every project teaches a
specific set of skills, ships with its own `README`, an "explain like I'm 5"
companion, and a test suite that actually passes (655 tests across the repo,
all green at the time of writing).

> **What this is (and isn't).** This is not a course with videos and quizzes,
> and it is not a copy-paste collection of Stack Overflow snippets. It is a
> *ladder*: you read the code of project N, understand every line, then use
> that understanding to read project N+1. The projects get harder on purpose.
> Project 12 (a secrets manager) and the auth/storage patterns in 16–20 are
> **teaching implementations, explicitly not for production** — see
> [SECURITY.md](SECURITY.md) before using anything here for real.

---

## Table of contents

- [Why basicthon exists](#why-basicthon-exists)
- [Who this is for](#who-this-is-for)
- [How it is different from other "20 beginner projects" lists](#how-it-is-different-from-other-20-beginner-projects-lists)
- [The roadmap: four levels, twenty projects](#the-roadmap-four-levels-twenty-projects)
  - [Foundations (01–05)](#foundations-0105)
  - [Structures & Patterns (06–10)](#structures--patterns-0610)
  - [Data & Algorithms (11–15)](#data--algorithms-1115)
  - [Systems & Integration (16–20)](#systems--integration-1620)
- [Repository architecture](#repository-architecture)
  - [Project isolation](#project-isolation)
  - [Per-project tooling](#per-project-tooling)
  - [CI matrix](#ci-matrix)
- [Technology choices by level](#technology-choices-by-level)
- [How to use this repository](#how-to-use-this-repository)
- [Development methodology](#development-methodology)
- [Project structure](#project-structure)
- [Testing](#testing)
- [Documentation conventions](#documentation-conventions)
- [Security note](#security-note)
- [Prerequisites and outcomes, project by project](#prerequisites-and-outcomes-project-by-project)
- [Reading one project properly: a guided tour](#reading-one-project-properly-a-guided-tour)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Glossary](#glossary)
- [Author](#author)
- [License](#license)

## Why basicthon exists

Most "learn Python" material fails in one of two ways:

1. **Toy examples that never connect.** You write a function that reverses a
   string, and then... what? Real programs are files + state + interfaces.
   basicthon's later projects combine exactly those: a CLI talking to a
   database through an API layer.
2. **Frameworks before fundamentals.** Tutorials jump straight to Django or
   pandas. When something breaks — and it will — a beginner has no mental
   model of what is underneath.

basicthon takes the opposite route: **stdlib first, frameworks last**. The
first ten projects run on pure Python. Databases arrive only after you have
felt the pain of managing lists in memory (project 04). FastAPI arrives only
after you have built a CRUD core as plain functions (project 16 shows the
functions first, then wraps them). By project 20 you can look at any web app
and recognize the layers, because you have built all of them yourself.

The name is deliberate: a *thon* of *basics*. Twenty projects, each small
enough to finish in an evening or two, each one step harder than the last.

## Who this is for

- **Beginners who know Python syntax** (variables, loops, functions, classes)
  but have never finished a real, working program.
- **Self-taught developers** with gaps: you can script, but you have never
  written tests, never touched SQLite directly, never seen why a JWT has an
  expiry claim.
- **Students preparing for internships**: projects 11–20 read like interview
  questions ("build CRUD", "add auth", "integrate CLI + DB + API").
- **Teachers and mentors** looking for a ready-made curriculum spine with a
  per-project reading order and honest security notes.

If you have never opened Python at all, start elsewhere (any interactive
tutorial), then come back when you know what a `for` loop and a `dict` are.
[ELI5.md](ELI5.md) explains the whole repository without assuming you code.

## How it is different from other "20 beginner projects" lists

| Typical list | basicthon |
|---|---|
| One-paragraph descriptions; no code | Full working code for every project |
| No tests | Every public function tested; summary in `docs/PROGRESS.md` |
| Projects unrelated to each other | Deliberate difficulty curve: 04→11→16 reappear combined in 20 |
| Copy-paste encouraged | Each project explains *why* it is written this way (ZuroKing's note) |
| Silent about security | Explicit warnings where teaching code must not be used for real ([SECURITY.md](SECURITY.md)) |
| Single blob repository | Strict isolation: every folder works standalone |

The isolation rule deserves emphasis because it shapes everything: **you can
delete any nineteen folders and the remaining one still works.** No shared
modules, no imports across projects, no root-level package. That constraint
costs some duplication (project 20 copies code from 04/11/16 by design) and
buys independence: download one folder, `pip install -e .`, done.

---

## The roadmap: four levels, twenty projects

### Foundations (01–05)

Pure standard library. Input/output, data types, error handling, file
persistence. No classes required until 06, though they appear naturally.

| # | Project | What it teaches |
|---|---|---|
| 01 | [CLI calculator](projects/01-cli-calculator/) | Pure functions, safe expression parsing via `ast` (why `eval()` is dangerous), REPL loops, clear error messages |
| 02 | [Guess number + RPS](projects/02-guess-number-rps/) | Randomness, game loops, input validation, separating rules from interface |
| 03 | [Password generator](projects/03-password-generator/) | Cryptographic randomness (`secrets` vs `random`), character policies, CLI flags |
| 04 | [To-do CLI](projects/04-todo-cli/) | JSON persistence, dataclasses, id management, CRUD thinking before databases |
| 05 | [Grades analyzer](projects/05-grades-analyzer/) | CSV parsing, aggregation statistics, sorting and grouping real-world data |

### Structures & Patterns (06–10)

Objects, file system work, and your own mini-framework. After this block you
can read most intermediate Python code without fear.

| # | Project | What it teaches |
|---|---|---|
| 06 | [Contacts (OOP)](projects/06-contacts-oop/) | Classes, encapsulation, equality/hash, moving from dicts to objects |
| 07 | [File organizer](projects/07-file-organizer/) | `pathlib`, category mapping, dry-run safety before destructive operations |
| 08 | [Duplicate finder](projects/08-duplicate-finder/) | Hashing files, size-first optimization, walking trees efficiently |
| 09 | [Timer/logger](projects/09-timer-logger/) | Time measurement, monotonic clocks, structured logging sessions |
| 10 | [Mini test framework](projects/10-mini-test-framework/) | How pytest works under the hood: discovery, assertions, reporting — by building your own |

### Data & Algorithms (11–15)

Real storage, real crypto concepts, real HTTP. mypy switches to strict mode
here — the code grows up.

| # | Project | What it teaches |
|---|---|---|
| 11 | [SQLite notes](projects/11-sqlite-notes/) | Raw SQL via stdlib `sqlite3`, schema creation, parameterized queries, row mapping |
| 12 | [Secret manager](projects/12-secret-manager/) ⚠️ educational | Authenticated encryption (Fernet), key handling via env vars — **teaching vault, never store real secrets** |
| 13 | [Currency converter](projects/13-currency-converter/) | HTTP clients (`httpx`), mocking network calls, offline rates cache |
| 14 | [Weather CLI](projects/14-weather-cli/) | Retry/backoff strategies, timeouts, graceful degradation when APIs fail |
| 15 | [Markov generator](projects/15-markov-generator/) | Markov chains, frequency tables, deterministic testing of random output |

### Systems & Integration (16–20)

Servers, auth, bots, LLMs, and the capstone that combines three earlier
projects into one application.

| # | Project | What it teaches |
|---|---|---|
| 16 | [FastAPI CRUD](projects/16-fastapi-crud/) | REST semantics (201/204/404/422), Pydantic validation, TestClient, why 204 must not carry a body |
| 17 | [FastAPI + JWT](projects/17-fastapi-jwt/) ⚠️ educational | Password hashing (bcrypt), token issue/verify, Bearer headers, token expiry — **teaching auth, not production auth** |
| 18 | [Telegram bot](projects/18-telegram-bot/) | External HTTP APIs, long polling, offset bookkeeping, secret tokens via env |
| 19 | [Ollama chatbot](projects/19-ollama-chatbot/) | Local LLM integration, conversation history management, context trimming |
| 20 | [Final integration](projects/20-final-integration/) | Three layers over one SQLite store: CLI + API + library access; combining skills from 04, 11 and 16 |

Projects marked ⚠️ contain deliberately simplified security implementations.
They exist to teach the concepts safely; see [SECURITY.md](SECURITY.md) for
what was left out and why.

---

## Repository architecture

The full architectural contract lives in
[`ARCHITECTURE.md`](ARCHITECTURE.md) (Russian twin:
[`ARCHITECTURE_ru.md`](ARCHITECTURE_ru.md); stable, source of truth). Here is
the short version and the reasoning behind it.

### Project isolation

Every folder in `projects/` is a complete, standalone application:

```text
projects/NN-project-slug/
├── README.md / README_ru.md      # usage, stages, author's note
├── ELI5.md / ELI5_ru.md          # plain-language explanation
├── ARCHITECTURE.md(_ru)          # only where design decisions warrant it (§6)
├── pyproject.toml                # build config, ruff/black/mypy/pytest settings
├── requirements.txt              # single source of truth for runtime deps
├── .env.example                  # wherever os.environ is used
├── src/<package>/                # importable package
└── tests/                        # pytest suite, no network needed
```

Why isolation instead of a monorepo with shared utilities?

- **Learners download one folder.** A student working on the weather CLI does
  not need the Telegram bot's dependencies, history, or test suite.
- **Dependency honesty.** Each project declares exactly what it needs. There
  is no invisible root environment hiding missing declarations.
- **Copy freedom.** Teachers can lift a single project into their own course
  without dragging half a repository along.

The cost is accepted duplication: project 20 intentionally *copies* (never
imports) code from projects 04, 11 and 16 so it remains standalone. This is
documented in its README as a snapshot decision.

### Per-project tooling

Each project carries its own `pyproject.toml` with `[tool.ruff]`,
`[tool.black]`, `[tool.mypy]` and `[tool.pytest.ini_options]` sections. There
is deliberately **no root-level pyproject**:

- CI runs each project against *its own* configuration, so a project cannot
  silently rely on repo-wide leniency.
- Projects stay portable: the config travels with the folder.
- Dev tools (`ruff`, `black`, `mypy`, `pytest`) live once in the root
  [`requirements-dev.txt`](requirements-dev.txt); runtime dependencies live in
  each project's `requirements.txt` with exact `==` pinning. Plain pip, no
  poetry/pipenv — beginners should learn the tools that work everywhere
  before learning opinionated wrappers around them.

Type checking is split by level: projects 01–10 pass regular `mypy`; projects
11–20 must pass `mypy --strict`. The stricter mode arrives together with
real persistence and HTTP code, where type errors stop being theoretical.

### CI matrix

The CI plan (specified in ARCHITECTURE.md §3, rule GRILL2-07) uses two
stages: a `discover` job lists `projects/*/` dynamically and feeds them into
`strategy.matrix`; each matrix job pins Python 3.11 via `actions/setup-python`,
installs dev tools with a pip cache keyed on `requirements-dev.txt`, installs
the project's requirements, and runs `ruff check`, `black --check`, `mypy`
(level-appropriate) and `pytest -v` inside that project's folder only. No
root-level combined run: a broken project fails alone.

> Note: the workflow file `.github/workflows/ci.yml` is **planned, not yet
> implemented** — the specification above is fixed in ARCHITECTURE.md and the
> same gates are currently run locally per project (`ruff` / `black` / `mypy`
> / `pytest`).

---

## Technology choices by level

Short version, no philosophy: each choice is the simplest thing that teaches
the concept honestly.

- **01–10: stdlib only.** The point of these levels is Python itself:
  functions, classes, files, hashing, time. Any third-party dependency would
  be noise. Even project 03 uses `secrets` rather than `random` because that
  distinction *is* the lesson.
- **11–12: SQLite and Fernet.** Project 11 uses raw `sqlite3` so learners see
  SQL strings, parameters and row mapping — ORM magic comes later, if ever.
  Project 12 uses `cryptography`'s Fernet because inventing your own
  encryption is the classic beginner catastrophe; using audited primitives is
  the lesson.
- **13–15: httpx, retry logic, Markov chains.** First contact with network
  code is always mocked in tests; the converter caches rates offline; the
  weather CLI treats failure as normal (retry/backoff). Project 15 stays on
  stdlib — Markov chains need dictionaries, not libraries.
- **16–17: FastAPI + Pydantic (+ PyJWT, bcrypt).** FastAPI's decorator model
  maps cleanly onto "thin wrapper over plain functions", which is exactly how
  16 is built: the CRUD core exists before any route. PyJWT and bcrypt are
  minimal, audited choices for the auth lesson.
- **18: Bot API via raw httpx.** A Telegram SDK would hide the request/response
  cycle this project exists to teach. Long polling is ~40 lines with httpx.
- **19: Ollama's local HTTP API.** Local-first AI keeps data on the machine
  and removes API keys from the beginner path entirely. Same skill as 18,
  different endpoint.
- **20: everything above, combined.** fastapi + uvicorn + sqlite3, glued by
  one `storage.py` module both the CLI and API call.

---

## How to use this repository

Three recommended paths, depending on your goal:

1. **Sequential (recommended for beginners):** do 01 → 20 in order. Read the
   project README, run its tests (`pytest -v`), break things on purpose,
   rebuild. Expect roughly 2–4 evenings per Foundations project and more for
   Systems & Integration.
2. **Gap-filling (for self-taught devs):** jump to what you are missing. The
   table above says what each project assumes. If 17 feels hard, spend an
   hour with 16 first — the curve is connected on purpose.
3. **Reference (for mentors):** pick projects as assignments. Each README
   states a lock scope (what is learned) and three build stages (minimal →
   improved → production-like), which map naturally onto graded milestones.

Detailed guidance lives in [`docs/LEARNING-PATH.md`](docs/LEARNING-PATH.md)
(Russian twin: `LEARNING-PATH_ru.md`); the pipeline every project was built
and reviewed with is described in
[`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

For every project the loop is the same:

```bash
cd projects/NN-project-slug
pip install -e .
pip install -r requirements.txt
pytest -v        # watch it pass before you change anything
python -m <package> --help
```

Then read `src/<package>` top-to-bottom — none of the modules are longer than
a few hundred lines, and every non-obvious decision is commented or explained
in the README.

## Development methodology

Every project in this repository went through the same pipeline (full text:
`docs/METHODOLOGY.md`, contract: ARCHITECTURE.md §7):

1. **Lock scope.** Two or three sentences in the README: what is learned,
   what is out of scope. Prevents feature creep.
2. **Write code in three stages.** Minimal (works) → improved (validated,
   typed) → production-like (tested, linted, documented).
3. **Technical review with real runs.** `pytest -v`, `ruff check`,
   `black --check`, `mypy` — executed, not claimed. Output summaries are
   recorded per project in [`docs/PROGRESS.md`](docs/PROGRESS.md).
4. **Pedagogical review.** Separate pass: is every trick explained? Would a
   beginner understand the naming? Unexplained "magic" is treated as a bug.
5. **Fix loop.** At most two iterations after review; remaining known
   imperfections go to `docs/known-issues.md` instead of blocking release.
6. **Done.** Tests genuinely green, documentation generated, progress marked.

The repository-level architecture itself went through three rounds of
adversarial questioning ("grill-me") before implementation started — the
changelog in ARCHITECTURE.md shows every decision and its origin.

## Project structure

```text
basicthon/
├── README.md / README_ru.md     # this file
├── CLAUDE.md(_ru)               # guidance for AI coding assistants
├── SECURITY.md(_ru)             # security policy & honest limitations
├── ELI5.md(_ru)                 # the whole repo explained without jargon
├── ARCHITECTURE.md              # repo-level contract (source of truth, v3.1)
├── LICENSE                      # MIT
├── CONTRIBUTING.md              # how to propose changes
├── CHANGELOG.md                 # notable changes
├── .python-version              # "3.11"
├── requirements-dev.txt         # ruff/black/mypy/pytest, pinned
├── docs/
│   ├── PROGRESS.md              # per-project status + pytest summaries
│   ├── LEARNING-PATH.md         # recommended order and pacing
│   ├── METHODOLOGY.md           # the development pipeline in detail
│   └── known-issues.md          # deferred issues, tagged per project
└── projects/
    ├── 01-cli-calculator/
    │   ├── README.md            # English entry point
    │   ├── README_ru.md         # Russian mirror
    │   ├── ELI5.md / ELI5_ru.md
    │   ├── pyproject.toml       # per-project tool config
    │   ├── requirements.txt     # pinned runtime deps (or "stdlib only")
    │   ├── .env.example         # only where env vars are used
    │   ├── src/cli_calculator/  # the actual package
    │   └── tests/               # pytest, offline-only
    ├── 02-guess-number-rps/
    │   └── ...
    └── 20-final-integration/
```

## Testing

All 655 tests across 20 projects pass, and none of them require network
access, API keys, a running Ollama server or a Telegram token:

```bash
# one project
cd projects/16-fastapi-crud && pytest -v

# everything (from repo root, PowerShell example)
Get-ChildItem projects | ForEach-Object {
  Push-Location $_.FullName; python -m pytest -q; Pop-Location
}
```

Mocking policy: HTTP is intercepted (`httpx.post` replaced in-process),
Telegram updates are dict fixtures, Ollama responses are canned JSON, SQLite
uses temporary directories. If a test needs the internet, it does not belong
in this repository.

Per-project summaries (test counts and timings) live in
[`docs/PROGRESS.md`](docs/PROGRESS.md).

## Documentation conventions

Language split is deliberate (ARCHITECTURE.md §1):

- Repository documents (`LEARNING-PATH.md`, `METHODOLOGY.md`, each with a
  `_ru` twin) — authored in Russian, because they are the author's working
  documents.
- Per-project documents — bilingual pairs (`README.md` ↔ `README_ru.md`),
  because an English README makes each project portfolio-friendly.

Every project README follows one template: lock scope → installation (always
the same two commands) → usage → details → three stages → API → testing →
ZuroKing's note → isolation statement. Every project also has an `ELI5`
variant that explains it without jargon.

## Security note

Short and prominent, because it matters: several projects implement
security-adjacent functionality as **teaching simplifications**. In
particular, project 12 stores secrets with real Fernet encryption but omits
everything a real vault needs (key rotation, hardened permissions, memory
protection), and project 17 demonstrates JWT auth with an in-memory user
store and a development fallback key. None of the twenty projects should
guard real credentials. The full list of simplifications, the `.env.example`
policy (placeholders only — never commit real secrets anywhere in this repo),
and the vulnerability reporting path are documented in
[SECURITY.md](SECURITY.md).

## Prerequisites and outcomes, project by project

Each entry: what to know *before* starting, and what you will be able to do
*after*. Use this to jump between levels without breaking the curve.

**01 — CLI calculator.**
Before: variables, functions, `if`. After: reading a grammar from an AST,
whitelisting instead of blacklisting (the security instinct), building a
read-eval-print loop.

**02 — Guess number + rock-paper-scissors.**
Before: loops. After: game state machines, `random` vs seeded determinism in
tests, splitting "rules of the game" from "talking to the player".

**03 — Password generator.**
Before: string methods. After: why `random` is predictable and `secrets` is
not; character-class policies; designing CLI flags people actually remember.

**04 — To-do CLI.**
Before: lists and dicts. After: dataclasses as typed records, JSON round-trips,
why ids must never be reused, the CRUD mental model every later project reuse.

**05 — Grades analyzer.**
Before: dicts. After: CSV realities (headers, encodings, empty rows),
aggregation (`mean`/`median`/distribution), sorting with keys.

**06 — Contacts (OOP).**
Before: functions. After: classes as blueprints, `__eq__`/`__hash__`
contracts, when a class is better than a dict — and when it is not.

**07 — File organizer.**
Before: `pathlib` basics. After: mapping rules as data, dry-run mode before
any destructive operation, idempotent scripts.

**08 — Duplicate finder.**
Before: hashing conceptually. After: size-first filtering for speed,
content hashes for correctness, walking large trees without freezing.

**09 — Timer/logger.**
Before: nothing special. After: monotonic vs wall clocks, structured session
logs, formatting durations humans can read.

**10 — Mini test framework.**
Before: having used pytest a little. After: discovery, assertion rewriting at
a toy scale, report generation — you stop fearing pytest because you built
its little sibling.

**11 — SQLite notes.**
Before: file persistence (04). After: schemas, `AUTOINCREMENT`,
parameterized queries (and why string-formatting SQL is how beginners get
hacked), row-to-object mapping. mypy becomes strict from here on.

**12 — Secret manager (educational).**
Before: 11's storage habits. After: authenticated encryption vs plain
encoding, Fernet tokens, env-based key delivery — plus the honest list of
everything a real vault adds.

**13 — Currency converter.**
Before: 11-level typing. After: `httpx` clients, mocking network responses so
tests stay offline, caching rates for offline use.

**14 — Weather CLI.**
Before: 13. After: timeouts everywhere, retry with backoff, treating API
failure as a normal branch rather than an exception.

**15 — Markov generator.**
Before: dicts of dicts. After: frequency tables, sampling, testing random
output by seeding it.

**16 — FastAPI CRUD.**
Before: 11–15 maturity. After: REST verbs and status codes as vocabulary,
Pydantic models as boundary guards, TestClient, the 204-no-body rule.

**17 — FastAPI JWT (educational).**
Before: 16. After: bcrypt password hashing, JWT structure (header.payload.
signature), expiry claims, Bearer headers — and exactly which production
hardening steps were skipped.

**18 — Telegram bot.**
Before: 16-level typing, any HTTP client experience. After: long polling,
offset cursors, external service error handling, token hygiene.

**19 — Ollama chatbot.**
Before: 18's HTTP habits. After: chat message arrays, context trimming, local
LLM servers, mocking slow dependencies.

**20 — Final integration.**
Before: 04 + 11 + 16 patterns (they are re-taught here as copies). After:
layered architecture — one storage module serving both a CLI and an API —
which is the shape of most real software.

## Reading one project properly: a guided tour

Here is how to work through any project, using **16-fastapi-crud** as the
example. The same recipe works for all twenty.

1. **Read the lock scope** (first paragraph of the README). You now know the
   borders: in-memory storage, five routes, no database. Anything beyond that
   is out of scope by design — do not add it while learning.
2. **Run the tests before reading code:**

   ```bash
   cd projects/16-fastapi-crud
   pip install -e .
   pip install -r requirements.txt
   pytest -v
   ```

   Forty-five tests pass in under a second, offline. You have just proven
   the code works — now find out why.
3. **Read `models.py` first** (~44 lines). Three Pydantic classes define what
   a task looks like and what counts as valid input. This is the vocabulary
   of the whole project.
4. **Read `app.py` top-down.** The first half is plain functions operating on
   a dict — create/get/list/update/delete. Notice there is zero FastAPI here.
   Only in the second half do thin route wrappers appear, each three lines
   long: validate, call the function, translate `None` into a 404.
5. **Break something deliberately.** Change `min_length=1` to `min_length=5`
   in `models.py`, rerun pytest, watch exactly two tests fail, read their
   failure messages. You have just experienced what tests are *for*.
6. **Read the ZuroKing note.** It compresses the project into one insight:
   the storage layer is trivially simple, and that simplicity is what makes
   the API wrapper readable.
7. **Only now extend it.** Add a search endpoint. Write its test first. You
   are doing step 2 of the methodology on your own.

Total time: one focused evening. Multiply by twenty projects and you have a
portfolio, not just homework.

## Troubleshooting

Common first-run problems and their fixes:

- **`python: can't open file 'src/cli_calculator/__main__.py'`** — you ran the
  command from the repository root. Each project runs from *its own folder*
  (`cd projects/NN-slug` first).
- **`ModuleNotFoundError: No module named 'cli_calculator'`** — you skipped
  `pip install -e .`. It registers the package against your current
  interpreter.
- **Tests fail with connection errors** — they should not; if they do, a
  proxy environment variable may be interfering with the HTTP mocks. Unset
  `HTTP_PROXY`/`HTTPS_PROXY` for the test run.
- **`mypy` behaves differently than described** — check you are inside the
  right level: projects 01–10 use plain `mypy`, 11–20 use `mypy --strict`.
- **Cyrillic looks broken in some tool output** — that is usually PowerShell
  5.1's console encoding, not the files. The files themselves are UTF-8.
- **A dependency refuses to install on Python 3.14** — the pins target
  3.11+; use Python 3.11–3.13 for smoothest results, matching CI.

## FAQ

**Why Python 3.11 specifically?** CI pins it, all configs declare
`requires-python = ">=3.11"`, and no 3.12+ syntax was used anywhere — so
3.11 through 3.13 all work locally. One number, no per-project drift.

**Why does every project repeat `ruff/black/mypy/pytest` config?** So each
folder is truly standalone: copy it anywhere and its quality gates travel
with it. Repo-wide config would create invisible coupling.

**Why not poetry / uv / pipenv?** Nothing wrong with them — but they each add
concepts (lockfiles, virtualenv management opinions) before a learner has
reason to care. Plain `pip install -e .` + `requirements.txt` works
everywhere, including inside CI matrices.

**Can I use these projects in my portfolio?** Yes — that is part of the
design (English READMEs, clean commits). Two honest notes: keep the
"educational only" labels visible on projects 12 and 17 (reviewers respect
candor more than bravado), and be ready to explain every line — interviewers
will ask.

**Can I contribute a new project?** Not as a 21st folder — the count is fixed
at 20 by contract (ARCHITECTURE.md §9). Improvements, translations and bug
fixes to existing projects are welcome via CONTRIBUTING.md.

**Why are repo docs Russian but project docs bilingual?** Deliberate split
(ARCHITECTURE.md §1): internal working documents serve the author; project
READMEs serve a worldwide audience. Both decisions are written down so nobody
has to guess.

**How long does the whole staircase take?** Rough math: Foundations ~2–4
evenings each, Structures & Patterns similar, Data & Algorithms and Systems &
Integration progressively longer — call it 60–100 focused evenings end to
end. Faster if you already program in another language; slower is fine too.

## Glossary

Terms used across the repository, in plain words. When a project README uses
one of these, it links back to the concept, not the other way around.

**AST (Abstract Syntax Tree)** — Python's way of representing code as a tree
of objects. Project 01 reads your math expression as a tree instead of
executing it blindly — the difference between parsing and running.

**bcrypt** — a password-hashing function that is deliberately slow. Slow is
good: it makes mass guessing expensive. Project 17.

**CLI** — Command-Line Interface; the text mode where you type commands like
`final-integration add`. Projects 01–09 and 20 all have one.

**CRUD** — Create, Read, Update, Delete: the four things you can do to stored
data, and the skeleton of most applications.

**Dry run** — showing what a program *would* do without actually doing it.
Project 07's safety net before moving real files.

**Env variable** — a named value in your operating system's environment,
used for configuration and secrets so they never end up in code. Read via
`os.environ`; every project that does this ships an `.env.example`.

**Fernet** — a recipe from the `cryptography` library: authenticated
encryption in one call. Project 12.

**JWT (JSON Web Token)** — a signed string proving "the server said this
person is logged in until time T". Project 17.

**Long polling** — asking a server "anything new?" and having the server hold
the answer a few seconds if there isn't. How project 18 receives Telegram
messages.

**Markov chain** — building new text by always picking the next word based on
which words followed it before. Project 15.

**Mocking** — replacing a real dependency (network, server) with a fake that
returns canned answers, so tests stay fast and offline.

**Monotonic clock** — a clock that only moves forward, immune to system time
changes; correct choice for measuring durations. Project 09.

**Parameterized query** — an SQL statement with placeholders (`?`) filled by
the library, which makes SQL injection structurally impossible. Project 11.

**Pin (pinned dependency)** — fixing a dependency to one exact version with
`==`, so `fastapi==0.110.2` means exactly that version forever.

**Pydantic** — the validation library FastAPI uses: describe data once as a
class, get type checks and error messages for free.

**pytest** — the test runner used everywhere here; finds files named
`test_*.py` and runs functions named `test_*`.

**REPL** — Read-Eval-Print Loop; a conversation where you type an expression
and see its result immediately. Project 01 has one.

**REST** — the convention that URLs are nouns (`/tasks/42`) and HTTP verbs
are verbs (`GET`, `POST`, `PUT`, `DELETE`). Projects 16, 17, 20.

**Retry/backoff** — retrying a failed network call after a growing delay
(1s, 2s, 4s...) instead of hammering a struggling server. Project 14.

**Strict typing (`mypy --strict`)** — the type checker assumes nothing:
every function must declare types, no silent `Any`. Mandatory from project
11 onward.

**TestClient** — FastAPI's helper that calls your routes in-process, without
starting a server or opening ports. Projects 16, 17, 20 tests.

**Type hint** — an annotation like `def add(a: int, b: int) -> int:` that
tells humans and `mypy` what goes in and out.

## How the repository itself was built

Meta, but useful for anyone maintaining a similar curriculum: basicthon was
not written ad hoc. Before any project code existed, the repo-level
architecture went through three rounds of adversarial review (called
"grill-me" internally) where an agent challenged every design decision until
each had a recorded justification — the G-01…G-19 and GRILL2-01…GRILL2-12
decisions you can trace in ARCHITECTURE.md §11.

Then each of the twenty projects passed through the same six-step pipeline
(lock scope → three-stage implementation → technical review with real tool
runs → pedagogical review → bounded fix loop → done), with an escalation rule:
any contradiction with the architecture contract stops the line if it affects
the current project, or gets deferred to `docs/known-issues.md` if it affects
a distant one. Nothing in this repository is exempt from its own rules —
including the documentation you are reading now, which also has bilingual
pairs that must mirror each other.

The practical consequence: if you want to know *why* something looks the way
it does, the answer is always findable — either in the project README, in the
project's ARCHITECTURE.md (for 12/17/20), or in the repo contract's changelog.
No folklore, no tribal knowledge.

## Author

Designed and maintained by **ZuroKing**. The author's notes inside each
project (`ZuroKing's note`) highlight the one non-obvious insight the project
was built to deliver — read them; they are the shortest path to the point.

Issues and pull requests are welcome — see
[`CONTRIBUTING.md`](CONTRIBUTING.md) for expectations (spoiler: tests and
isolation rules are non-negotiable).

## License

[MIT](LICENSE) © 2026 ZuroKing
