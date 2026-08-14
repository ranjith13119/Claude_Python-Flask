# Spec: Delete Expense

## Overview
This feature replaces the `/expenses/<int:id>/delete` placeholder with a working delete action. Each row in the profile transactions table gets a Delete button that removes the expense via a POST request and redirects back to the profile. Following the Step 03 logout pattern, delete is POST-only (a GET returns 405) so it can never be triggered by a link or prefetch. Like edit, it enforces ownership — a user may only delete their own expenses.

## Depends on
- Step 1: Database setup — `expenses` table exists.
- Step 3: Login / Logout — POST-only action pattern from `/logout` is reused.
- Step 7: Add expense — ownership + session guard patterns reused.

## Routes
- `POST /expenses/<int:id>/delete` — delete the expense, then redirect to `/profile` — logged-in only, ownership required (GET → 405)

## Database changes
No schema changes. Add one data-layer function to `database/db.py`:
- `delete_expense(expense_id)` — parameterised `DELETE FROM expenses WHERE id = ?`

## Templates
- **Modify:** `templates/profile.html` — each row of the transactions table gets a Delete button in the actions column: a small POST form (like the logout form in `base.html`) with `action="{{ url_for('delete_expense', id=expense['id']) }}"`.

## Files to change
- `app.py` — replace the `/expenses/<int:id>/delete` placeholder with POST-only logic:
  - Method check: only POST allowed → Flask returns 405 for GET automatically when route is POST-only
  - Fetch expense by id; if missing **or** `expense["user_id"] != session["user_id"]` → 404
  - `delete_expense(id)` then `redirect(url_for("profile"))`
- `database/db.py` — add `delete_expense()`
- `templates/profile.html` — add Delete button form per row
- `static/css/style.css` — danger-styled small button (use `--danger` variable)

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw sqlite3 via `get_db()` only
- Parameterised queries only — never string-format SQL
- Use CSS variables — never hardcode hex values; no inline styles
- All templates extend `base.html`; use `url_for()` for routes/static assets
- Route registered as POST-only (no `methods=["GET"]`) — GET → 405
- Ownership check: `expense is None or expense["user_id"] != session["user_id"]` → 404
- Delete button is a form with `method="POST"` — never a link or GET
- On success, redirect to `url_for("profile")`

## Definition of done
- [ ] `GET /expenses/<id>/delete` returns 405
- [ ] POST without being logged in redirects to `/login`
- [ ] POST for another user's (or non-existent) expense returns 404 and nothing is deleted
- [ ] POST for the owner's expense deletes the row (verified in DB), then redirects to `/profile`
- [ ] The profile transactions table shows a Delete button per row, and deleting removes that row from the page
- [ ] Deleting the last expense leaves the profile page rendering normally (empty state)