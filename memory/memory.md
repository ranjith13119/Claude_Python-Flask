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

## 2026-08-12 — Step 02 Registration (implemented + tested)

- User reversed the Step-01 DB decision (PR #2, `chore: stop tracking the local database file`): `expense_tracker.db` is now **gitignored, local-only** (updated AGENTS.md/CLAUDE.md accordingly in PR #3).
- `database/db.py`: added `create_user(name, email, password)` — parameterized INSERT, werkzeug `scrypt:` hash, returns `lastrowid`; `sqlite3.IntegrityError` propagates (route catches).
- `app.py`: `/register` now GET+POST. POST validates (all fields required, password ≥ 8 chars), normalizes email to lowercase, catches IntegrityError → "An account with this email already exists"; success = 302 redirect to `/login` (POST-Redirect-GET). Added `app.secret_key` from `SPENDLY_SECRET_KEY` env var (dev fallback) — foundation for Step 03 sessions.
- `templates/register.html`: form action → `url_for('register')`. No new templates/CSS classes needed.
- Tests: `tests/test_02-registration.py` — 12/12 pass (page renders, redirect, row created, hash verifies, lowercase email, dup/short/empty/whitespace errors). Full suite 27/27.
- Branch: `feature/registration`. Spec: `.claude/spec/02-registration.md` (+ `.opencode/spec/` copy). Plans mirrored in both plans folders.
- Gotcha: flask test client needs `init_db()` run first — tables only exist after `python app.py` startup block.

## 2026-08-12 — Step 03 Login / Logout (implemented + tested)

- `database/db.py`: added `get_user_by_email(email)` and `get_user_by_id(user_id)` — parameterized SELECT, return sqlite3.Row or None.
- `app.py`: `/login` GET+POST — lowercase-normalized email, `check_password_hash`, generic "Invalid email or password" for wrong-password AND unknown-email AND empty fields (never reveals which failed); success `session["user_id"]` → 302 to landing. `/logout` now POST-only (CSRF-safe), `session.clear()` → 302. Added `@app.context_processor inject_current_user` → `current_user` (user row or None) for all templates. GET /logout = 405.
- `templates/base.html`: session-aware navbar — logged in: email + Log out POST form button (new `.nav-user`/`.nav-logout` CSS using vars from `:root`); logged out: Sign in / Get started. `login.html`: form action → `url_for('login')`.
- Key decision (user: "Always perform the best action"): POST-only logout (CSRF-safe), context processor for current_user (reused by Step 04 Profile), stale/invalid session user_id renders logged-out without crash or session mutation.
- Tests: `tests/test_03-login-logout.py` — 17/17 pass (form render, redirect, session persistence, navbar states, case-insensitive email, generic errors, logout 302/405, stale session). Full suite 44/44.
- Branch: `feature/login-logout`. Spec: `.claude/spec/03-login-logout.md` (+ `.opencode/spec/` mirror). Plans mirrored in both plans folders.


## 2026-08-13 — Rollback to Step 03 (user-mandated)

- User reported UI "completely distorted, no CSS applied, was good till spec 3". Root cause: the Step 05 frontend-design-skill UI refactor (new palette/typography) broke the tested look.
- Action: rolled the repo back to the pre-Spec-04 baseline (commit `dd7dd29` tree) on branch `feature/backed-connection` as commit `f3b5849`: restored app.py/db.py/style.css/memory.md, deleted templates/profile.html, tests/test_04-profile.py, test_05-profile.py, 04-profile specs+plans (.claude/.opencode), file.md.
- frontend-design skill is BANNED by user for this project — removed `.claude/memory/tools/frontend-design.md` and `domain/Frontend.md`.
- IMPORTANT: the rollback commit lives on `feature/backed-connection`; main still contains Step 04 code. Feature branches for rebuilt steps must be based on `f3b5849` (or a future merge of it), NOT on main — verified when creating `feature/profile`.

## 2026-08-13 — Step 04 Profile static UI (rebuilt after rollback, implemented + tested)

- Rebuilt from scratch on branch `feature/profile`, based on rollback commit `f3b5849` (clean Step 03 state).
- `app.py`: `/profile` session guard (302 → /login when logged out) + `render_template("profile.html", ...)` with hardcoded context — Demo User / demo@spendly.com / "March 2026", stats (₹12,450 / 24 / Food), 3 transactions, 4-category breakdown (38/25/14/23). No DB calls; Step 05 wires real data.
- `templates/profile.html`: identity header with avatar initials via `{{ name.split() | map("first") | join("") | upper }}`, account card, 3 stat cards, transactions table with `.cat-badge`, breakdown with exact-value `.bar-fill.pct-{n}` progress bars. Extends base.html; zero hex, zero inline styles.
- `static/css/style.css`: appended Profile block — `.profile-*`, `.avatar`, `.stat-card`, `.expenses-table`, `.cat-badge`, `.bar-track/.bar-fill`, `.breakdown-*`; all colors from `:root`; responsive at 600px.
- Tests: `tests/test_04-profile.py` — 12/12 (access control 302/200, identity, stat cards, table columns, breakdown percents, navbar state, no hash leak, extends base.html, no hex/inline styles). Full suite 59/59.
- Template-rule tests only assert `{% extends "base.html" %}` + no hex + no inline styles — url_for lives in base.html, not per-template (learned: don't assert url_for() inside child templates).
- Spec: `.claude/spec/04-profile.md` (+ `.opencode/spec/` mirror). Plans in both plans folders; `Logs/04-profile.md` created.

## 2026-08-13 — Step 05 Backend Connection (implemented + tested)

- `database/db.py`: added `get_expenses_by_user_id(user_id)` — parameterized `SELECT ... WHERE user_id = ? ORDER BY date DESC`, returns list of sqlite3.Row.
- `app.py`: `/profile` now fully live — session guard kept, stale-session redirect, computes total_spent / transaction_count / top_category (max category total, `-` when none) / transactions / category_breakdown (₹ totals + integer percents) / member_since from created_at. Helpers: `format_rupee()` (`₹{:,.2f}`) + `build_category_breakdown()` (CATEGORIES order, deterministic ties).
- `static/css/style.css`: extended `.bar-fill.pct-N` 0–100 so live percents render (was only 14/23/25/38).
- Template `profile.html` unchanged — Step 04 design preserved, dict-style access (`stats["total_spent"]`, `tx["date"]`).
- Seed data note: top category is **Shopping** (₹79.99), not Food.
- Tests: `tests/test_05-backend-connection.py` — 15/15 pass. Updated `test_04-profile.py` hardcoded assertions (March 2026 → Member since, ₹12,450 → ₹294.64, 38%/25%/14%/23% → 26%/27%/20%) since Step 05 makes data live. Full suite 74/74.
- Branch: `feature/backend-connection`. Spec: `.claude/spec/05-backend-connection.md` (+ `.opencode/spec/`). Plan: `.opencode/plans/05-backend-connection.md` (`.claude/plans/` is gitignored). Log: `Logs/05-backend-connection.md`.
- Stashed agents/commands (test-writer/quality-reviewer/security-reviewer/test-runner, code-review command) restored from stash — committed on this branch as separate chore commit.

## 2026-08-13 — Step 06 Date Filter for Profile Page (implemented + tested)

- `app.py` `/profile`: `from_date`/`to_date` query params — `valid_date()` helper (strptime `%Y-%m-%d`; malformed/out-of-range ignored → treated as absent), inclusive range filter via string compare on the transactions list (new list, original untouched), params echoed back to template.
- `templates/profile.html`: GET filter form above "Recent transactions" (two date inputs, Filter button, Reset link), Jinja `{% else %}` empty state ("No transactions in this date range." vs "No transactions yet.").
- `static/css/style.css`: `.filter-form`/`.filter-field`/`.filter-btn`/`.filter-reset`/`.filter-empty` block — `:root` vars only, responsive at 600px.
- Filter only affects the transactions table; stats + breakdown stay full-range.
- Tests: `tests/test_06-date-filter-profile.py` — 18/18 (form render, from/to/both/boundary filtering, empty state, invalid dates ignored + inputs cleared, prefill, reset link, 302 guard, stats unaffected, template rules). Full suite 92/92.
- Test gotcha: seed's oldest expense is `today-7` — a `to_date` boundary test must use `today-7`, not `today-8`.
- Branch: `feature/date-filter-profile` (fast-forward merged from `feature/backend-connection` so 06 builds on live-data profile). Spec: `.claude/spec/06-date-filter-profile.md` (+ `.opencode/spec/`). Plan mirrored to `.opencode/plans/`. Log: `Logs/06-date-filter-profile.md`.
- CLAUDE.md roadmap: Step 06 title updated from "Expense list" to "Date filter for profile page".

## 2026-08-13 - Step 07 Add Expense (implemented + tested)

- Built on main (Steps 01-04). NOTE: Steps 05/06 (backend connection, date filter) live on unmerged branch feature/date-filter-profile - this branch does NOT include them.
- database/db.py: added create_expense(user_id, amount, category, date, description) - parameterised INSERT, returns lastrowid; no schema change.
- app.py: /expenses/add now GET+POST; auth guard (302 /login), validation order: amount (float > 0) then category in CATEGORIES (imported, no dup list) then date (date.fromisoformat strict, not future); first error re-renders with error, inserts nothing; success 302 landing (PRG). Description empty -> NULL.
- templates/add_expense.html: reuses auth-section/auth-card/form-group/form-input/btn-submit classes; category dropdown loops CATEGORIES; date defaults to today via today=date.today().isoformat(). Zero hex/inline styles.
- style.css: added .form-select (matches .form-input via :root vars) + .form-optional.
- Tests: tests/test_07-add-expense.py - 24/24 (access control GET/POST 302, form render + 7 categories + today default, valid insert w/ correct user_id + NULL description, 9 invalid variants -> 200 error + no insert, template rules). Full suite 82/82. First-run green.
- Spec: .claude/spec/07-add-expense.md; plan mirrored at .opencode/plans/07-add-expense.md (.claude/plans/ is gitignored); Log: Logs/07-add-expense.md. Branch: feature/add-expense.
- Decision: no nav link to the add form yet - Step 08/09 will add nav once list/edit exist. Amount stored as REAL.

## 2026-08-14 — Steps 08-10 Edit/Delete/Monthly Earnings (implemented + tested, 172/172)

- Branch: feature/crud-earnings, based on feature/add-expense (which now includes Steps 01-07 after merge of feature/date-filter-profile).
- db.py: added earnings table to SCHEMA (id, user_id FK, month YYYY-MM, amount REAL NOT NULL, created_at, UNIQUE(user_id, month); CREATE TABLE IF NOT EXISTS so existing local DBs pick it up on startup). New fns: get_expense_by_id, update_expense, delete_expense, upsert_earnings (INSERT..ON CONFLICT(user_id,month) DO UPDATE — same-month save overwrites, never duplicates), get_earnings_by_user_id (ORDER BY month DESC).
- app.py: extracted shared validate_expense_input(amount_raw, category, date_raw) used by add AND edit (same error strings as Step 07); /expenses/<int:id>/edit GET+POST (ownership check → 404 for missing OR foreign; pre-filled form; PRG to /profile); /expenses/<int:id>/delete POST-only, route fn named delete_expense_route (avoids clash with imported db fn delete_expense — url_for must use that name); /earnings POST (month regex r"\d{4}-\d{2}" + date.fromisoformat(month+"-01") double check — catches 2026-13 AND non-ASCII digits; amount same rule as expenses; failure re-renders profile with earnings_error via refactored render_profile(error=None), no write). profile() → render_profile(error=None); build_monthly_comparison(expenses, earnings_rows) — union of months, sorted DESC, net only when both exist.
- IMPORTANT security fix (review finding): float("nan")/float("inf") pass an "amount > 0" check (NaN comparisons always False); sqlite3 binds NaN as NULL → IntegrityError on NOT NULL REAL column → 500. All amount validations now use math.isfinite(amount) first; nan/inf regression cases in test_08 + test_10 invalid-input lists.
- Templates: edit_expense.html (pre-filled, reuses auth-*/form-* classes); profile.html — actions column (Edit link + Delete inline POST form), "Add expense" button in card header, Monthly earnings card (month type="month" default current month + comparison table Month|Earnings|Spent|Net with net-positive/net-negative); base.html — "Add expense" nav link (class nav-link, styled by existing .nav-links a). CSS: .card-header/.btn-sm/.btn-danger-sm/.inline-form/.table-actions/.earnings-* — :root vars only.
- Tests: test_08 23/23, test_09 10/10, test_10 19/19 — from specs; ownership (second-user fixture via db.create_user), 404-vs-405 semantics, upsert count stays 1, spent computed from DB (date-robust, don't hardcode 294.64 when today ≤ 7th — seed offsets cross months), month_spent helper uses substr(date,1,7). Full suite 172/172.
- Reviewer subagents (quality-reviewer/security-reviewer) failed in this environment ("Model not found: claude-sonnet-4-6/") — review done inline by main agent instead; note for future sessions.
- Specs .claude/spec/08-10 (+ .opencode/spec/ mirrors); plan .claude/plans/08-10-crud-earnings.md + .opencode/plans/ mirror; Logs/08-10 created.
