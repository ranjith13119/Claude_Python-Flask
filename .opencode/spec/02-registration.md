# Spec: Registration

## Overview

Users can create a Spendly account with their full name, email address, and password. Successful registration inserts the user into the `users` table with a werkzeug-hashed password and redirects to the login page; duplicate emails and invalid input are rejected with a clear error message shown on the form. This is the first feature that writes user-provided data to the database, so it establishes the project's form-handling and validation patterns that login (Step 03) and profile (Step 04) will reuse.

## Depends on

- Step 01 — Database setup (`users` table with `id`, `name`, `email` UNIQUE, `password_hash`, `created_at`; `get_db()` in `database/db.py`)

## Routes

- `GET /register` — render the registration form — public (template already renders; keep GET handling)
- `POST /register` — validate input, create account, redirect to `/login` on success; re-render form with error on failure — public

## Database changes

No schema changes — the `users` table from Step 01 already covers all needed columns.

Add one helper to `database/db.py`:

- `create_user(name, email, password)` — inserts a new user with `generate_password_hash(password)` using a parameterized query; returns the new user's `id`. Duplicate email raises `sqlite3.IntegrityError`, which the route must catch and convert into a friendly error.

## Templates

- **Modify:** `templates/register.html` — change the hardcoded `action="/register"` to `action="{{ url_for('register') }}"`. The form (name/email/password), `required` attributes, `{{ error }}` display, and "Sign in" link already exist and stay as-is.

## Files to change

- `app.py` — import `request`, `redirect`, `url_for`, `flash`-free error handling; add `app.secret_key = os.environ.get(...)` fallback; implement POST handling for `/register` with validation; pass `error` to the template on failure
- `database/db.py` — add `create_user()` helper
- `templates/register.html` — form action via `url_for()`

## Files to create

- None (test file `tests/test_02-registration.py` is created by the test-feature step)

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — parameterized queries only, never string formatting in SQL
- Passwords hashed with werkzeug `generate_password_hash` (current default `scrypt:...`) — never store plain text
- Email normalized to lowercase (`email.strip().lower()`) before insert/check; name stripped
- Password min 8 characters — server-side validation with friendly error
- Duplicate email caught via `sqlite3.IntegrityError` → error message "An account with this email already exists"
- Missing/empty fields → re-render form with a friendly error, never a 500
- Use CSS variables from `:root` in `static/css/style.css` — never hardcode hex colors; reuse existing `auth-*`/`form-*` classes already in the templates
- All templates extend `base.html`; use `url_for()` for routes and static assets
- On success, redirect to `login` (POST-Redirect-GET pattern) — do not render login as a template response
- Never echo the submitted password back into the template

## Definition of done

- [ ] GET /register renders the form with name, email, and password fields
- [ ] Submitting a valid new account creates a user row in the database
- [ ] Stored password is a werkzeug hash, not plain text, and verifies against the submitted password
- [ ] Submitting the same email twice shows the friendly duplicate-email error, not a 500
- [ ] Password shorter than 8 characters shows a friendly error on the form
- [ ] Empty fields show a friendly error on the form
- [ ] Successful registration redirects to /login
- [ ] Registered email is stored lowercase
- [ ] `python -m pytest tests/test_02-registration.py -v` passes (written from this spec by the test step)