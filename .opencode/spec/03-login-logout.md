# Spec: Login and Logout

## Overview

Registered users can sign in with their email and password to start a session, and sign out from the navbar when done. Successful login stores the user's id in the Flask session cookie, so subsequent requests know who is logged in. Failed logins (unknown email or wrong password) show a single generic error so the form does not reveal which credential was wrong. This feature converts the existing static `/login` and placeholder `/logout` routes into the session foundation that every "logged-in only" feature (Profile, backend connection, expense list, add/edit/delete) builds on.

## Depends on

- Step 01 — Database setup (`users` table, hashed passwords via werkzeug)
- Step 02 — Registration (`create_user()`, `app.secret_key` already set, lowercase email convention)

## Routes

- `GET /login` — render the sign-in form — public
- `POST /login` — verify credentials, start session, redirect to `/` on success; re-render form with a generic error on failure — public
- `POST /logout` — clear the session, redirect to `/` — logged-in (harmless when not logged in)

## Database changes

No schema changes — the `users` table already stores `email` and `password_hash`.

Add one helper to `database/db.py`:

- `get_user_by_email(email)` — parameterized `SELECT` returning the user row (sqlite3.Row) or `None` when no match.

## Templates

- **Modify:** `templates/login.html` — change hardcoded `action="/login"` to `action="{{ url_for('login') }}"`. Form fields, `{{ error }}` block, and "Create one free" link stay as-is.
- **Modify:** `templates/base.html` — make the navbar session-aware:
  - Logged out: current "Sign in" + "Get started" links
  - Logged in: show the logged-in user's email and a small "Log out" `<form method="POST" action="{{ url_for('logout') }}">` button — never a GET link
  - The base template reads the logged-in user from a `current_user` template variable

## Files to change

- `app.py` — add `session` import; implement POST handling for `/login`, real `/logout`, and an `@app.context_processor` that injects `current_user` (the user row or `None`) using `session["user_id"]`
- `database/db.py` — add `get_user_by_email()`
- `templates/login.html` — form action via `url_for()`
- `templates/base.html` — session-aware navbar

## Files to create

- None (test file `tests/test_03-login-logout.py` is created by the test-feature step)

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — parameterized queries only, never string formatting in SQL
- Passwords verified with werkzeug `check_password_hash` — never compare plain text; never log or echo passwords
- Email normalized to lowercase (`email.strip().lower()`) before lookup, matching Step 02's convention
- Use a single generic error "Invalid email or password" for both unknown email and wrong password — never reveal which failed
- Login success: `session["user_id"] = user["id"]` then redirect (POST-Redirect-GET), never render a template
- Logout must use POST only (CSRF-safe) and clear the whole session
- `current_user` lookup on every request via context processor; a missing/invalid `user_id` in session must render as logged out, never crash
- Use CSS variables from `:root` in `static/css/style.css` — never hardcode hex colors; reuse existing `auth-*`/`form-*`/nav classes
- All templates extend `base.html`; use `url_for()` for routes and static assets
- Never echo the submitted password back into the template

## Definition of done

- [ ] GET /login renders the sign-in form with email and password fields
- [ ] Logging in with demo@spendly.com / demo123 redirects to / and starts a session
- [ ] The navbar shows the logged-in user's email and a Log out button instead of Sign in / Get started
- [ ] Logging in with the wrong password shows "Invalid email or password", not a 500
- [ ] Logging in with an unknown email shows the same generic error
- [ ] A logged-in session persists across multiple requests
- [ ] POST /logout clears the session, redirects to /, and the navbar returns to the logged-out state
- [ ] An invalid or stale user_id in the session renders pages fine as logged out (no crash)
- [ ] `python -m pytest tests/test_03-login-logout.py -v` passes