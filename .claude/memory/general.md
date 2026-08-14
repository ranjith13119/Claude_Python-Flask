cross-project facts, preferences, environment setup — embedded in .claude/memory per AGENTS.md

Dependencies: pip install -r requirements.txt (flask, werkzeug, pytest, pytest-flask)
Run: python app.py — dev server on port 5001 (not Flask's default 5000), debug on
Tests: python -m pytest (no tests exist yet; pytest-flask is installed for them)
DB: expense_tracker.db at project root (local-only, listed in .gitignore, reseeded idempotently on app startup)
Passwords use werkzeug's current default hash method (scrypt:...), not pbkdf2:...
No ORMs (no SQLAlchemy); parameterized SQL queries only; passwords hashed with werkzeug
CSS uses variables from :root in static/css/style.css — never hardcode hex colors
All templates extend templates/base.html; use url_for() for routes/static assets
Git: never commit directly to main; work on feature/<slug> branches with Conventional Commit messages; squash-merge PRs, then delete branches
file.md at the root is junk (a stray terminal capture) — ignore it
Demo credentials: demo@spendly.com / demo123
App runs on port 5001 (not default 5000); debug mode on
Memory: .claude/memory/ initialized per AGENTS.md with memory.md index, general.md facts, domain/{topic}.md files, tools/{tool}.md configs