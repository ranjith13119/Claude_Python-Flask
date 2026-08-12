# Implementation Plan — 02 Registration

**Branch:** `feature/registration`
**Spec:** `.claude/spec/02-registration.md` (identical copy in `.opencode/spec/`)
**Status:** Planned 2026-08-12

## 1. Goal

Let visitors create a Spendly account (name, email, password) with server-side validation, werkzeug-hashed passwords, and friendly error messages. First feature that writes user-provided data to the DB — establishes form-handling patterns reused by Steps 03/04.

## 2. Prerequisites

- Step 01 complete: `users` table (id PK, name NOT NULL, email NOT NULL UNIQUE, password_hash NOT NULL, created_at), `get_db()` with Row factory + FK pragma
- `feature/registration` branch created from clean `main`

## 3. Files

| File | Change |
| --- | --- |
| `database/db.py` | add `create_user(name, email, password)` helper |
| `app.py` | add `request`/`redirect`/`url_for` imports, `app.secret_key`, POST handling for `/register` |
| `templates/register.html` | `action="/register"` → `url_for('register')` |
| `tests/test_02-registration.py` | created later via `/test-feature 02-registration` |

## 4. Function-by-function

### 4.1 `database/db.py` — `create_user()`

```python
def create_user(name, email, password):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        return cur.lastrowid
```

- Parameterized query only; `generate_password_hash` (werkzeug, `scrypt:` default)
- Duplicate email → `sqlite3.IntegrityError` propagates (route catches)
- `generate_password_hash` already imported (used by `seed_db`)

### 4.2 `app.py` — `/register` GET+POST

Imports: add `request`, `redirect`, `url_for` to the flask import line. Add after `app = Flask(__name__)`:
`app.secret_key = os.environ.get("SPENDLY_SECRET_KEY", "dev-secret-key")` (+ `import os`) — foundation for Step 03 sessions.

```python
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required")
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters")

        try:
            create_user(name, email, password)
        except sqlite3.IntegrityError:
            return render_template("register.html", error="An account with this email already exists")

        return redirect(url_for("login"))

    return render_template("register.html")
```

- `from database.db import init_db, seed_db, create_user`; `import sqlite3`
- Never echo the password back into the template
- Success = 302 redirect to `/login` (POST-Redirect-GET)

### 4.3 `templates/register.html`

Single change: `<form method="POST" action="{{ url_for('register') }}">`. Error block, `required` attributes, classes (`auth-card`, `form-input`, `btn-submit` — all exist in `style.css`) stay untouched.

## 5. Error handling table

| Scenario | Behavior |
| --- | --- |
| Empty name/email/password | 200 + "All fields are required" |
| Password < 8 chars | 200 + "Password must be at least 8 characters" |
| Duplicate email | `IntegrityError` → 200 + "An account with this email already exists" |
| Valid submission | 302 → `/login`; user row with hashed password |
| Email with uppercase | stored lowercase |

## 6. Definition of done (from spec)

- [ ] GET /register renders the form with name, email, and password fields
- [ ] Submitting a valid new account creates a user row in the database
- [ ] Stored password is a werkzeug hash, not plain text, and verifies against the submitted password
- [ ] Submitting the same email twice shows the friendly duplicate-email error, not a 500
- [ ] Password shorter than 8 characters shows a friendly error on the form
- [ ] Empty fields show a friendly error on the form
- [ ] Successful registration redirects to /login
- [ ] Registered email is stored lowercase
- [ ] `python -m pytest tests/test_02-registration.py -v` passes

## 7. Verification

1. Manual: run `python app.py` → `GET /register` renders form; POST valid → redirected to /login; duplicate/short/empty → errors shown
2. Automated (after `/test-feature 02-registration`): pytest-flask `test_client`, `monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")` + `init_db()` fixture — never touch real `expense_tracker.db`
3. `python -m pytest tests/test_02-registration.py -v` until green

## 8. Ship steps

1. Commit: `feat: add user registration with validation`
2. Push, PR title "Add user registration", squash-merge, delete branches
3. Update CLAUDE.md roadmap: Step 02 ✅ Complete