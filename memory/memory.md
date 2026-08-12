# Spendly Project Memory

Log of important implementation decisions and conversation outcomes.

## Project rule (user-mandated)

- **Always test a feature once it is implemented** — write `tests/test_<step>-<slug>.py` from the spec and run `python -m pytest ... -v` until green before marking done. Recorded in CLAUDE.md and AGENTS.md.

## 2026-08-12 — Step 01 Database Setup (implemented + tested)

- `database/db.py` fully implemented: `get_db()` (sqlite3.Row + `PRAGMA foreign_keys=ON`), `init_db()` (IF NOT EXISTS users/expenses), `seed_db()` (idempotent demo data).
- DB file: `expense_tracker.db` at project root — user removed it from `.gitignore` mid-Step-01: **decisely committed to git** (user wants the DB tracked; regenerate/reseed is still idempotent on startup). Note: committing binary DBs will cause merge conflicts on schema changes.
- Demo login: demo@spendly.com / demo123 (werkzeug `scrypt:` hash — werkzeug 3.x default, NOT `pbkdf2:`).
- Seed: 1 user + 8 expenses covering all 7 fixed categories (`CATEGORIES` constant in db.py), dates spread across current month, YYYY-MM-DD.
- `app.py`: `init_db()` + `seed_db()` in `app.app_context()` inside `__main__` (not at import time).
- Verified: idempotent across runs, FK + UNIQUE enforced, app boots HTTP 200 on :5001.
- Tests: `tests/test_01-database-setup.py` — 15/15 pass (DB file creation, schema/constraints, seed data, idempotency, FK/UNIQUE, app startup). Tests monkeypatch `db.DB_PATH` to tmp — never touch the committed DB from tests.
- CLAUDE.md created (roadmap with step status, conventions, schema, mandatory-test rule) — the `.claude/commands` files can now reference it.
- Branch: `feature/database-setup`. Plan: `.claude/plans/01-database-setup.md` with a mirror copy in `.opencode/plans/01-database-setup.md` (keep both in sync; mirrors the spec-folder pattern).
- Known inconsistency: commands reference `.claude/specs/` (plural) but folder is `.claude/spec/` (singular); `.opencode/spec/` holds a copy. To reconcile later.
- When testing hash prefixes: werkzeug ≥3.x default method is `scrypt:`, assertions must accept both `pbkdf2:`/`scrypt:`.