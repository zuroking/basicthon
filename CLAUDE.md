# CLAUDE.md

Guidance for AI coding assistants (Claude, or any other) working in this
repository.

## Project

`basicthon` — a public learning repository of exactly **20 isolated Python
projects** for beginners, ordered by rising difficulty (Foundations 01–05 →
Structures & Patterns 06–10 → Data & Algorithms 11–15 → Systems &
Integration 16–20). Python **3.11** (`.python-version` pins `3.11`; all
`pyproject.toml` files require `>=3.11`).

The design contract is **ARCHITECTURE.md** at the repo root (Russian twin:
ARCHITECTURE_ru.md) — status СТАБИЛЬНО v3.1, the source of truth. Read it before changing anything
structural. Its §9 lists explicit non-goals; its §11 changelog explains why
decisions exist.

## Non-negotiable rules

Violating any of these is a bug even if tests stay green:

- **Exactly 20 projects (G-05).** Never propose or create a 21st project.
  Adding one requires an explicit written decision from the author outside
  any review loop.
- **Project isolation.** No shared/ modules, no imports across
  `projects/*` folders, no repo-level `pyproject.toml`. The single sanctioned
  exception: project 20 may *copy-paste* (never import) code from projects
  04, 11 and 16, as a snapshot.
- **Real test runs only (G-18).** Never claim "tests pass" without executing
  them. Record only summary lines (`N passed in Xs`) in `docs/PROGRESS.md`;
  full verbose output stays in CI logs.
- **No network in tests (G-12).** HTTP is mocked in-process, Telegram updates
  are dict fixtures, Ollama responses are canned JSON, SQLite uses temp dirs.
  A test needing internet or real keys must not exist here.
- **Secrets policy.** `.env.example` contains placeholders and generation
  hints only. If you ever find a real token/key/password committed anywhere,
  stop and escalate immediately.
- **mypy strictness split (GRILL2-04).** Projects 01–10: regular `mypy`.
  Projects 11–20: `mypy --strict`. Do not relax either side.
- **Dependencies.** Runtime deps go only in each project's `requirements.txt`
  with exact `==` pinning; every project's `pyproject.toml` keeps
  `dependencies = []`. Dev tools live once in root `requirements-dev.txt`.
- **Language policy (G-10).** Repo-level docs are Russian-only by design;
  per-project docs are bilingual pairs (`README.md` ↔ `README_ru.md`, etc.).
  Do not add `_ru` suffixes to repo-level docs or drop them from project docs.

## Where things live

```text
ARCHITECTURE.md            # repo contract, source of truth (v3.1)
docs/PROGRESS.md           # THE todo-list: per-project status + pytest summaries
docs/known-issues.md       # deferred issues, tagged [project-NN] (may not exist = none)
projects/NN-slug/          # one self-contained app per folder
├── README.md / README_ru.md / ELI5.md / ELI5_ru.md
├── ARCHITECTURE.md(_ru)   # ONLY for projects 12, 17, 20 (criterion §6)
├── pyproject.toml         # ruff/black/mypy/pytest config per project
├── requirements.txt       # pinned runtime deps, or "# stdlib only..." comment
├── .env.example           # wherever os.environ is used (12–14, 16–20)
├── src/<package>/         # package name set explicitly per project
└── tests/
```

## Commands

Work inside a project folder:

```bash
cd projects/NN-project-slug
pip install -e .
pip install -r requirements.txt
python -m pytest -v          # must be genuinely executed, never assumed
ruff check .
black --check .
mypy --strict src            # strict only for 11-20; plain mypy for 01-10
```

## Development cycle (per project)

1. Lock scope (README states what is learned, three stages).
2. Write code minimal → improved → production-like.
3. Technical review: actually run pytest/ruff/black/mypy; fix findings.
4. Pedagogical review: unexplained magic is a bug; naming must make sense to
   a beginner.
5. Fix loop: max two iterations. Anything still unresolved goes to
   `docs/known-issues.md` tagged `[project-NN]`, project closes as
   `done-with-known-issues`.
6. Mark done in `docs/PROGRESS.md` with a real pytest summary line.

Escalation rule (G-01): if you find a contradiction with ARCHITECTURE.md that
affects the current or next project — stop and ask the author. If it affects
a distant project — record it in known-issues and continue.

## Code conventions inside projects

- Public functions/methods (not starting with `_`) need type hints and at
  least one test (G-13); `cli.py`/`main.py` are exempt from the coverage
  criterion but still typed. Project 10's criterion is replaced by
  self-testing on its built-in demo suite.
- Core logic never lives in CLI files; CLI files never contain business rules.
- Env helpers follow one pattern: validate `var_name`, strip values, return
  documented defaults, raise `ValueError` on misuse. Every env var used in
  code appears in `.env.example`.
- Error style: `ValueError` for user mistakes, domain results as `None`/`False`,
  HTTP codes mapped at the route layer (422 validation, 404 missing,
  401 auth). DELETE endpoints return 204 with an explicitly empty body.
- Comments explain *why*, not *what*. Beginner-readability outranks cleverness.

## Documentation conventions

- Bilingual pairs must mirror each other's meaning; when you change one,
  change the other.
- Project README template is fixed: lock scope → installation (`pip install -e .`
  then `pip install -r requirements.txt`, two separate commands) → usage →
  details → stages → API → testing → ZuroKing's note → isolation statement.
- Security-adjacent projects (12, 17, and integration patterns in 16, 18–20)
  carry visible "educational only" warnings. Keep them prominent when editing.

## Environment notes

- Dev machines are Windows (PowerShell 5.1) + Python 3.12–3.14 locally while
  CI pins 3.11 — code must stay 3.11-compatible; do not use 3.12+ syntax.
- Do not edit Russian-language Markdown through PowerShell
  `Set-Content`/`Get-Content` pipelines — PowerShell 5.1 mangles UTF-8
  Cyrillic. Use file-editing tools that preserve encoding.
- Tool versions are pinned in `requirements-dev.txt` (`ruff==0.15.20`,
  `black==26.5.1`, `mypy==2.1.0`, `pytest==9.1.0`); do not bump casually.
