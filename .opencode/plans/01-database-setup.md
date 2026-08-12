# Implementation Plan — 01-database-setup

**Branch:** `feature/database-setup`
**Spec:** `.claude/spec/01-database-setup.md` (identical copy in `.opencode/spec/`)
**Status:** Implemented + verified 2026-08-12

## 1. Goal

Replace the stub in `database/db.py` with a working SQLite data layer (schema + idempotent seeding) and wire it into `app.py` startup. All later features (auth, expenses CRUD) build on this.

## 2. Prerequisites

- Python 3 + `pip install -r requirements.txt` (flask, werkzeug, pytest, pytest-flask)
- Clean `main` checked out

## 3. Branch strategy

- Create `feature/database-setup` from `main`
- Never commit to `main` directly
- Single Conventional Commit, squash-merge PR to `main`, delete branch after merge

## 4. Database file location

- `expense_tracker.db` at project root (next to `app.py`/`database/`)
- Path is derived, not hardcoded: `Path(__file__).resolve().parent.parent / "expense_tracker.db"` so it stays correct regardless of working directory
- Reseeded idempotently on every `python app.py` start
- Local-only: listed in `.gitignore` (untracked since PR #2)

## 5. Schema — two tables

### `users`

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| name | TEXT | NOT NULL |
| email | TEXT | NOT NULL, UNIQUE |
| password_hash | TEXT | NOT NULL |
| created_at | TEXT | DEFAULT (datetime('now')) |

### `expenses`

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| user_id | INTEGER | NOT NULL, FK → users.id |
| amount | REAL | NOT NULL |
| category | TEXT | NOT NULL |
| date | TEXT | NOT NULL (YYYY-MM-DD) |
| description | TEXT | nullable |
| created_at | TEXT | DEFAULT (datetime('now')) |

Notes:
- Use `CREATE TABLE IF NOT EXISTS` → re-running `init_db()` is safe
- Enforce FK with `PRAGMA foreign_keys = ON` on every connection (SQLite defaults it OFF)

## 6. Function-by-function implementation (`database/db.py`)

### 6.1 Imports & constants

- `sqlite3`, `date`/`timedelta` from `datetime`, `Path` from `pathlib`
- `generate_password_hash` from `werkzeug.security`
- `DB_PATH` = project root / `expense_tracker.db`
- `CATEGORIES` = exactly: Food, Transport, Bills, Health, Entertainment, Shopping, Other (7 fixed values from spec §10)
- `SCHEMA` = single string with both `CREATE TABLE IF NOT EXISTS` statements

### 6.2 `get_db()`

1. `sqlite3.connect(DB_PATH)` — creates file if missing
2. `conn.row_factory = sqlite3.Row` → dictionary-like access (`row["col"]`)
3. `conn.execute("PRAGMA foreign_keys = ON")`
4. Return `conn`

### 6.3 `init_db()`

1. `with get_db() as conn:` (context manager commits/rolls back + closes)
2. `conn.executescript(SCHEMA)`
3. Idempotent: safe to call multiple times

### 6.4 `seed_db()`

1. Open connection; check `SELECT COUNT(*) FROM users` → if count > 0, return early (no duplication)
2. INSERT demo user: `Demo User` / `demo@spendly.com` / `generate_password_hash("demo123")` (werkzeug current default `scrypt:...`)
3. Fetch demo user's `id` back via `SELECT id FROM users WHERE email = ?`
4. INSERT 8 sample expenses via `executemany` with parameterized queries:
   - 8 entries spanning all 7 categories (Food ×2, one for each remaining category)
   - Dates = `date.today() - timedelta(days=offset)` formatted ISO (`YYYY-MM-DD`), offsets 0–7 spread across current month
   - All rows reference demo user's `user_id`
   - `amount` as REAL (floats), `description` as text

Rules: parameterized queries only (`?` placeholders), never f-strings/`%` in SQL. No ORM.

## 7. Changes to `app.py`

1. Add import: `from database.db import init_db, seed_db`
2. In `if __name__ == "__main__":` block, before `app.run(debug=True, port=5001)`:
   - `with app.app_context(): init_db(); seed_db()`
3. All existing placeholder routes stay untouched

## 8. Edge cases & error handling expectations

| Scenario | Expected |
| --- | --- |
| Duplicate email insert | `sqlite3.IntegrityError` (UNIQUE constraint) |
| Expense with invalid `user_id` | `sqlite3.IntegrityError` (FK constraint) — only if `PRAGMA foreign_keys=ON` |
| `seed_db()` run twice | No duplicates (early return) |
| `init_db()` run twice | No error (IF NOT EXISTS) |
| DB file missing | Created automatically by `sqlite3.connect` |
| Invalid query | Clear `sqlite3` error raised for debugging (no silent swallowing) |

## 9. Definition of done (from spec §14)

- [x] Database file is created on app startup
- [x] Both tables exist with correct schema and constraints
- [x] Demo user exists with hashed password
- [x] 8 sample expenses exist across categories
- [x] No duplicate seed data on repeated runs
- [x] App starts without errors
- [x] Foreign key enforcement works
- [x] All queries use parameterized SQL

## 10. Verification — manual checks

1. Run `init_db()` + `seed_db()` twice across separate interpreter runs → 1 user / 8 expenses, no duplication ✔
2. Check password hash starts with `scrypt:` and `check_password_hash` verifies `demo123` ✔
3. Query expenses → all 7 categories present, all dates match `YYYY-MM-DD`, all rows have demo `user_id` ✔
4. Inject invalid `user_id` → `IntegrityError` ✔
5. Re-insert demo email → `IntegrityError` ✔
6. `python app.py` → boots on 5001, `GET /` returns 200 ✔

## 11. Verification — automated tests (once written)

- `tests/test_01-database-setup.py` with 15 tests (see existing file)
- Tests must monkeypatch `database.db.DB_PATH` to a tmp path — never touch the committed/real `expense_tracker.db`
- Command: `python -m pytest tests/test_01-database-setup.py -v`

## 12. Ship steps (summary)

1. Commit on `feature/database-setup`: `feat: set up sqlite database with demo seed data`
2. Push `-u origin`, open PR → title: "Add database setup with demo seed data"
3. Squash-merge, delete remote branch, switch to `main`, delete local branch

## Follow-ups

- Generate `tests/test_01-database-setup.py` via `/test-feature 01-database-setup` (done — 15 tests, green)
- Note: commands reference `.claude/specs/` (plural); actual folder is `.claude/spec/` (singular) — reconcile naming alongside `.opencode/spec/`