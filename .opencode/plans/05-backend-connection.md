# Plan: Step 05 — Backend Connection

Branch: `feature/backend-connection` (based on `d237e2e` / Step 04 state; spec already at `.claude/spec/05-backend-connection.md`)

## Steps

1. **database/db.py — add `get_expenses_by_user_id(user_id)`**
   - Parameterized `SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC`
   - Returns list of `sqlite3.Row` (empty list when none)

2. **app.py — rewrite `/profile` route (live data)**
   - Keep session guard: `if session.get("user_id") is None: return redirect(url_for("login"))`
   - `user = get_user_by_id(session["user_id"])`; if None → `redirect(url_for("login"))` (stale session)
   - `expenses = get_expenses_by_user_id(user["id"])`
   - Compute:
     - `total_spent` = sum of amounts, ₹-formatted with thousands separators (2 decimals, e.g. `₹294.64`)
     - `transaction_count` = len(expenses)
     - `top_category` = category with highest total amount; `"-"` when no expenses
     - `transactions` = [{date, description, category, amount(₹-formatted)}] from rows
     - `category_breakdown` = per-category total (₹-formatted) + integer percent (`round(total/cat_total*100)`), `"-"`/empty when no expenses
     - `member_since` = `created_at` parsed to `"%B %Y"` (e.g. "August 2026")
   - Render `profile.html` with Step 04's variable names: `name`, `email`, `member_since`, `stats` (dict), `transactions`, `category_breakdown`
   - Helper for ₹ formatting + category aggregation — keep inside `app.py` (module-level `_format_rupee` / `_build_category_breakdown` if it keeps the route readable)

3. **static/css/style.css — extend pct classes**
   - Current `.bar-fill.pct-*` exists only for 14/23/25/38 (Step 04 hardcoded values). Real data produces arbitrary percents (seed: 26/8/20/7/7/27/4), so add exact-value `.bar-fill.pct-N { width: N%; }` for N in 0..100 (only values, using existing `:root` vars — no hex)
   - No layout/design changes — additive only

4. **tests/test_05-backend-connection.py** (create, from spec — 11 tests)
   - Fixtures: `fresh_db` (tmp DB_PATH + init/seed), `client` (TESTING), `login()` helper (POST /login)
   - Access control: logged-out 302 → /login; logged-in 200
   - Content: real name/email (not hardcoded-only), stats computed from seeded expenses (sum/count/top category Food), transactions table shows seeded expense descriptions, category breakdown shows seeded categories with computed percents via `pct-*` classes, `member_since` month derived from `created_at`
   - Edge cases: user with zero expenses → 200 with ₹0 / 0 / "-" (no crash); stale session (user_id without row) → 302 /login
   - Template rules: no `password`/`scrypt:` in body, no hex in profile.html, extends base.html, no inline styles

5. **Verify** — `python -m pytest tests/test_05-backend-connection.py -v` (all green), then full suite `python -m pytest -q` (stays green)

6. **Docs** — plan mirrored to `.opencode/plans/05-backend-connection.md`; `Logs/05-backend-connection.md` per AGENTS.md; update `memory/memory.md` + `.claude/memory/` index; update CLAUDE.md roadmap (Step 05 → complete)

7. **Ship** — commit on `feature/backend-connection` (Conventional Commits; separate commit for the restored agents/commands/docs files if they are unrelated to Step 05), push, PR (squash-merge convention)

## Notes / decisions

- Template unchanged: `profile.html` from Step 04 already uses `stats["total_spent"]` / `tx["date"]` dict-style access — pass dicts with exactly those keys
- Percent rounding: `round()` per category (integer); bars render via the extended `.pct-N` set; percents of one category may not sum to exactly 100 (spec allows)
- Top category tie-break: first category with the max total, iterating in `CATEGORIES` order for determinism
- Amount format: `₹{:,.2f}` (seeded amounts have cents, e.g. 14.5 → `₹14.50`)
- `member_since`: seed `created_at` is UTC `datetime('now')` — parse with `datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")`; fallback to raw string if format differs (never crash)
- The restored stash (agents, commands, code-review files) belongs on this branch too — commit separately as `chore: ...` so Step 05 changes stay reviewable
- Old attempt `979fa69` (reverted in `f3b5849`) had 11 tests using `profile-table` class — the current redesigned template uses `expenses-table`; tests must assert against the CURRENT template classes
