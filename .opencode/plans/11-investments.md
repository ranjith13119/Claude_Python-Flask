# Plan: Step 11 — Investment Tracking

Branch: `feature/investments` (from `feature/crud-earnings`, which holds Steps 08-10)
Spec: `.claude/spec/11-investments.md` (+ `.opencode/spec/` mirror)

## Tasks

### 1. Database layer — `database/db.py`
- Add `"Investment"` to `CATEGORIES` (7 → 8)
- Add `INVESTMENT_TYPES = ["MF", "Stocks", "Gold", "Bonds", "Crypto", "Real Estate", "Other"]`
- Add `investments` table to `SCHEMA` (id, user_id FK, type, amount REAL, date, note nullable, created_at)
- Add `create_investment(user_id, type, amount, date, note)` and `get_investments_by_user_id(user_id)` (ORDER BY date DESC)

### 2. App layer — `app.py`
- Import new names; extract `parse_amount(amount_raw)` returning `(amount, error)` with the finite+positive rule; reuse in `validate_expense_input` and the earnings route so all three amount validators share one implementation
- Add `validate_investment_input(amount_raw, type_raw, date_raw)` (type in INVESTMENT_TYPES; date fromisoformat + not future)
- New `POST /investments`: session guard → validate → error: `render_profile(investment_error=error)`; success: `create_investment` → redirect profile
- `render_profile(error=None)` → `render_profile(earnings_error=None, investment_error=None)`; `/earnings` failure updated to `earnings_error=`
- `build_monthly_comparison(expenses, earnings_rows, investments)` gains `invested` per month; months union includes investment months; net unchanged
- Profile context: `total_invested` stat, `investments` list, `investment_breakdown` (breakdown shape over INVESTMENT_TYPES), `investment_types`
- New `build_investment_breakdown(investments)` mirroring `build_category_breakdown` shape

### 3. Template — `templates/profile.html`
- 4th stat card "Total invested"
- Investments card: form (type select 7 options, amount, date default today, note), `investment_error` slot, table Date | Type | Amount | Note, by-type breakdown, empty state "No investments yet."
- Comparison table: Invested column; empty-state colspan 4 → 5

### 4. CSS — `static/css/style.css`
- Shared selectors: `.earnings-form, .invest-form`, `.earnings-table, .invest-table`, `.earnings-save, .invest-save`; breakdown reuses `.breakdown-*`; CSS variables only

### 5. Tests
- Update `tests/test_01-database-setup.py`: EXPECTED_CATEGORIES += "Investment"
- Update `tests/test_07-add-expense.py` / `tests/test_08-edit-expense.py`: EXPECTED_CATEGORIES += "Investment" (rename "seven" → "eight" test methods)
- New `tests/test_11-investments.py` per spec's Definition of done (~22 tests):
  - Access control, valid insert (+NULL note), all 7 types in form, invalid type/amount (incl. nan/inf)/date variants → 200 + error + no row
  - Profile: stat card, form, list, breakdown, empty state
  - Comparison: Invested column value, net = earnings − spent unchanged, investment-only month listed
  - Template rules (extends base, no hex, no inline styles)
- Run new file until green, then full suite (expect ~194)

### 6. Review
- Inline quality + security review (subagents unavailable in this environment — verified in Step 08-10)
- Key checks: ownership scoping (session user only), parameterised SQL, float edge cases (nan/inf), autoescape, PRG

### 7. Docs
- `Logs/11-investments.md`, memory.md entry, CLAUDE.md roadmap (Step 11 ✅, schema + title 1-11)

### 8. Ship
- Commits: `feat: add investment tracking — Step 11`, `docs: ...`
- Push `feature/investments`, PR → main (note dependency on PR #11; GitHub auto-rebases the diff once #11 squash-merges)
