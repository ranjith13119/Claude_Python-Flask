# Log: Step 06 — Date Filter for Profile Page

Date: 2026-08-13
Branch: feature/date-filter-profile
Status: implemented + tested (18/18 new, full suite 92/92)

## What was done

- `app.py` `/profile` route: reads `from_date`/`to_date` query params, validates with `valid_date()` helper (`datetime.strptime(value, "%Y-%m-%d")` — malformed/out-of-range silently ignored, treated as absent), filters the `transactions` list with string comparisons on `YYYY-MM-DD` (inclusive range), builds a new list (original untouched). Params passed back to the template so the form stays filled.
- `templates/profile.html`: filter bar above "Recent transactions" — GET form posting to `url_for('profile')` with two `<input type="date">` fields, Filter button, Reset link (clears both params). Empty state via Jinja `{% else %}` on the loop: "No transactions in this date range." when a filter is active, "No transactions yet." otherwise. No inline styles, no hex.
- `static/css/style.css`: appended filter block — `.filter-form`, `.filter-fields`, `.filter-field`, `.filter-actions`, `.filter-btn`, `.filter-reset`, `.filter-empty`; all colors from `:root` variables; responsive collapse at 600px.
- Filter applies to the transactions table only — stat cards and category breakdown stay full-range (per spec).

## Issues encountered

- Test bug (not app bug): my `to_date` test used `today-8` but the seed's oldest expense is `today-7` — fixed the test constant to `SEVEN_DAYS_AGO`. App behavior was correct.

## Verification

- `python -m pytest tests/test_06-date-filter-profile.py -v` → 18/18 passed
- `python -m pytest -q` → 92/92 passed

## Next

- Ship: commit, push `feature/date-filter-profile`, PR (squash-merge), delete branch.
- Step 07 (Add expense) — the filter route pattern (query params + validation) is reusable for expense list pages.