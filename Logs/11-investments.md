# Log: Step 11 — Investment Tracking

Date: 2026-08-14
Branch: feature/investments
Status: implemented + tested (27/27 new, full suite 199/199)

## What was done

- `database/db.py`:
  - `CATEGORIES` now 8 — added `"Investment"` (expense category dropdowns on add/edit pick it up automatically since they loop `CATEGORIES`).
  - New `INVESTMENT_TYPES = ["MF", "Stocks", "Gold", "Bonds", "Crypto", "Real Estate", "Other"]`.
  - New `investments` table in `SCHEMA` (id, user_id FK, type, amount REAL, date, note nullable, created_at; `CREATE TABLE IF NOT EXISTS` → existing local DBs pick it up on next startup).
  - New `create_investment(user_id, type, amount, date, note)` (mirrors `create_expense`) and `get_investments_by_user_id(user_id)` (ORDER BY date DESC).
  - Seed: added 9th expense `("Gold coin", "Investment", 50.00, today-8)` so seed still covers every category. New seed totals: ₹344.64 total, Shopping still top (₹79.99), breakdown percents Food 22 / Transport 7 / Bills 17 / Health 6 / Entertainment 6 / Shopping 23 / Other 4 / Investment 15.
- `app.py`:
  - Extracted shared `parse_amount(amount_raw)` → `(amount, error)` (finite + positive) — now used by `validate_expense_input`, the `/earnings` route and the new `validate_investment_input`; one source of truth for amount rules/error strings.
  - New `validate_investment_input(amount_raw, type_raw, date_raw)` (type in `INVESTMENT_TYPES`; date strict + not future).
  - New `POST /investments`: session guard → validate → on error re-render profile with `investment_error`; on success `create_investment` → 302 `/profile` (PRG). Note stripped, empty → NULL.
  - `render_profile(error=None)` → `render_profile(earnings_error=None, investment_error=None)`; `/earnings` failure updated accordingly.
  - `build_monthly_comparison(expenses, earnings_rows, investments)` — new `invested` per month from `investment["date"][:7]`; months = union of all three sources, sorted DESC; `net` unchanged (earnings − spent; investment purchases already flow through Spent — no double counting, Invested column is informational).
  - New `build_investment_breakdown(investments)` (mirrors `build_category_breakdown` shape over `INVESTMENT_TYPES`); stats gained `total_invested`.
- `templates/profile.html`: 4th stat card "Total invested"; new Investments card — form (type select looping `investment_types`, amount, date default `current_month-01`, note), `investment_error` slot, table Date | Type | Amount | Note, "Investments by type" breakdown (reuses `.breakdown-*`), "No investments yet." empty state; comparison table gained Invested column (colspan 4→5).
- `static/css/style.css`: `.earnings-*` rules now shared selectors (`.earnings-form, .invest-form`, `.earnings-table, .invest-table`, `.earnings-save, .invest-save`, plus `.invest-form input[type="date"]` and `.form-select` in the shared input rule); added `.card-subtitle`. CSS variables only.
- Tests: new `tests/test_11-investments.py` 27/27 (access control; valid insert + NULL note; all 7 types savable; 11 invalid variants incl. nan/inf → 200 + error + no row; form renders all 7 types; stat card ₹0.00 → updates; list row; by-type breakdown 75%/25%; empty state; Invested column; net = earnings − spent unchanged; investment-only month listed; template rules). Updated for the 8th category + new seed: test_01 (EXPECTED_CATEGORIES + count 9), test_04 (₹344.64, >9<, 4 stat cards, percents 22/23/17), test_05 (₹344.64, pct-22/pct-23, count 9), test_06 (₹344.64, count 9), test_07/test_08 (EXPECTED_CATEGORIES + 8, renamed "seven"→"eight" methods).

## Issues encountered

- test_01's `test_all_categories_covered` failed after adding "Investment" to CATEGORIES — seed data didn't cover the new category. Fixed properly: seed gained a Gold coin Investment expense (keeps the seed-covers-all-categories invariant) and the dependent totals/counts/percent assertions in test_04/05/06 were updated from the computed values (no hardcoded guessing).
- Reviewer subagents still unavailable in this environment — inline review done by the main agent (security: session-scoped writes, parameterised SQL, finite amounts, whitelisted types, POST-only; quality: shared `parse_amount`, deliberate duplication for teaching clarity). No changes required.

## Verification

- `python -m pytest tests/test_11-investments.py -v` → 27/27 passed
- `python -m pytest -q` → 199/199 passed (Steps 01–11)

## Next

- Ship: commit, push `feature/investments`, PR (base main — note dependency on PR #11; GitHub drops the 08–10 commits from the diff once #11 squash-merges).