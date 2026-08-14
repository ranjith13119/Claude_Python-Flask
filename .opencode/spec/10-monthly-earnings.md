# Spec: Monthly Earnings

## Overview
This feature adds the income side of the ledger: a logged-in user can record how much they earned in any month, and the profile page shows a month-by-month comparison of earnings vs expenses (net = earnings − spent). A new `earnings` table stores one amount per user per month (`YYYY-MM`), upserted on save so re-entering a month overwrites instead of duplicating. This is the first summary/comparison feature and gives the app its core "track vs budget/income" value prop. It is the final step of the current roadmap (Steps 08/09 complete the expense lifecycle; this closes the income loop).

## Depends on
- Step 1: Database setup — schema pattern, `get_db()`, seed conventions.
- Step 3: Login / Logout — session guard, POST-only action pattern.
- Step 5: Backend connection — live-data `/profile` with `get_expenses_by_user_id`.
- Step 7: Add expense — validation + PRG patterns.

## Routes
- `POST /earnings` — upsert the logged-in user's earnings for a month, then redirect to `/profile` — logged-in only
- `GET /profile` (modified) — additionally computes and passes a monthly comparison list

## Database changes
New table `earnings` (added to `SCHEMA` — safe for existing DBs via `CREATE TABLE IF NOT EXISTS`):
- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `user_id INTEGER NOT NULL` FK → users.id
- `month TEXT NOT NULL` (strict `YYYY-MM`)
- `amount REAL NOT NULL`
- `created_at TEXT NOT NULL DEFAULT (datetime('now'))`
- `UNIQUE (user_id, month)` — one earnings row per user per month

New data-layer functions in `database/db.py`:
- `upsert_earnings(user_id, month, amount)` — `INSERT ... ON CONFLICT(user_id, month) DO UPDATE SET amount = excluded.amount`
- `get_earnings_by_user_id(user_id)` — parameterised `SELECT * FROM earnings WHERE user_id = ? ORDER BY month DESC`

## Templates
- **Modify:** `templates/profile.html`:
  - New **"Monthly earnings"** section: a small POST form (`action="{{ url_for('earnings') }}"`) with a month input (`type="month"`, default current month) and an amount input, plus a comparison table listing each month that has earnings or expenses: Month | Earnings | Spent | Net (positive → green tint, negative → danger tint via CSS variables).
  - Add an "Add expense" button linking to `url_for('add_expense')` (visible entry point for Step 07).
- **Modify:** `templates/base.html` — logged-in navbar gains an "Add expense" link to `url_for('add_expense')`.

## Files to change
- `database/db.py` — add `earnings` table to `SCHEMA`, add `upsert_earnings()`, `get_earnings_by_user_id()`
- `app.py`:
  - New `POST /earnings` route: session guard; validate month (regex `^\d{4}-\d{2}$` plus real-date check via `date.fromisoformat(month + "-01")`) and amount (`float`, `> 0`); on failure re-render `/profile` with an earnings error (redirect back to profile and render with error is not possible on POST → re-render `profile.html` with error context, or simpler: redirect to profile — spec decision below); on success `upsert_earnings(...)` → redirect to `url_for("profile")`
  - `profile()`: build monthly comparison — group expenses by `date[:7]`, merge with earnings rows (same month), compute `earnings` (or 0/None), `spent`, `net`; sort by month descending; pass to template along with `current_month`
- `static/css/style.css` — `.earnings-*` section styles, `.btn-sm`, `.btn-danger-sm`, `.net-positive`/`.net-negative` (CSS variables only)

## Files to create
No new template files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw sqlite3 via `get_db()` only
- Parameterised queries only — never string-format SQL
- Use CSS variables — never hardcode hex values; no inline styles
- All templates extend `base.html`; use `url_for()` for routes/static assets
- Month stored strictly as `YYYY-MM`; validated server-side (format + real month)
- Earnings amount follows the expense amount rules (positive number)
- Comparison is read-only aggregation of `expenses` + `earnings` — no new writes on GET
- Empty state: months with no data are not listed; if nothing at all, show a friendly empty row
- On successful POST → redirect (PRG)

## Definition of done
- [ ] `POST /earnings` without being logged in redirects to `/login`
- [ ] Saving earnings for a month inserts a row with the correct user_id, month and amount
- [ ] Saving the same month again overwrites the amount (still exactly one row for that user+month)
- [ ] Saving an invalid month (`2026-13`, `abc`, empty) or non-positive amount fails gracefully (no row, error shown, 200)
- [ ] `/profile` shows the earnings form with the current month pre-filled
- [ ] `/profile` comparison table lists months with earnings and/or expenses with Earnings, Spent and Net values correct for the seed data (e.g. current month: earnings added by user, spent ₹294.64, net = earnings − 294.64)
- [ ] The navbar and profile page offer an "Add expense" link for logged-in users
- [ ] No hex colour values or inline styles in the new template markup