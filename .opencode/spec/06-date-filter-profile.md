# Spec: Date Filter for Profile Page

## Overview
This feature adds a date-range filter to the profile page's transaction history. Users can enter a from-date and a to-date to narrow the transactions table to expenses within that range. The filter is applied server-side via GET query parameters (`from_date`, `to_date`) on the existing `/profile` route, so it remains testable with pytest and works with whatever data source the route currently uses (hardcoded lists in Step 04, real DB rows once Step 05 lands). It builds directly on the Step 04 profile UI without introducing a new page or route.

## Depends on
- Step 1: Database setup (schema must exist)
- Step 2: Registration (user accounts must be creatable)
- Step 3: Login + Logout (session must be set; `/profile` must be a protected route)
- Step 4: Profile page (the transaction history table being filtered lives in `templates/profile.html`)

Note: the filter logic is data-source agnostic. It filters the `transactions` list the route passes to the template — the same list that Step 05 (backend connection, pending) will later populate from the `expenses` table.

## Routes
No new routes. Modify the existing:
- `GET /profile` — accept optional query params `from_date` and `to_date` (format `YYYY-MM-DD`); filter the transactions passed to the template — logged-in only (302 to `/login` when unauthenticated)

## Database changes
No database changes. The existing `users` and `expenses` tables are sufficient; filtering happens in Python on the list passed to the template.

## Templates
- **Create:** none
- **Modify:** `templates/profile.html` — add a filter bar above the "Recent transactions" table:
  - `<form method="GET" action="{{ url_for('profile') }}">` with two `<input type="date">` fields named `from_date` and `to_date`, a Filter button and a Reset link (`url_for('profile')` with no params)
  - Date inputs pre-filled from the current query params when present
  - An empty-state message in the table body when the filter yields no rows
  - No inline styles; reuse/extend CSS variables

## Files to change
- `app.py` — in the `profile()` view:
  - Read `request.args.get("from_date")` and `request.args.get("to_date")`
  - Validate: must be empty or a valid `YYYY-MM-DD` string (use `datetime.date.fromisoformat`); invalid values are ignored (treated as absent) — do not 400 the page
  - Filter the `transactions` list: row kept when its `date` is `>= from_date` (if set) and `<= to_date` (if set)
  - Pass `from_date`, `to_date` back to the template so the form stays filled
- `templates/profile.html` — filter form + empty state (see Templates)
- `static/css/style.css` — append a Profile-filter block using `:root` variables only (no hex)

## Files to create
- `tests/test_06-date-filter-profile.py` — written by the test-feature workflow, from this spec only

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never string-format SQL
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline styles
- Authentication guard: check `session.get("user_id")`; if absent, `redirect(url_for("login"))`
- Dates compared as strings in `YYYY-MM-DD` form only — never parse/reformat for comparison
- Invalid date params (e.g. `2026-02-30`, `abc`) are ignored silently, never cause a 500
- Filtering must not mutate the original transaction list
- The Reset link must clear both params and return the full unfiltered list

## Definition of done
- [ ] Visiting `/profile` without being logged in still redirects to `/login`
- [ ] `/profile` shows a date filter form with from-date and to-date inputs
- [ ] Submitting the form with only `from_date` set shows only transactions on or after that date
- [ ] Submitting the form with only `to_date` set shows only transactions on or before that date
- [ ] Submitting the form with both dates set shows only transactions inside that inclusive range
- [ ] A filter with no matching transactions shows an empty-state message (not a blank table)
- [ ] The Reset link returns the full unfiltered transaction list
- [ ] Invalid date values (malformed, out-of-range) render the page without a 500 and with the full list
- [ ] The form inputs are pre-filled with the active filter values after submission
- [ ] No hex colour values appear in `profile.html` — only CSS variables
- [ ] `python -m pytest tests/test_06-date-filter-profile.py -v` passes
