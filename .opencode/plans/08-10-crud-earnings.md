# Plan: Steps 08-10 — Edit Expense, Delete Expense, Monthly Earnings

Branch: `feature/crud-earnings` (based on `feature/add-expense` which contains Steps 01-07 merged)
Specs: `.claude/spec/08-edit-expense.md`, `09-delete-expense.md`, `10-monthly-earnings.md`

## Steps

1. **database/db.py**
   - Add to `SCHEMA`: `earnings` table (id, user_id FK, month TEXT `YYYY-MM`, amount REAL, created_at, `UNIQUE (user_id, month)`) — `CREATE TABLE IF NOT EXISTS` so existing local DBs pick it up on startup
   - `get_expense_by_id(expense_id)` — SELECT * WHERE id = ?
   - `update_expense(expense_id, amount, category, date, description)` — parameterised UPDATE
   - `delete_expense(expense_id)` — parameterised DELETE
   - `upsert_earnings(user_id, month, amount)` — INSERT ... ON CONFLICT(user_id, month) DO UPDATE SET amount = excluded.amount
   - `get_earnings_by_user_id(user_id)` — SELECT * WHERE user_id = ? ORDER BY month DESC

2. **app.py**
   - Extract Step 07 validation into `validate_expense_input(amount_raw, category, date_raw)` returning `(amount, category, date_raw, error)` — error strings identical to Step 07 so test_07 stays green; use it in both `add_expense` and `edit_expense`
   - `edit_expense(id)`: GET+POST; session guard; `get_expense_by_id(id)`; ownership: `expense is None or expense["user_id"] != session["user_id"]` → 404; GET renders `edit_expense.html` pre-filled (amount, category selected, date, description); POST validates → re-render with error on failure; success `update_expense(...)` → redirect `url_for("profile")`
   - `delete_expense(id)`: POST-only decorator; session guard; ownership → 404; `delete_expense(id)` → redirect `url_for("profile")` (GET → 405 automatically)
   - `earnings` route: POST-only; session guard; validate month: regex `^\d{4}-\d{2}$` + `date.fromisoformat(month + "-01")`; amount float > 0; on failure re-render `profile.html` with earnings_error (reuse profile context); success `upsert_earnings(...)` → redirect `url_for("profile")`
   - `profile()`: build monthly comparison — dict of month → spent from expenses (`date[:7]`), merge earnings rows; for each month in union: earnings amount or None, spent or None, net when both present; sort month desc; pass `monthly_comparison`, `current_month`, `earnings_error` (None default)

3. **Templates**
   - `templates/edit_expense.html` — same structure as add_expense.html; pre-filled `value="{{ expense['amount'] }}"` etc.; category `<select>` with `{% if category == expense['category'] %}selected{% endif %}`; cancel link to `url_for('profile')`
   - `templates/profile.html` — add "Add expense" button near section header; transactions table gains actions column: Edit link (`btn-sm`) + Delete POST form (`btn-sm btn-danger-sm`); new "Monthly earnings" section: form (month `type="month"` value=current_month, amount, save button) + comparison table (Month | Earnings | Spent | Net) with `.net-positive`/`.net-negative`; empty-state row when no months
   - `templates/base.html` — logged-in navbar: "Add expense" link next to email

4. **static/css/style.css** — append Earnings + actions block: `.section-actions`, `.btn-sm`, `.btn-danger-sm`, `.earnings-form`, `.earnings-table`, `.net-positive`, `.net-negative`, `.table-actions` — `:root` vars only

5. **Tests** (from specs, never from implementation)
   - `tests/test_08-edit-expense.py` (~18): access control; 404 for missing + other-user's expense; GET pre-filled (amount/category/date/description, selected category); valid update → row changed + redirect /profile; invalid variants (amount abc/0/-5, bad category, bad date, future date) → 200 error + unchanged row; description cleared to NULL; template rules (extends base, no hex, no inline styles)
   - `tests/test_09-delete-expense.py` (~10): GET → 405; logged-out POST → 302 /login; missing/other-user → 404 + row still present; owner POST → row gone + 302 /profile; delete-all leaves profile rendering
   - `tests/test_10-monthly-earnings.py` (~16): logged-out POST → 302 /login; insert new month row; same-month upsert overwrites (count stays 1); invalid months (2026-13, abc, empty, 2026-1) + invalid amounts → error, no row; profile shows form + current month default; comparison values correct for seed (spent 294.64, net = earnings - 294.64); months without expenses but with earnings listed; navbar + profile "Add expense" link present; template rules

6. **Verify** — run each test file until green, then `python -m pytest -q` full suite

7. **Review** — launch quality-reviewer + security-reviewer agents in parallel on the diff; fix findings

8. **Docs** — plans mirrored to `.opencode/plans/`; `Logs/08-edit-expense.md`, `Logs/09-delete-expense.md`, `Logs/10-monthly-earnings.md`; memory/memory.md + `.claude/memory/`; CLAUDE.md roadmap rows 08/09/10 → Complete

9. **Ship** — commit (`feat:` + `docs:`), push `feature/crud-earnings`, PR (squash-merge convention)

## Notes / decisions

- Ownership violations → 404 (don't leak whether an id exists)
- Delete is POST-only (405 on GET), same as logout
- Earnings upsert uses SQLite `ON CONFLICT` — requires the UNIQUE constraint in schema
- `validate_expense_input` extraction keeps Step 07 error strings byte-identical
- Comparison months = union of expense months and earnings months, sorted desc; Net only computed when both exist
- Earnings POST failure re-renders profile.html with full context (no PRG on error — same pattern as add expense)