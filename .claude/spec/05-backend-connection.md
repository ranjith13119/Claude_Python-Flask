# Spec: Backend Connection

## Overview

Step 04 delivered the Profile page as a static UI fed by hardcoded context in `app.py`. This step replaces every hardcoded value with real data from the database: the route loads the logged-in user from the `users` table, pulls their actual expenses from the `expenses` table, and computes the stats, recent-transactions list, and category breakdown (with percentages) from that real data. The Profile page now reflects the user's true spending instead of demo numbers, making it the first fully "live" page in the app and the foundation for Steps 06-09 (expense list, add, edit, delete), which all read the same expense rows.

## Depends on

- Step 01 — Database setup (`users` + `expenses` tables, `seed_db()` demo data)
- Step 03 — Login / Logout (`session["user_id"]`, `get_user_by_id()`)
- Step 04 — Profile static UI (template structure, CSS classes, session guard)

## Routes

- `GET /profile` — render the profile page from live database data — logged-in only (302 to `/login` when logged out)

No new routes.

## Database changes

No schema changes. The `users` and `expenses` tables already store everything needed.

Add one helper to `database/db.py`:

- `get_expenses_by_user_id(user_id)` — parameterized `SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC` returning a list of sqlite3.Row, empty list when the user has no expenses.

## Templates

- **Modify:** `templates/profile.html` — template stays as-is; all context variables keep the same names so no template changes are required. If any data shape changes (e.g. amount formatting), the template must still render exactly the same layout, classes, and sections.
- **Create:** none

## Files to change

- `database/db.py` — add `get_expenses_by_user_id(user_id)`
- `app.py` — rewrite the `/profile` route to:
  1. Keep the session guard (`redirect(url_for("login"))` when logged out)
  2. Load the user via `get_user_by_id(session["user_id"])`; redirect to `/login` if the row is missing (stale session)
  3. Load expenses via `get_expenses_by_user_id(user["id"])`
  4. Compute `total_spent` (sum of amounts), `transaction_count` (number of rows), `top_category` (category with the highest total amount, "-" when there are no expenses)
  5. Build `category_breakdown` aggregated per category with formatted totals and integer percentages (round to nearest; percentages of one category may not sum to exactly 100)
  6. Build `transactions` list from the expense rows (date, description, category, ₹-formatted amount)
  7. Derive `member_since` from the user's `created_at` (e.g. "March 2026")
  8. Render `profile.html` with the same variable names Step 04 used (`name`, `email`, `member_since`, `stats`, `transactions`, `category_breakdown`)

## Files to create

- (test file `tests/test_05-profile.py` is created by the test-feature step)

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — parameterized queries only, never string formatting in SQL
- Passwords hashed with werkzeug — never render or expose any hash; the page must never leak `password_hash`
- Session guard first: logged-out requests redirect to `/login`; a user_id with no matching user row (stale session) must also redirect safely, never crash
- Use the `current_user` context processor pattern from Step 03 where sensible — no duplicate user lookups
- Amounts formatted with the rupee symbol and thousands separators (e.g. `₹12,450`, `₹320.50`) in the route — no currency logic in the template
- Category names come from the DB seed data and must match the fixed list: Food, Transport, Bills, Health, Entertainment, Shopping, Other
- Empty state: a user with zero expenses must render the page fine — `stats` total ₹0, count 0, top category "-", empty transactions table, empty breakdown (no crash, no division by zero)
- Use CSS variables from `:root` in `static/css/style.css` — never hardcode hex colors; no template/CSS changes to the Step 04 design (no redesign, no frontend-design skill)
- All templates extend `base.html`; use `url_for()` for routes and static assets

## Definition of done

- [ ] GET /profile while logged out responds 302 and redirects to /login
- [ ] GET /profile while logged in responds 200 and shows the real user's name and email from the `users` table, not the hardcoded "Demo User" values
- [ ] The three stat cards show values computed from the user's actual expenses: total spent (sum of amounts), transaction count (row count), top category (largest category total)
- [ ] The transactions table shows the user's real expense rows (date, description, category, ₹-formatted amount) from the `expenses` table, ordered by date descending
- [ ] The category breakdown shows per-category totals and percentages computed from real expense data, and the percentages render through the exact-value `.pct-*` classes
- [ ] `member_since` is derived from the user's `created_at`
- [ ] A user with no expenses sees ₹0 / 0 / "-" and empty table/breakdown with a 200 response (no crash, no division by zero)
- [ ] A stale session (user_id with no matching user) redirects to /login, not a 500
- [ ] No password hash appears anywhere in the response
- [ ] The page layout, classes, and styling are unchanged from Step 04
- [ ] `python -m pytest tests/test_05-profile.py -v` passes
- [ ] Full suite stays green: `python -m pytest -q`