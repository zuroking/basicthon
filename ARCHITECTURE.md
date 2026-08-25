# ARCHITECTURE.md — basicthon

> English version of the contract. Russian version: [ARCHITECTURE_ru.md](ARCHITECTURE_ru.md).
> Status: STABLE v3.1 (v3.2, v3.3 — see Changelog). Survived three rounds of `grill-me`; cosmetic fixes NIT-01..06 applied. Fixed as the source of truth for project implementation.
> This document describes the repository-level architecture, not any single project's.
> Author: ZuroKing

---

## 1. Repository purpose

`basicthon` is an open learning repository of 20 isolated Python projects for
beginners, ordered along a rising difficulty curve (Foundations → Structures
& Patterns → Data & Algorithms → Systems & Integration). Every project is a
self-contained unit: you can download a single folder and it will work
without the rest of the repository.

A secondary goal: the repository carries author notes and a structure
recognizably tied to ZuroKing, without hurting code readability for
beginners. Notes in `docs/zuroking-notes/` are written only where there is a
non-trivial insight, in Russian (GRILL2-11), 150–300 words, at most one file
per project (`NN-slug.md`, matching the project folder name), linked from
`projects/NN-slug/README.md`.

Language policy (a deliberate decision, not a bug): repository-level
documents ship as bilingual pairs (`docs/LEARNING-PATH.md` ↔
`docs/LEARNING-PATH_ru.md`, `docs/METHODOLOGY.md` ↔ `docs/METHODOLOGY_ru.md`,
`docs/PROGRESS.md` ↔ `docs/PROGRESS_ru.md`). The `_ru` suffix applies to
documentation inside `projects/*/` (`README_ru.md`, `ELI5_ru.md`,
`ARCHITECTURE_ru.md`) because an English project README widens the portfolio
audience, while the repository's internal methodology is the author's working
document.

---

## 2. Agent model and autonomy boundaries

Implementation is driven by an OpenCode agent on the Muse Spark 1.2 model,
following this cycle:

1. Writing `ARCHITECTURE.md` (this document, repository level).
2. A pass through `grill-me` (2–3 iterations), surfacing questions and
   inconsistencies to the author.
3. The main per-project loop:
   a. Writing the project files.
   b. `code-review` of what was written/changed.
   c. Fixing what was found.
   d. Repeating b–c until the readiness criteria are met (see section 8).
   e. Marking the module complete in `docs/PROGRESS.md` (the repository
      todo-list).
4. After each project is complete — documentation generation:
   `README.md`, `ELI5.md`, `ARCHITECTURE.md` (only for the projects where it
   is required — see section 6), and their Russian `_ru` twins
   (`README_ru.md`, `ELI5_ru.md`, `ARCHITECTURE_ru.md`).

**Escalation rule for architectural contradictions (G-01):** the agent treats
this document as the source of truth. On discovering a contradiction:
- if it affects the current or next project per `docs/PROGRESS.md` — stop and
  escalate to the author; wait; do not continue the pipeline;
- if it affects a project far down the queue — record it in
  `docs/known-issues.md` tagged `[project-NN]` and continue without stopping.

`docs/PROGRESS.md` is the repository's single todo-list (see section 7).
`docs/known-issues.md` is the log of deferred contradictions/notes.

---

## 3. Top-level repository structure

```
basicthon/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── .python-version          # GRILL2-12: pins "3.11"
├── requirements-dev.txt     # GRILL2-03: ruff/black/mypy/pytest — repo dev tools
├── .github/workflows/ci.yml # GRILL2-07: discover + strategy.matrix over projects/*/
├── docs/
│   ├── LEARNING-PATH.md
│   ├── METHODOLOGY.md
│   ├── PROGRESS.md          # G-16/GRILL2-09: todo-list, "N passed in Xs" summary line per project
│   ├── known-issues.md      # G-01/G-04: log of deferred contradictions
│   └── zuroking-notes/      # GRILL2-11: NN-slug.md in Russian, 150–300 words, linked from projects/NN-slug/README.md
├── scripts/
│   └── new_project.py       # GRILL2-10: takes --slug and --package explicitly; spec deferred (G-19)
└── projects/
    └── NN-project-slug/
```

Each `projects/NN-project-slug/` is an isolated module. Numbering is
two-digit (`01`–`20`), slugs are kebab-case with no abbreviations meaningful
only to the author. The Python package name (`package_name`) is set
separately via the `--package` parameter when calling `scripts/new_project.py`
(GRILL2-10) — there is no automatic transliteration/mapping from the slug.

**CI (GRILL2-03, GRILL2-07):** `.github/workflows/ci.yml` consists of two
stages: (1) a `discover` job lists `projects/*/` and passes the list as an
output to the next job through `matrix` (never hard-code the list of 20
folders in yml); (2) each matrix job installs `requirements-dev.txt` (with a
pip cache via `actions/cache` keyed on the hash of `requirements-dev.txt`)
for `ruff`/`black`/`mypy`/`pytest`, then installs its folder's
`requirements.txt` and runs `ruff check`, `black --check`, `mypy` (see
GRILL2-04), `pytest -v` only inside that folder, using the config from that
project's own `pyproject.toml`. The future `ci.yml` must pin the interpreter
version explicitly via `actions/setup-python` with `python-version: "3.11"`
in every matrix job instead of relying on the runner's system Python; local
technical-review runs may use any available 3.11+ version — that does not
block progress, but the `ci.yml` itself must be explicit when written. No
combined root-level run.

---

## 4. Single-project structure

```
projects/NN-project-slug/
├── README.md
├── README_ru.md
├── ELI5.md
├── ELI5_ru.md
├── ARCHITECTURE.md        # only for projects from section 6
├── ARCHITECTURE_ru.md     # only for projects from section 6
├── pyproject.toml         # GRILL2-01: standard, no extra tools like poetry; [build-system] (setuptools), [project] name/version="0.1.0"/requires-python=">=3.11", [tool.ruff], [tool.pytest.ini_options]
├── requirements.txt       # G-07: always present; for stdlib-only — a single "# stdlib only, no external dependencies" comment; the single source of truth for runtime dependencies (GRILL2-02)
├── .env.example           # GRILL2-06: required for any project using os.environ/a secret; minimum set: 12,13,14,16,17,18,19,20
├── src/
│   └── package_name/      # name set via --package (GRILL2-10), not derived from the slug
│       ├── __init__.py
│       └── ...
└── tests/
    └── test_*.py
```

Every project is fully isolated: its own `pyproject.toml` (standard, no extra
tools like poetry — GRILL2-01) with `[build-system]` (setuptools),
`[project]` (`name`/`version="0.1.0"`/`requires-python=">=3.11"`),
`[tool.ruff]`, `[tool.pytest.ini_options]`; `dependencies = []` always stays
empty (GRILL2-02). Runtime dependencies live only in `requirements.txt` (the
single source of truth). There is no repository-level `pyproject.toml`
(G-02). CI matrices use each project's config separately.

Installation for local runs/tests (GRILL2-02): the first installation step in
each project's `README.md`/`README_ru.md` lists two separate commands:

```
pip install -e .
pip install -r requirements.txt
```

`requirements.txt` is present at all times, no exceptions (G-07). For
stdlib-only projects the file contains a single comment line:
`# stdlib only, no external dependencies`. Projects with external
dependencies use exact `==` pinning (G-17/GRILL2-12).

`.env.example` is mandatory for any project where the code uses `os.environ`
or holds a configurable secret/key/password (GRILL2-06); the minimum affected
set: 12, 13, 14, 16, 17, 18, 19, 20.

---

## 5. Technology standards

- Python 3.11 (pinned by `.python-version` containing `3.11` at the repo root,
  GRILL2-12; all `pyproject.toml` files use `requires-python = ">=3.11"`
  without exceptions and without per-project drift), mandatory type hints on
  all public functions/methods.
- `pytest` for tests. Coverage criterion (G-13, refined by GRILL2-05):
  "core logic" = all code in `src/` except files consisting entirely of CLI
  parsing and output (`cli.py`, `main.py`). Every public function/method (not
  starting with `_`; class methods count the same as top-level functions)
  outside CLI files has at least one test. Exception: №10 (mini test
  framework) — the criterion is replaced by "the framework correctly tests
  itself on its built-in demo suite". No percentage thresholds.
- `ruff` for linting, `black` for formatting, `mypy` for typing — configured
  in each project's `pyproject.toml` (`[tool.ruff]` and
  `[tool.pytest.ini_options]` sections; black/mypy settings also live in the
  project's `pyproject.toml`). The tools themselves — `ruff`/`black`/`mypy`/
  `pytest` — are repository dev tools from the root `requirements-dev.txt`
  (see §4 on `dependencies`), not per-project dependencies (GRILL2-03). No
  repository-level config is used (G-02, G-18).
- Dependencies are minimal; stdlib is preferred over third-party libraries
  wherever it does not contradict the project goal (e.g. №13–19 inherently
  require `requests`/`httpx`/FastAPI/etc). No shared runtime dependencies
  between projects (see section 3 — deliberate isolation). `requirements.txt`
  is the single source of truth (GRILL2-02),
  `pyproject.toml:dependencies = []`.
- Version pinning (G-17, GRILL2-12): projects with external dependencies use
  exact pinning (`==`) in `requirements.txt`, not ranges;
  `requires-python = ">=3.11"` everywhere.
- Network-free tests (G-12): all tests in CI must work without network and
  without real API keys. HTTP requests go through `unittest.mock`/mocked HTTP
  layers, Telegram updates are mocked dict objects, Ollama responses are
  canned JSON — real inference is never tested in CI. `.env.example` — see
  GRILL2-06.
- Language policy — see section 1 (G-10): bilingual pairs throughout;
  the `_ru` suffix marks the Russian side of every pair.

---

## 6. Difficulty levels and the project list

The formal criterion for requiring `ARCHITECTURE.md` (G-03): the file is
mandatory if a project contains ≥2 decisions from {crypto primitive choice,
authentication scheme, secret storage scheme, non-trivial DB schema,
retry/backoff strategy}. By this criterion: №12 — yes, №17 — yes, №20 — yes;
all others — no.

| Level | № | Project | ARCHITECTURE.md? |
|---|---|---|---|
| Foundations | 01 | CLI calculator | no |
| | 02 | Guess number + rock-paper-scissors | no |
| | 03 | Password generator (`secrets`) | no |
| | 04 | To-do CLI with JSON persistence | no |
| | 05 | Grades analyzer from CSV | no |
| Structures & Patterns | 06 | Contacts (OOP) | no |
| | 07 | File organizer | no |
| | 08 | Duplicate file finder | no |
| | 09 | Timer/stopwatch with logging | no |
| | 10 | Mini test framework | no |
| Data & Algorithms | 11 | SQLite notes | no |
| | 12 | Educational secret manager | **yes** |
| | 13 | Currency converter | no |
| | 14 | Weather CLI with retry | no |
| | 15 | Markov text generator | no |
| Systems & Integration | 16 | REST API on FastAPI (CRUD) | no |
| | 17 | FastAPI + JWT auth | **yes** |
| | 18 | Telegram bot | no |
| | 19 | Chat bot over a local LLM (Ollama) | no |
| | 20 | Final integration (CLI+SQLite+API) | **yes** |

Note on №17: it contains ≥3 decisions from the criterion list — JWT signing
algorithm choice, signing secret storage, token lifetime — so
`ARCHITECTURE.md` is mandatory.

---

## 7. Development methodology (see docs/METHODOLOGY.md)

For every project:

1. **Lock scope** — 2–3 sentences in the README: what is learned, three
   stages (minimal → improved → production-like).
2. **Writing the code** stage by stage.
3. **Technical review** — actual automated runs of `pytest -v` +
   `ruff check` + `black --check` + `mypy` (strictness level in section 8,
   GRILL2-04) — not an agent's textual claim (G-18) — plus a manual check
   for bugs/vulnerabilities and compliance with section 5.
4. **Pedagogical review** — a separate pass: is the code understandable to a
   beginner, is there unexplained "magic", do the names make sense in a
   teaching context. Notes in `docs/zuroking-notes/` are not a mandatory
   criterion of this review (G-15); notes are in Russian, named `NN-slug.md`,
   linked with one line at the end of `README.md` (GRILL2-11).
5. **Fix loop** — at most 2 iterations after review; exit criterion: 0 bugs,
   0 unexplained places — not "until perfect".
6. **Done** — tests genuinely green (`pytest -v`, output never fabricated),
   documentation generated (section 8).

**Fix-loop exhaustion rule (G-04):** if after 2 fix-loop iterations findings
remain uncovered, they move to `docs/known-issues.md` tagged `[project-NN]`;
the module still closes as Done but is marked `done-with-known-issues`
instead of `done` in `docs/PROGRESS.md`.

**Todo-list and artifacts (G-16, GRILL2-09):** `docs/PROGRESS.md` is the
repository's single todo-list — a plain markdown checklist across all 20
projects. Full `pytest -v` output lives only in CI logs (not committed).
Per project, `docs/PROGRESS.md` keeps only a summary line (e.g.
`23 passed in 1.2s`), never full output.

---

## 8. Module readiness criteria ("Definition of Done")

A module counts as complete when:

- [ ] The code passes technical review with no open findings (real runs, G-18).
- [ ] The code passes pedagogical review with no open findings.
- [ ] `pytest -v` — all tests green; full output in CI logs; only a summary
      line in `docs/PROGRESS.md` (GRILL2-09).
- [ ] `ruff check` — no errors.
- [ ] `black --check` — no changes (G-09).
- [ ] `mypy` — no errors, strictness per project group (GRILL2-04):
  - projects 01–10 (Foundations, Structures & Patterns): plain `mypy` (no
    `--strict`);
  - projects 11–20 (Data & Algorithms, Systems & Integration):
    `mypy --strict`.
- [ ] README.md / README_ru.md — present, describe 3 stages and carry the
      ZuroKing note; first installation steps list the two commands
      `pip install -e .` and `pip install -r requirements.txt` (GRILL2-02);
      for projects with `docs/zuroking-notes/NN-slug.md` — `README.md` ends
      with a `См. также: заметка автора` line linking to
      `docs/zuroking-notes/NN-slug.md` (GRILL2-11).
- [ ] ELI5.md / ELI5_ru.md — present.
- [ ] ARCHITECTURE.md / ARCHITECTURE_ru.md — present if the project is marked
      in section 6 (criterion G-03).
- [ ] `requirements.txt` — present (G-07, GRILL2-02 — single source of truth,
      `pyproject.toml:dependencies = []`); for projects with external deps —
      exact `==` pinning (G-17, GRILL2-12); `requires-python = ">=3.11"` in
      `pyproject.toml` (GRILL2-12); `.env.example` present for any project
      with `os.environ`/secrets, minimum 12,13,14,16,17,18,19,20 (GRILL2-06).
- [ ] The module is marked in `docs/PROGRESS.md` as `done` or
      `done-with-known-issues` (G-04, G-16) with a pytest summary line
      (GRILL2-09).

---

## 9. Explicit non-goals (Out of Scope)

Fixed so the agent does not expand scope on its own:

- No universal CLI runner combining all 20 projects into one command.
- No shared/ module with reusable cross-project code (see section 3).
- №12 (secret manager) is an educational implementation explicitly labeled
  "not for real use"; it does not follow the rigor of `secure-secrets-vault`
  (portfolio project #8, separate repository).
- No Docker/deployment infrastructure — outside the scope of a purely
  educational repository.
- **Exactly 20 projects (G-05).** Adding a 21st requires the author's
  explicit written decision outside any `grill-me`/`code-review` cycle. The
  agent neither proposes nor creates additional projects on its own.
- **Exception for №20 (G-08, refined by GRILL2-08):** project №20 is
  explicitly allowed to copy and adapt code from №04, №11, №16 (copy-paste,
  NEVER `import` across project folders) to preserve isolation. It is a
  snapshot taken at №20 creation time, with no obligation to sync with the
  sources if they change later — an isolation-vs-duplication trade-off. The
  README.md/README_ru.md of №20 must carry two notices: (1) "This project
  reuses patterns from projects 04, 11 and 16 — code copied and adapted, not
  imported, to preserve project isolation"; (2) "Snapshot at creation time —
  later changes in 04/11/16 are not ported automatically". This is the only
  exception to the `shared/` ban.

---

## 10. Points fixed for grill-me (summary)

Round one of `grill-me` (v1) closed items G-01..G-18 (see Changelog); round
two closed GRILL2-01..GRILL2-12. Still open:

- **G-19 (scripts/new_project.py without a spec) — remains open.** Not solved
  in this iteration; a separate specification will follow after the current
  round closes. The agent does not invent a solution on its own. The
  `--slug`/`--package` parameters from GRILL2-10 are part of that future spec
  and are fixed here only as an interface.

---

## 11. Changelog

**v3.3 — 2026-08-25** — author decision: the root contract becomes a
bilingual pair:

- `ARCHITECTURE.md` — the English version (base);
- `ARCHITECTURE_ru.md` — the Russian version; content identical, both sides
  change together;
- status remains STABLE; no substantive decisions changed.

**v3.2 — 2026-08-25** — author decision: docs/ documentation converted to
bilingual pairs with uppercase names:

- `docs/learning-path.md` → `docs/LEARNING-PATH.md` (EN) + `docs/LEARNING-PATH_ru.md` (RU);
- `docs/methodology.md` → `docs/METHODOLOGY.md` (EN) + `docs/METHODOLOGY_ru.md` (RU);
- `docs/progress.md` → `docs/PROGRESS.md` (EN) + `docs/PROGRESS_ru.md` (RU);
- §1 language policy updated: repository-level documents are now also
  bilingual pairs (previously "Russian only"); the `_ru` suffix remains the
  Russian side of a pair.

**v3.1 — 2026-08-25** — cosmetic fixes from the final review (NIT-01..06),
status changed to STABLE:

- NIT-01: §3 — unified the `discover` job name (was `discover-job` in the tree).
- NIT-02: §3 — clarified each matrix job installs `requirements-dev.txt` with a pip cache (`actions/cache` keyed on the file hash), not "once globally".
- NIT-03: §4 — fixed installation as two separate lines (`pip install -e .` / `pip install -r requirements.txt`), removed the `&&` variant.
- NIT-04: §4 — `dependencies = []` kept only in §4; §3 tree and §5 text now reference §4.
- NIT-05: §11 — added an explicit line about G-14 (v2) being replaced by GRILL2-10 (v3).
- NIT-06: accounted for while writing the №20 README (no architecture change needed).
- Status: `DRAFT v3` → `STABLE v3.1`, fixed as source of truth.

**v3 — 2026-08-25** — author decisions from the second `grill-me` round (GRILL2-01..GRILL2-12):

- GRILL2-01: §4, §5 — standard `pyproject.toml`: `[build-system]` (setuptools), `[project]` name/version="0.1.0"/requires-python=">=3.11", `[tool.ruff]`, `[tool.pytest.ini_options]`; removed the "minimal" wording.
- GRILL2-02: §4, §5, §8 — `requirements.txt` is the single source of truth, `pyproject.toml:dependencies = []` (§4), README lists two separate lines `pip install -e .` / `pip install -r requirements.txt`.
- GRILL2-03: §3, §5 — root `requirements-dev.txt` for ruff/black/mypy/pytest; CI installs it once before the matrix.
- GRILL2-04: §7, §8 — split mypy strictness: 01–10 plain `mypy`, 11–20 `mypy --strict`.
- GRILL2-05: §5 — "public function/method" = does not start with `_`, methods equal to functions; №10 exception — self-testing on the demo suite.
- GRILL2-06: §4, §5, §8 — `.env.example` for any project with `os.environ`/secrets, minimum 12,13,14,16,17,18,19,20.
- GRILL2-07: §3 — CI matrix generated dynamically via a `discover` job (listing `projects/*/`), never hard-coded.
- GRILL2-08: §9 — №20 is a snapshot without sync, trade-off documented in the README.
- GRILL2-09: §7, §8 — full `pytest -v` output lives only in CI logs; `docs/PROGRESS.md` keeps a summary line.
- GRILL2-10: §3, §4 — removed automatic slug→package mapping; `new_project.py` takes `--slug` and `--package` explicitly.
- GRILL2-11: §1, §3, §7, §8 — notes language Russian, name `NN-slug.md`, link `См. также: заметка автора` at the end of the README.
- GRILL2-12: §3, §4, §5, §8 — `.python-version` changed to `3.11`; all `pyproject.toml` use `requires-python = ">=3.11"`.
- Slug-mapping rule (G-14, v2) replaced by explicit `--slug`/`--package` (GRILL2-10, v3).

**v2 — 2026-08-25** — author decisions from the first `grill-me` round (G-01..G-19):

- G-01: §2 — escalation rule (stop for the current/next project, otherwise `docs/known-issues.md` tagged `[project-NN]`).
- G-02: §4, §5 — per-project `pyproject.toml` (`[tool.ruff]`, `[tool.pytest.ini_options]`), CI as a matrix over folders.
- G-03: §6 — formal ≥2-decisions criterion; №17 moved to "yes" for `ARCHITECTURE.md`.
- G-04: §7 — fix-loop exhaustion rule → `docs/known-issues.md` + `done-with-known-issues` status in `docs/PROGRESS.md`.
- G-05: §9 — explicit ban on a 21st project without written author approval.
- G-06: §4, §8 — `pip install -e .` as the first README step (closed via G-02).
- G-07: §4, §5, §8 — `requirements.txt` always present; stdlib-only marked with `# stdlib only, no external dependencies`.
- G-08: §6, §9 — №20 exception: copy-paste from 04/11/16 without imports + mandatory README notice.
- G-09: §8 — `black --check` added to DoD.
- G-10: §1, §5 — language policy: repo-level Russian only, `_ru` only inside `projects/*/` (deliberate decision).
- G-11: §3 — CI `strategy.matrix` over `projects/*/`, running ruff/black/mypy/pytest inside each folder.
- G-12: §5, §4 — network-free tests (mocks), `.env.example` for 13,14,18,19.
- G-13: §5 — refined the "core logic" criterion (all of `src/` except `cli.py`/`main.py`, every public function outside CLI has at least one test).
- G-14: §3 — `NN-kebab-slug` → `package_name` mapping rule (hyphens→underscores), example `07-file-organizer` → `file_organizer`.
- G-15: §1, §3, §7 — `docs/zuroking-notes/` optional (150–300 words, max one file per project), not a mandatory pedagogical-review criterion.
- G-16: §2, §7, §8 — todo-list = `docs/PROGRESS.md`, `pytest -v` output into commit/PR body.
- G-17: §3, §5, §8 — `.python-version` = `3.10`, exact `==` pinning for 13–19.
- G-18: §7, §8 — technical review = real runs, added `mypy --strict` to DoD.
- G-19: §3, §10 — remains open, unsolved in this iteration.
