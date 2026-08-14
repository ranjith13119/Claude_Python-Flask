# Log: Step 07 — Add Expense

Date: 2026-08-13
Branch: feature/add-expense
Status: implemented + tested (24/24 new, full suite 82/82)

## What was done

- `database/db.py`: added `create_expense(user_id, amount, category, date, description)` — parameterised `INSERT INTO expenses` via `get_db()`, returns `cur.lastrowid` (mirrors `create_user` style). No schema change — `expenses` table exists from Step 01.
- `app.py`: `/expenses/add` now GET+POST (replaces the Step 7 placeholder). Auth guard first: no `session["user_id"]` → 302 `/login`. POST validates in order: amount present + `float()` parses + `> 0`; category `in CATEGORIES` (imported from db.py — no duplicated list); date strict via `date.fromisoformat()` + not in the future. Any failure re-renders the form with `error` (first error wins) and inserts nothing. Success: `create_expense(...)` → 302 to landing (PRG). Description stripped, empty → `None` (NULL).
- `templates/add_expense.html`: extends `base.html`, reuses `auth-section`/`auth-card`/`auth-error`/`form-group`/`form-input`/`btn-submit` classes. Fields: amount (number, step 0.01, min 0.01), category `<select>` looping `categories` (no hardcoded list), date (`type="date"` defaulting to `today`), optional description. Zero hex, zero inline styles.
- `static/css/style.css`: added `.form-select` (matches `.form-input` look using `:root` vars) and `.form-optional` (muted label hint).

## Issues encountered

- None in app code. Tests all passed on first run (24/24).
- Notes: `.claude/plans/` is gitignored — the tracked plan mirror is `.opencode/plans/07-add-expense.md`.

## Verification

- `python -m pytest tests/test_07-add-expense.py -v` → 24/24 passed
- `python -m pytest -q` → 82/82 passed

## Next

- Ship: commit, push `feature/add-expense`, PR (squash-merge), delete branch.
- Step 08 (Edit expense) — `create_expense` pattern (parameterised write + validation + PRG) extends to `update_expense`/`delete_expense` in Steps 08/09.