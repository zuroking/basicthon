# Contributing to basicthon

> Русская версия: [CONTRIBUTING_ru.md](CONTRIBUTING_ru.md)

Thanks for wanting to improve the repository. This document explains what
kinds of changes are welcome, how the repository is organized, and which
rules are fixed by contract.

## Repository layout

The design contract is **[ARCHITECTURE.md](ARCHITECTURE.md)** (v3.1, stable)
— read it before proposing structural changes. Short version:

- `projects/NN-slug/` — twenty self-contained beginner projects, each with
  its own `pyproject.toml`, `requirements.txt`, `src/<package>/`, `tests/`,
  bilingual docs and (where needed) `.env.example`.
- `docs/` — repo-level working documents: `PROGRESS.md` (status + pytest
  summaries), `LEARNING-PATH.md`, `METHODOLOGY.md`.
- Root: showcase READMEs, `SECURITY.md`, `CLAUDE.md`, `ELI5.md`, pinned dev
  tools in `requirements-dev.txt`.

Code standards live in ARCHITECTURE.md §5; the pinned toolchain is
[`requirements-dev.txt`](requirements-dev.txt) (`ruff`, `black`, `mypy`,
`pytest`). Per-project quality gates: `ruff check .`, `black --check .`,
`mypy` (plain for 01–10, `--strict` for 11–20), `pytest -v`.

## What we accept

- **Bug fixes** in existing projects (code or tests).
- **Test improvements** — better coverage of public functions, clearer
  failure messages.
- **Doc improvements** — clearer wording in any README/ELI5 pair; both
  language versions must change together.
- **New examples inside an existing project's scope** — e.g. an extra
  command in project 04's CLI, if it serves the same learning goal.

## What we do not accept

- **New projects (a 21st folder).** The repository is contractually fixed at
  exactly twenty projects (ARCHITECTURE.md §9, rule G-05). PRs adding new
  project folders will be closed — this is a scope decision, not an
  invitation to negotiate in review.
- **Cross-project imports or shared modules.** Isolation is the core design
  constraint: every folder must work standalone. The single sanctioned
  exception (project 20 copy-pasting from 04/11/16 as a snapshot) already
  exists and needs no extensions.
- **New runtime dependencies without strong justification.** Runtime deps go
  only into the affected project's `requirements.txt`, exact-pinned with
  `==`; `pyproject.toml:dependencies = []` stays empty. Stdlib-first is the
  house style.
- **Network-dependent tests.** All tests must pass offline (rule G-12):
  HTTP mocked, Telegram updates as dict fixtures, SQLite in temp dirs.
- **Relaxing type strictness.** Projects 01–10 use plain `mypy`; 11–20 use
  `mypy --strict`. Do not downgrade either side.

## How to propose a change

1. Open an issue first for anything larger than a typo fix — describe the
   problem, not just the solution.
2. Work inside the single affected project folder; keep changes scoped.
3. Make sure the full gate passes locally:

   ```bash
   cd projects/NN-slug
   pip install -e .
   pip install -r requirements.txt
   pytest -v          # genuinely run it
   ruff check .
   black --check .
   mypy src           # --strict for projects 11-20
   ```

4. If your change affects documented behavior, update the project's
   `README.md` **and** `README_ru.md` in the same PR (bilingual pairs mirror
   each other), plus `docs/PROGRESS.md` if test counts change.
5. Keep the pedagogical bar: code in these projects is meant to be read by
   beginners. Prefer obvious over clever, explain *why* in comments where a
   step is non-obvious, keep business logic out of `cli.py`.

## Security-sensitive areas

Projects 12 and 17 (and auth/storage patterns in 16–20) are deliberately
simplified teaching implementations — see [SECURITY.md](SECURITY.md). PRs
that add production hardening there are welcome only if they preserve
beginner readability; PRs that remove the "educational only" warnings are
not.

## License

By contributing you agree that your contributions are licensed under the
repository's [MIT License](LICENSE).
