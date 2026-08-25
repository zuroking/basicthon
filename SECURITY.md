# Security Policy

> Русская версия: [SECURITY_ru.md](SECURITY_ru.md)

## ⚠️ Read this first: educational code, not production code

**basicthon is a learning repository. Several projects implement
security-relevant functionality as deliberately simplified teaching
versions. None of them are safe for real-world use.**

The most important cases, in descending order of risk:

| Project | What it looks like | Why it must not be used for real |
|---|---|---|
| **12 — Secret Manager** | Real Fernet (AES + HMAC) encryption | No key rotation, no hardened file permissions, no memory protection, single unencrypted-name JSON index, no atomic writes. A toy vault. |
| **17 — FastAPI JWT** | Working login/register/`Bearer` flow | In-memory user store (wiped on restart), hard-coded dev fallback key (`dev-secret-key-change-me`) if `$SECRET_KEY` is unset, no refresh/revocation, no HTTPS enforcement, no rate limiting. |
| **16 / 20 — REST APIs** | Clean CRUD semantics | No authentication on any endpoint; anyone who can reach the port can read and delete all data. |
| **18 — Telegram bot / 19 — Ollama chatbot** | Token/env handling patterns | Demonstrate correct *habits* (secrets via env, never logged), but have no threat model of their own beyond that. |

This is not an accident or an omission: ARCHITECTURE.md §9 fixes it as a
design goal ("№12 is a teaching implementation with an explicit 'not for real
use' label"). The simplifications exist so that each concept fits into a
beginner-readable module. Every affected project repeats this warning in its
README.

**Do not store real passwords, API keys, tokens or personal data in any
project in this repository.**

## Reporting a vulnerability

Found something broken in the teaching code? Reports are welcome.

- For anything that could mislead a learner into an insecure habit (e.g. a
  crypto misuse *not* covered by the documented simplifications above), open
  a GitHub issue describing the project, the file, and the risk.
- For genuinely sensitive findings you'd rather not post publicly, contact
  the maintainer directly through GitHub.
- Please include: project number/name, affected files, steps to reproduce,
  and which documented simplification (if any) already covers it.

Reports that contradict the documented scope above (for example, "project 12
does not rotate keys" or "project 17 has no rate limiting") will be closed as
working-as-documented — but if you believe a documented decision itself is
wrong, an issue against [ARCHITECTURE.md](ARCHITECTURE.md) §9 is very welcome.

## Secrets policy for contributors

- `.env.example` files contain **placeholders and generation hints only**
  (`change-me-to-a-long-random-secret-32-bytes`, `1234567890:AA-your-token-here`).
  Never commit a `.env` file, a filled token, or any credential anywhere in
  this repository.
- Tests never use real keys, real bots or network access; they mock HTTP and
  use temporary directories (ARCHITECTURE.md §5, rule G-12).
- If you accidentally commit a secret: revoke/rotate it immediately at the
  provider side before cleaning history — removing it from git does not
  un-leak it.

## Scope

In scope: anything in the teaching code that contradicts its own
documentation, teaches an insecure pattern without saying so, or leaks
credentials committed to the repository.

Out of scope: the deliberate simplifications listed in the table above;
weak user-chosen inputs in demo flows; the absence of production features
(rotation, rate limiting, HTTPS) that every README explicitly disclaims.

## Supported versions

Only the latest state of `main` receives fixes. There are no release branches.
