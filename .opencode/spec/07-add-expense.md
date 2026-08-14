# Spec: Add Expense

## Overview
This feature replaces the `/expenses/add` placeholder with a working expense-creation form. A logged-in user fills in amount, category, date and an optional description; the expense is validated and inserted into the `expenses` table, then the user is redirected back to the landing page. This is the first write path in the app (registration already writes to `users`) and the first time the fixed category list from `database/db.py::CATEGORIES` is used by an interactive form. It establishes the validation + redirect pattern that Steps 8 (edit) and 9 (delete) will follow.

## Depends on
- Step 1: Database setup — the `expenses` table (id, user_id, amount, category, date, description) already exists.
- Step 3: Login / Logout — `/expenses/add` must be a logged-in-only route; the session guard pattern from `/profile` is reused.

## Routes
- `GET /expenses/add` — render the add-expense form — logged-in only (redirect to `/login` if not authenticated)
- `POST /expenses/add` — validate and insert the expense, then redirect — logged-in only

## Database changes
No schema changes. The `expenses` table from Step 1 is sufficient. Add one data-layer function to `database/db.py`:
- `create_expense(user_id, amount, category, date, description)` — parameterised `INSERT` into `expenses`, returns `cur.lastrowid`.

## Templates
- **Create:** `templates/add_expense.html` — form extending `base.html`:
  - Amount field (number, required, > 0, up to 2 decimals)
  - Category `<select>` populated from the fixed category list (Food, Transport, Bills, Health, Entertainment, Shopping, Other)
  - Date field (HTML5 `type="date"`, required, `YYYY-MM-DD`), defaulting to today
  - Description field (optional, text)
  - Submit button; error message area re-rendered on validation failure (same pattern as `login.html`/`register.html`)

## Files to change
- `app.py` — replace the `/expenses/add` placeholder with a GET/POST view function that:
  - Redirects unauthenticated users to `/login`
  - Validates the submitted form (all fields required except description; amount must parse to a positive number; category must be in `CATEGORIES`; date must parse as `YYYY-MM-DD` and not be in the future)
  - Calls `create_expense(...)` on success and redirects to `landing`
  - Re-renders the form with an error message on failure
- `database/db.py` — add `create_expense()` (parameterised `INSERT` via `get_db()`)
- `static/css/style.css` — add form styles using only existing `:root` variables (reuse the auth-form styles where possible)

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw sqlite3 via `get_db()` only
- Parameterised queries only — never string-format SQL
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values; no inline styles
- All templates extend `base.html`; use `url_for()` for routes/static assets
- Authentication guard: check `session.get("user_id")`; if absent, `redirect(url_for("login"))`
- The category list must come from `database/db.py::CATEGORIES` — no hardcoded duplicate list in `app.py` or the template
- Amounts stored as REAL; dates stored strictly as `YYYY-MM-DD`
- On success, redirect (POST/Redirect/GET pattern) — never render a template on a successful POST

## Definition of done
- [ ] Visiting `/expenses/add` without being logged in redirects to `/login`
- [ ] Visiting `/expenses/add` while logged in returns HTTP 200 and shows the form
- [ ] The form has fields for amount, category, date and description, with all seven categories present in the dropdown
- [ ] Submitting a valid expense (e.g. amount 320, Food, today) redirects to `/` and inserts exactly one row for the logged-in user in the `expenses` table
- [ ] Submitting with a missing amount/category/date re-renders the form with an error message and inserts nothing
- [ ] Submitting a non-numeric or non-positive amount re-renders the form with an error message and inserts nothing
- [ ] Submitting an invalid or future date re-renders the form with an error message and inserts nothing
- [ ] The inserted row stores the correct `user_id` (the session user, not someone else's)
- [ ] No hex colour values appear in `add_expense.html` — only CSS variables