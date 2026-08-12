# Implementation Plan — 03 Login and Logout

**Branch:** `feature/login-logout`
**Spec:** `.claude/spec/03-login-logout.md` (identical copy in `.opencode/spec/`)
**Status:** Planned 2026-08-12

## 1. Goal

Session-based authentication: sign in with email/password, sign out via POST, session-aware navbar. Foundation for all logged-in-only features (Steps 04–09).

## 2. Prerequisites

- Steps 01–02 complete (users table, `create_user`, `app.secret_key`, lowercase email convention)
- `feature/login-logout` branch created from clean `main`

## 3. Files

| File | Change |
| --- | --- |
| `database/db.py` | add `get_user_by_email(email)` |
| `app.py` | `session` import, `login()` GET+POST, real `logout()`, `@app.context_processor` for `current_user` |
| `templates/login.html` | `action` → `url_for('login')` |
| `templates/base.html` | session-aware navbar (repo pattern exists in `style.css`) |
| `tests/test_03-login-logout.py` | created later via `/test-feature 03-login-logout` |

## 4. Function-by-function

### 4.1 `database/db.py`

```python
def get_user_by_email(email):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
```

Returns `sqlite3.Row` or `None`. Parameterized. Place before/after `create_user` (module-level, no deps).

### 4.2 `app.py`

Imports: add `session` to the flask import line; add `check_password_hash` to the werkzeug import (`from werkzeug.security import check_password_hash`).

Context processor (registered right after routes, used by `base.html`):

```python
@app.context_processor
def inject_current_user():
    user_id = session.get("user_id")
    user = None
    if user_id is not None:
        with db.get_db() as conn:  # or get_user_by_email + by-id lookup
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return {"current_user": user}
```

- Plan: add `get_user_by_id(id)` alongside `get_user_by_email` for a clean lookup (documented in spec as part of helper work) — or reuse a single helper. Decision: add both helpers, each one-liner.
- Never crash on stale session: `SELECT` returns `None` → navbar shows logged-out state. **Do not silently clear** — rendering as logged out is enough per spec.

`login()`:

```python
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password")
        session["user_id"] = user["id"]
        return redirect(url_for("landing"))
    return render_template("login.html")
```

- Generic error for both failure modes (spec rule).
- Success: session + redirect (POST-Redirect-GET).

`logout()` — replace placeholder:

```python
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("landing"))
```

- POST-only (spec rule).

### 4.3 `templates/login.html`

One-line change: `<form method="POST" action="{{ url_for('login') }}">`. `{{ error }}` block already present.

### 4.4 `templates/base.html`

Navbar links section becomes:

```jinja
<div class="nav-links">
  {% if current_user %}
    <span class="nav-user">{{ current_user["email"] }}</span>
    <form method="POST" action="{{ url_for('logout') }}" class="nav-logout">
      <button type="submit" class="nav-cta">Log out</button>
    </form>
  {% else %}
    <a href="{{ url_for('login') }}">Sign in</a>
    <a href="{{ url_for('register') }}" class="nav-cta">Get started</a>
  {% endif %}
</div>
```

- Reuse existing nav classes; a small `.nav-user`/`.nav-logout` rule in `style.css` using CSS variables only if spacing needs it (prefer existing classes first).
- If `auth-*`/`nav-*` classes don't cover the inline form, add minimal CSS with variables from `:root` (e.g. `var(--accent)`) — never a hardcoded hex.

## 5. Error handling table

| Scenario | Behavior |
| --- | --- |
| Correct credentials | 302 → `/`; `session["user_id"]` set |
| Wrong password | 200 + "Invalid email or password" |
| Unknown email | 200 + same generic error |
| Empty fields | 200 + same generic error |
| POST /logout | session cleared; 302 → `/` |
| Stale/forged `user_id` in session | renders as logged out, no crash |

## 6. Definition of done (from spec)

- [ ] GET /login renders the sign-in form with email and password fields
- [ ] Logging in with demo@spendly.com / demo123 redirects to / and starts a session
- [ ] The navbar shows the logged-in user's email and a Log out button instead of Sign in / Get started
- [ ] Wrong password shows "Invalid email or password", not a 500
- [ ] Unknown email shows the same generic error
- [ ] A logged-in session persists across multiple requests
- [ ] POST /logout clears the session, redirects to /, navbar returns to logged-out state
- [ ] Invalid/stale user_id in session renders fine as logged out
- [ ] `python -m pytest tests/test_03-login-logout.py -v` passes

## 7. Verification

1. Manual: `python app.py` → login with demo credentials → navbar switches; logout → navbar reverts; wrong password → generic error
2. Automated (test-feature step): pytest-flask test_client, monkeypatch `db.DB_PATH` to tmp, `init_db()` + `seed_db()` — never touch real `expense_tracker.db`
3. Session tests: use `client.post("/login", ...)` then assert `session["user_id"]` via `client.session_transaction()`
4. Full suite regression: `python -m pytest -q` (expect 27 existing + new all green)

## 8. Ship steps

1. Commit: `feat: add login and logout with sessions`
2. Push, PR title "Add login and logout", squash-merge, delete branches
3. Update CLAUDE.md roadmap: Step 03 ✅ Complete; memory.md log entry