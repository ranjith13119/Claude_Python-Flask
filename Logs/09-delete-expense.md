# Log: Step 09 — Delete Expense

Date: 2026-08-14
Branch: feature/crud-earnings
Status: implemented + tested (10/10 new, full suite 172/172)

## What was done

- `database/db.py`: added `delete_expense(expense_id)` (parameterised DELETE).
- `app.py`: `/expenses/<int:id>/delete` is POST-only (replaces the Step 9 placeholder; GET → 405 automatically). Route function named `delete_expense_route` to avoid clashing with the imported db function `delete_expense`. Auth guard first → 302 `/login`. Ownership: missing or foreign expense → 404 (nothing deleted). Success: `delete_expense(id)` → 302 `/profile` (PRG).
- `templates/profile.html`: transactions table gained an actions column (Edit link + Delete inline POST form via `url_for('delete_expense_route', id=tx['id'])`); empty-state colspan 4→5. Transactions dict in `render_profile` now carries `id`.
- `static/css/style.css`: added `.btn-sm`, `.btn-danger-sm`, `.inline-form` (margin 0, inline-flex), `.table-actions` (white-space nowrap) using `:root` vars only.

## Issues encountered

- None. DELETE-by-GET is blocked at the router level (405) rather than in code — tests pin this.

## Verification

- `python -m pytest tests/test_09-delete-expense.py -v` → 10/10 passed
- `python -m pytest -q` → 172/172 passed (Steps 01–10)

## Next

- Ship Steps 08–10 together: commit, push `feature/crud-earnings`, PR (squash-merge), delete branch.