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
## 2026-08-12 - Step 04 Profile Page (static UI, implemented + tested)

- Spec was REVISED by user after initial draft: UI-first design - hardcoded data, NO DB queries this step; Step 05 "Backend connection" wires real data into these templates later.
- pp.py: /profile replaced stub - session guard (302 to /login when logged out) + render_template with hardcoded context (name/email/member_since, stats, 3 transactions, 4-category breakdown with percents).
- 	emplates/profile.html: 4 sections - avatar initials (Jinja first-char map), user info card, 3 stat cards, transaction table with .cat-badge, category breakdown with progress bars. No inline styles; bar widths via exact-value classes .pct-14/23/25/38.
- static/css/style.css: appended Profile block - all :root variables, zero hex (spec rule incl. test that scans template for hex).
- Tests: 	ests/test_04-profile.py - 11/11 (guard 302/200, 4 sections present, navbar state, no password hash, hex-free + extends-base file checks). Full suite 58/58.
- Branch: eature/profile. Spec mirrored in .opencode/spec/. Plans in both plans folders. Pending remainder: commit/push/PR already part of ship flow.
