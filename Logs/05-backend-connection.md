# Log: Step 05 — Backend Connection

Date: 2026-08-13
Branch: feature/backend-connection
Status: implemented + tested (15/15 new, full suite 74/74)

## What was done

- `database/db.py`: added `get_expenses_by_user_id(user_id)` — parameterized `SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC`, returns list of sqlite3.Row (empty when none).
- `app.py`: rewrote `/profile` route to load live data — session guard kept; stale session (user_id with no row) redirects to `/login`; computes `total_spent` (₹-formatted sum), `transaction_count`, `top_category` (max category total, `-` when none), `transactions` list, `category_breakdown` (per-category ₹ totals + integer percents via `build_category_breakdown()` helper), `member_since` derived from `created_at` (`%B %Y`).
- `app.py` helpers: `format_rupee()` (`₹{:,.2f}`) and `build_category_breakdown()` (iterates `CATEGORIES` order for deterministic top-category ties).
- `static/css/style.css`: extended `.bar-fill.pct-N` exact-value classes from 4 (14/23/25/38) to 0–100 so arbitrary live percentages render; additive only, no hex, uses existing `:root` vars.
- Template unchanged (`profile.html` Step 04 design preserved — same variable names, dict-style access).

## Issues encountered

- Full-suite failures after wiring live data: `test_04-profile.py` still asserted Step 04 hardcoded values (`March 2026`, `₹12,450`, `38%/25%/14%/23%`). Updated to assert real computed values (`Member since`, `₹294.64`, `>8<`, `Shopping`, `26%/27%/20%`). Root cause: Step 04 spec's DoD asserted static demo values by design; Step 05 intentionally replaces them.
- Seed data top category is **Shopping** (₹79.99), not Food — max category total wins.

## Verification

- `python -m pytest tests/test_05-backend-connection.py -v` → 15/15 passed
- `python -m pytest -q` → 74/74 passed

## Next

- Ship: commit (Conventional Commits), push `feature/backend-connection`, PR (squash-merge), delete branch.
- Step 06 (Date filter for profile page) filters the same `transactions` list this route now builds from real data.
