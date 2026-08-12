# Spec: Profile Page

## Overview

Logged-in users can view their own account page showing the full name, email address, and account creation date they registered with. Visiting `/profile` while logged out redirects to the login page, and every logged-in user only ever sees their own data. This is the first "logged-in only" page in Spendly, so it establishes the access-control pattern every protected route from Step 05 onward will reuse, and it gives the "My profile" button added to the landing hero in Step 03 a real destination.

## Depends on

- Step 01 — Database setup (`users` table with `name`, `email`, `created_at`)
- Step 02 — Registration (users get created with a name and email)
- Step 03 — Login / Logout (`session["user_id"]`, `get_user_by_id()`, `current_user` context processor)

## Routes

- `GET /profile` — render the logged-in user's profile page; redirect to `GET /login` when not logged in — logged-in

## Database changes

No database changes — the `users` table already stores everything needed (`name`, `email`, `created_at`). No new columns, tables, or constraints.

## Templates

- **Create:** `templates/profile.html` — a section with the user's full name (heading), email, and joined date (formatted from `created_at`), plus a card-styled profile summary and a sign-out link/button reusing existing classes (`auth-*` not required; use a simple card layout consistent with the site with variables-only CSS)
- **Modify:** none

## Files to change

- `app.py` — replace the `/profile` placeholder with a real route: if no `session["user_id"]`, `redirect(url_for("login"))`; otherwise render `profile.html` with the current user row; the `current_user` context processor from Step 03 already supplies the data

## Files to create

- `templates/profile.html`
- (test file `tests/test_04-profile.py` is created by the test-feature step)

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — parameterized queries only, never string formatting in SQL
- Access control: check `session["user_id"]` in the route; logged-out visitors get a 302 redirect to `/login` before any rendering
- Always render the data of the logged-in user only — never a user id from the URL or query string
- `created_at` is stored as UTC SQLite `datetime('now')`; display it as a readable human date (e.g. "Joined Aug 2026") — parse defensively, never crash on a malformed value
- Do not expose `password_hash` or internal ids in the template
- Use CSS variables from `:root` in `static/css/style.css` — never hardcode hex colors; reuse existing card/typography classes where they fit, add only needed rules with variables
- All templates extend `base.html`; use `url_for()` for routes and static assets
- The navbar "My profile" link (landing hero, Step 03) must keep working unchanged

## Definition of done

- [ ] GET /profile while logged out redirects (302) to /login
- [ ] Logging in as demo@spendly.com / demo123 and visiting /profile shows "Demo User"
- [ ] The profile page shows the account's email address
- [ ] The profile page shows a readable joined/created date formatted from `created_at`
- [ ] A registered second user sees only their own name/email on /profile, never Demo User's
- [ ] The profile page never displays the password hash
- [ ] The landing "My profile" link navigates to the profile page for logged-in users
- [ ] `python -m pytest tests/test_04-profile.py -v` passes