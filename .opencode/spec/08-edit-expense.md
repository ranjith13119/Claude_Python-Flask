# Spec: Edit Expense

## Overview
This feature replaces the `/expenses/<int:id>/edit` placeholder with a working edit form. A logged-in user opens an existing expense, changes amount, category, date or description, and the row is updated in place. This is the first UPDATE path in the app and completes the expense lifecycle alongside Step 07 (create) and Step 09 (delete). It reuses the exact validation rules from Step 07 so the two forms behave identically, and it enforces ownership — a user may only edit their own expenses.

## Depends on
- Step 1: Database setup — `expenses` table exists.
- Step 3: Login / Logout — route must be logged-in only; session guard pattern reused.
- Step 7: Add expense — validation rules, `CATEGORIES` list and form markup are the baseline for the edit form.

## Routes
- `GET /expenses/<int:id>/edit` — render pre-filled edit form — logged-in only, expense must belong to the session user
- `POST /expenses/<int:id>/edit` — validate and update the expense, then redirect to `/profile` — logged-in only, ownership required

## Database changes
No schema changes. Add two data-layer functions to `database/db.py`:
- `get_expense_by_id(expense_id)` — parameterised `SELECT * FROM expenses WHERE id = ?`, returns row or None
- `update_expense(expense_id, amount, category, date, description)` — parameterised `UPDATE expenses SET ... WHERE id = ?`

## Templates
- **Create:** `templates/edit_expense.html` — extends `base.html`; same field set as `add_expense.html` (amount, category select, date, description) but pre-filled from the existing row; category dropdown shows the row's current category selected; "Save changes" submit button and a cancel link back to `/profile`; error re-render pattern identical to the add form.
- **Modify:** `templates/profile.html` — each row of the transactions table gets an "Edit" link to `url_for('edit_expense', id=expense['id'])` in a new actions column.

## Files to change
- `app.py` — replace the `/expenses/<int:id>/edit` placeholder with GET/POST logic:
  - Fetch expense by id; if missing **or** `expense["user_id"] != session["user_id"]` → 404 (never reveal whether an id exists)
  - GET: render form pre-filled with the row
  - POST: validate with the same rules as Step 07 (amount > 0, category in `CATEGORIES`, strict date not in future); on failure re-render with error and no DB write; on success `update_expense(...)` → redirect to `url_for("profile")`
- `database/db.py` — add `get_expense_by_id()` and `update_expense()`
- `templates/profile.html` — add Edit link column
- `static/css/style.css` — styles for the small action link/button

## Files to create
- `templates/edit_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw sqlite3 via `get_db()` only
- Parameterised queries only — never string-format SQL
- Passwords hashed with werkzeug (no auth changes)
- Use CSS variables — never hardcode hex values; no inline styles
- All templates extend `base.html`; use `url_for()` for routes/static assets
- Ownership check on every request: `expense is None or expense["user_id"] != session["user_id"]` → 404
- Validation rules and error strings identical to Step 07 (`add_expense`)
- The category list must come from `database/db.py::CATEGORIES` — no hardcoded duplicate
- On success, redirect (POST/Redirect/GET pattern)

## Definition of done
- [ ] Visiting `/expenses/<id>/edit` without being logged in redirects to `/login`
- [ ] Visiting the edit page for another user's (or non-existent) expense returns 404
- [ ] The edit form is pre-filled with the expense's amount, category, date and description
- [ ] All seven categories are present in the dropdown with the current one selected
- [ ] Submitting valid changes updates the row (verified in DB) and redirects to `/profile`
- [ ] Submitting an invalid amount/category/date re-renders with an error message and changes nothing in the DB
- [ ] The profile page shows an Edit link for each transaction row
- [ ] No hex colour values or inline styles appear in `edit_expense.html`
