# Methodology

> Repository-level document. Russian version: [METHODOLOGY_ru.md](METHODOLOGY_ru.md).
> Full contract — [ARCHITECTURE.md](../ARCHITECTURE.md) §7–§8; this file adapts
> the development cycle for the contributing reader.

## Why a methodology

Every project in this repository went through the same pipeline. This is not
bureaucracy: the pipeline guarantees the three things the repository exists
for — the code works (tests were genuinely executed), the code is explainable
(no "magic" for a beginner), and scope does not creep (it is fixed in
writing up front). If you contribute, following the same steps preserves
those guarantees.

## The six-step cycle

### 1. Lock scope

Before the first line of code, two or three sentences fix what the project
teaches and what is explicitly out of scope. The statement lives at the top
of each project README ("What you learn" / "Что изучаем"). The point: the
temptation to "add one more feature" is checked against a written promise,
not against the author's mood.

### 2. Code in three stages

- **minimal** — works on the smallest set of entities;
- **improved** — validation, typing, edge handling;
- **production-like** — tests, lint, documentation.

The stages are described in each project README. They double as natural
milestones if you use the projects as assignments.

### 3. Technical review — real runs only

Rule G-18: "tests are green" is a fact of execution, not a claim. The full
gate inside a project folder:

```bash
pytest -v          # all tests green
ruff check .       # linter clean
black --check .    # formatting unchanged
mypy src           # plain mypy for 01–10; --strict for 11–20 (GRILL2-04)
```

A summary line such as `45 passed in 0.67s` goes into
[PROGRESS.md](PROGRESS.md); full output stays with CI logs.

### 4. Pedagogical review — a separate pass

Technical green does not answer "is this readable by a beginner". A separate
pass checks: every non-trivial line is explained (comment or README), naming
makes sense in a learning context, business logic is not hidden inside
`cli.py`. Unexplained magic counts as a bug.

### 5. Fix loop — at most two iterations

Review findings are fixed within at most two passes. The exit criterion is
zero open bugs and zero unexplained places — not "perfection". Rule G-04:
anything left after two iterations moves to `known-issues.md` (created as
needed) tagged `[project-NN]`, and the project closes as
`done-with-known-issues`.

### 6. Done

Tests genuinely green, documentation paired (`README` ↔ `README_ru`,
`ELI5` ↔ `ELI5_ru`), status recorded in PROGRESS.md.

## Rules that cannot be bypassed

Full list — ARCHITECTURE.md §9; critical for contributors:

- **Exactly 20 projects (G-05).** New project folders are not accepted as PRs.
- **Isolation:** no imports between `projects/*`; the single exception is
  project 20's copy-paste snapshot from 04/11/16.
- **No network in tests (G-12):** HTTP mocked, SQLite in temp directories.
- **Dependencies:** only in the project's `requirements.txt`, pinned `==`;
  `pyproject.toml:dependencies = []`.
- **Languages:** repository docs ship bilingual pairs; per-project docs use
  the same pairing. Both sides change together.

How to apply these when contributing — see [CONTRIBUTING.md](../CONTRIBUTING.md).
