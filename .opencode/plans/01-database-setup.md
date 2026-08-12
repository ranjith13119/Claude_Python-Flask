# Implementation Plan — 01-database-setup

**Branch:** `feature/database-setup`
**Spec:** `.claude/spec/01-database-setup.md` (identical copy in `.opencode/spec/`)
**Status:** Implemented + verified 2026-08-12

## Plan

1. Branch: `git checkout -b feature/database-setup` from clean `main` ✔
2. `database/db.py`: implement `get_db()` (sqlite3.Row, `PRAGMA foreign_keys=ON`), `init_db()` (`CREATE TABLE IF NOT EXISTS` users/expenses), `seed_db()` (idempotent — early return if users exist; demo user demo@spendly.com / demo123 via werkzeug; 8 expenses across all 7 fixed categories, dates spread across current month). DB at project root `expense_tracker.db` (gitignored; regenerated on startup). ✔
3. `app.py`: import `init_db`/`seed_db`, call both inside `app.app_context()` in `__main__` before `app.run()`. Routes untouched. ✔

## Verification performed

- Script: init/seed ×2 across runs → 1 user / 8 expenses (no duplication) ✔
- Password is werkzeug-hashed (`scrypt:...`) and verifies against `demo123` ✔
- All 7 categories present, all dates `YYYY-MM-DD`, all expenses linked to demo user ✔
- FK violation on invalid `user_id` → `IntegrityError` ✔
- Duplicate email → `IntegrityError` (UNIQUE) ✔
- `python app.py` boots, GET / → HTTP 200 ✔

## Follow-ups

- `/test-feature 01-database-setup` to generate `tests/test_01-database-setup.py`
- Note: commands reference `.claude/specs/` (plural); actual folder is `.claude/spec/` (singular) — reconcile naming alongside `.opencode/spec/`.