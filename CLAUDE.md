# CLAUDE.md — Spendly (Claude Code companion to AGENTS.md)

Spendly: a Flask expense tracker built incrementally as a teaching project ("Steps 1–9").
This file is the roadmap + conventions reference that the `.claude/commands/` workflow depends on.

## Roadmap & Status

| Step | Feature | Spec | Status |
| --- | --- | --- | --- |
| 01 | Database Setup | `.claude/spec/01-database-setup.md` | ✅ Complete (tests: 15/15) |
| 02 | Registration | `.claude/spec/02-registration.md` | ✅ Complete (tests: 12/12) |
| 03 | Login / Logout | — | ⬜ Pending |
| 04 | Profile | — | ⬜ Pending |
| 05 | Backend connection | — | ⬜ Pending |
| 06 | Expense list | — | ⬜ Pending |
| 07 | Add expense | — | ⬜ Pending |
| 08 | Edit expense | — | ⬜ Pending |
| 09 | Delete expense | — | ⬜ Pending |

Specs live in `.claude/spec/` (mirrored in `.opencode/spec/`). Do not start a feature before its spec exists and is reviewed.

## Conventions

- No ORMs (no SQLAlchemy); **parameterized SQL only** — never string formatting in SQL.
- Passwords hashed with werkzeug (`generate_password_hash`) — current default prefix is `scrypt:`, not `pbkdf2:`.
- `PRAGMA foreign_keys = ON` on every connection (`get_db()` already does this).
- Amounts stored as REAL. Dates strict `YYYY-MM-DD`.
- CSS: use variables from `:root` in `static/css/style.css` — never hardcode hex colors.
- All templates extend `templates/base.html`; use `url_for()` for routes/static assets.
- Fixed expense categories: Food, Transport, Bills, Health, Entertainment, Shopping, Other (see `database/db.py::CATEGORIES`).
- Git: never commit directly to main; `feature/<slug>` branches, Conventional Commits, squash-merge, delete branches after merge.

## Testing (mandatory)

- **Every implemented feature MUST be tested before it is marked done.** Write `tests/test_<step>-<slug>.py` from the spec (Do NOT derive tests from the implementation), then run `python -m pytest tests/test_<step>-<slug>.py -v` until green. Never close a feature with failing tests.
- DB tests: monkeypatch `database.db.DB_PATH` to a tmp path — never write to the committed `expense_tracker.db` from tests.
- Demo credentials: demo@spendly.com / demo123.

## Schema (Step 01)

**users** — id INTEGER PK AUTOINCREMENT · name TEXT NOT NULL · email TEXT NOT NULL UNIQUE · password_hash TEXT NOT NULL · created_at TEXT DEFAULT datetime('now')

**expenses** — id INTEGER PK · user_id INTEGER NOT NULL FK→users.id · amount REAL NOT NULL · category TEXT NOT NULL · date TEXT NOT NULL (YYYY-MM-DD) · description TEXT nullable · created_at TEXT DEFAULT datetime('now')

## Run

- `python app.py` → dev server on **port 5001** (not 5000), debug on. DB (`expense_tracker.db`, local-only, gitignored since PR #2) is created/seeded idempotently on startup.
- `python -m pytest` runs the suite.

## Gotchas

- README.md is UTF-16 LE — read with `Get-Content -Encoding Unicode` / `iconv -f UTF-16`.
- `file.md` at root is junk (stray terminal capture) — ignore.
- Commands reference `.claude/specs/` (plural); the actual folder is `.claude/spec/` (singular) — reconcile naming when convenient.