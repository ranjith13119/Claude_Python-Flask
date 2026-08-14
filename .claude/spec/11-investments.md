# Spec: Investment Tracking

## Overview
This feature lets a logged-in user capture their investments (Mutual Funds, Stocks, Gold, Bonds, Crypto, Real Estate, etc.) so the app can report the three sides of the ledger: earnings, expenses, and investments. Two changes work together:

1. **"Investment" becomes an expense category** — buying gold/MF/stocks is money out, so it is recorded like any expense (counts in Spent; category breakdown shows it like the others).
2. **A new `investments` table captures the asset side** — one row per purchase with a type, amount, date and optional note. The profile page gets an "Investments" card (add form + list + by-type breakdown + total invested stat) and the monthly comparison table gains an "Invested" column (Month | Earnings | Spent | Invested | Net).

Net stays `earnings − spent` (investment purchases already flow through Spent — no double counting); the Invested column is informational, showing what the user put into assets that month.

## Depends on
- Step 1: Database setup — schema pattern, `get_db()`, seed conventions.
- Step 3: Login / Logout — session guard, POST-only action pattern.
- Step 5: Backend connection — live-data `/profile`.
- Step 7: Add expense — validation + PRG patterns.
- Step 10: Monthly earnings — `render_profile()` refactor, `build_monthly_comparison()`, earnings card on profile.

## Routes
- `POST /investments` — add an investment for the logged-in user, then redirect to `/profile` — logged-in only
- `GET /profile` (modified) — additionally computes total invested, investment list, by-type breakdown, and an "Invested" column in the monthly comparison

## Database changes
1. `CATEGORIES` in `database/db.py` gains `"Investment"` (now 8 categories — affects the expense category dropdowns on add/edit, which loop `CATEGORIES`; no template change needed there).
2. New constant `INVESTMENT_TYPES = ["MF", "Stocks", "Gold", "Bonds", "Crypto", "Real Estate", "Other"]`.
3. New table `investments` (added to `SCHEMA` — safe for existing DBs via `CREATE TABLE IF NOT EXISTS`):
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `user_id INTEGER NOT NULL` FK → users.id
   - `type TEXT NOT NULL` (must be in `INVESTMENT_TYPES`)
   - `amount REAL NOT NULL`
   - `date TEXT NOT NULL` (strict `YYYY-MM-DD`, not in the future)
   - `note TEXT` nullable (optional free text)
   - `created_at TEXT NOT NULL DEFAULT (datetime('now'))`

New data-layer functions in `database/db.py`:
- `create_investment(user_id, type, amount, date, note)` — parameterised INSERT, returns `lastrowid` (mirrors `create_expense`)
- `get_investments_by_user_id(user_id)` — parameterised `SELECT * FROM investments WHERE user_id = ? ORDER BY date DESC`

## Templates
- **Modify:** `templates/profile.html`:
  - Fourth stat card **"Total invested"** (`stats["total_invested"]`, ₹ formatted).
  - New **"Investments"** card after the earnings card: a POST form (`action="{{ url_for('investments') }}"`) with a type `<select>` looping `investment_types` (7 options), amount input, date input (default today), optional note input, and an error slot (`investment_error`, class `auth-error`). Below it a table: Date | Type | Amount | Note, with a by-type breakdown list (same row style as "Spending by category") and an empty state ("No investments yet.").
  - Monthly comparison table gains an **Invested** column (₹ value or `—` when the month has no investments); empty-state `colspan` 4 → 5.

## Files to change
- `database/db.py` — add `"Investment"` to `CATEGORIES`; add `INVESTMENT_TYPES`; add `investments` table to `SCHEMA`; add `create_investment()`, `get_investments_by_user_id()`
- `app.py`:
  - New `POST /investments` route: session guard; validate type (`in INVESTMENT_TYPES`), amount (finite, `> 0`), date (`date.fromisoformat`, not future); on failure re-render profile with `investment_error` (via `render_profile(investment_error=error)`); on success `create_investment(...)` → redirect to `url_for("profile")`
  - `render_profile(error=None)` → `render_profile(earnings_error=None, investment_error=None)`; `/earnings` failure passes `earnings_error=`; compute `total_invested`, `investment_breakdown` (reuse `build_category_breakdown` shape over `INVESTMENT_TYPES`), pass `investments` list and `investment_types`
  - `build_monthly_comparison(expenses, earnings_rows, investments)` — add invested-by-month from `investment["date"][:7]`; months = union of expense/earnings/investment months, sorted descending; `net` unchanged (`earnings − spent` only when both exist)
  - Amount validation shared: extract the amount-parse rules (finite + positive) so expenses, earnings and investments use identical strings — e.g. a small `parse_amount()` helper used by all three validators
- `static/css/style.css` — investments card reuses `.earnings-*` layout styles via shared selectors (e.g. `.earnings-form, .invest-form { … }`, `.earnings-table, .invest-table { … }`, `.earnings-save, .invest-save { … }`); breakdown rows reuse existing `.breakdown-*`. CSS variables only.

## Files to create
- `tests/test_11-investments.py` (spec-derived; see Definition of done)

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw sqlite3 via `get_db()` only
- Parameterised queries only — never string-format SQL
- Use CSS variables — never hardcode hex values; no inline styles
- All templates extend `base.html`; use `url_for()` for routes/static assets
- Investment type must be in `INVESTMENT_TYPES` (no free-form types)
- Amount follows the existing rule (finite positive number); date strict `YYYY-MM-DD`, not in the future
- The profile page is read-only aggregation of `expenses` + `earnings` + `investments` — no writes on GET
- On successful POST → redirect (PRG)
- Investment-category expenses count in Spent exactly like other expenses (no special-casing in stats/breakdown/comparison)

## Definition of done
- [ ] `POST /investments` without being logged in redirects to `/login`
- [ ] Adding a valid investment inserts a row with the correct user_id, type, amount, date and note; empty note stores NULL
- [ ] Invalid type (`Hack`, empty), invalid amount (`abc`, `0`, `-5`, `nan`, `inf`, empty), invalid date (empty, `2026-02-30`, future) fail gracefully: 200, error shown, no row inserted
- [ ] `Investment` appears in the expense category dropdown on `/expenses/add` and `/expenses/<id>/edit` (8 categories total)
- [ ] `/profile` shows: "Total invested" stat card, investments form with all 7 types, investment list table, by-type breakdown, "No investments yet." empty state
- [ ] `/profile` comparison table has an Invested column; with a same-month investment it shows the invested ₹ amount; Net is still `earnings − spent`
- [ ] A month with an investment but no expenses/earnings is listed in the comparison (invested shown, others `—`)
- [ ] No hex colour values or inline styles in the new template markup
- [ ] Existing suite stays green (category-count tests 01/07/08 updated for the 8th category)