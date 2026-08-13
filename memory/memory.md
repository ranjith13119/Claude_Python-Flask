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