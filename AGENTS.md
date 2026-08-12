# AGENTS.md

Spendly: a Flask expense tracker built incrementally as a teaching project ("Steps 1–9"). The repo is currently an early scaffold.

## Setup and run

- Dependencies: `pip install -r requirements.txt` (flask, werkzeug, pytest, pytest-flask).
- Run: `python app.py` — dev server on **port 5001** (not Flask's default 5000), debug on. Visit http://localhost:5001.
- Tests: `python -m pytest` (no tests exist yet; pytest-flask is installed for them).

## Testing (mandatory)

- Every implemented feature MUST be tested before it is marked done: write `tests/test_<step>-<slug>.py` from the spec (never derive tests from the implementation), run `python -m pytest tests/test_<step>-<slug>.py -v` until green. Existing example: `tests/test_01-database-setup.py` (15 tests).
- DB tests must monkeypatch `database.db.DB_PATH` to a tmp path — never write to the committed `expense_tracker.db`. Demo credentials: demo@spendly.com / demo123.

## Gotchas

- **README.md is UTF-16 LE encoded** — the Read tool fails on it with "Cannot read binary file". Read it via `Get-Content -Encoding Unicode` (Windows) or `iconv -f UTF-16` (Unix). It contains nothing useful beyond the title.
- `database/db.py` implements the data layer (`get_db()`, `init_db()`, `seed_db()`) against `expense_tracker.db` at the project root. The DB file is local-only (listed in `.gitignore`, untracked since PR #2) and reseeded idempotently on app startup (`python app.py`). Passwords use werkzeug's current default hash method (`scrypt:...`), not `pbkdf2:`.
- Most routes in `app.py` are placeholders returning plain-text "coming in Step N" (e.g. `/logout`, `/expenses/add`). Only `/`, `/register`, `/login` render templates.
- `file.md` at the root is junk (a stray terminal capture) — ignore it.

## Conventions (de-facto project rules)

- No ORMs (no SQLAlchemy); parameterized SQL queries only; passwords hashed with werkzeug.
- CSS uses variables from `:root` in `static/css/style.css` — never hardcode hex colors.
- All templates extend `templates/base.html`; use `url_for()` for routes/static assets.
- Git: never commit directly to main; work on `feature/<slug>` branches with Conventional Commit messages; squash-merge PRs, then delete branches.
- `.claude/commands/` defines a spec-driven workflow (`create-spec`, `test-feature`, `ship-feature`) that references `CLAUDE.md` and `.claude/specs/` — **neither exists yet**; they are expected to be created as the project progresses. Test files follow `tests/test_<step>-<slug>.py` naming. Same commands are ported to opencode at `.opencode/command/` (same spec storage in `.claude/specs/`); keep the two in sync.

## Memory 

- Store our important conversation in the local memory 'memory.md' in the memory folder 
- Store all the created specification in the specs folder 
- Always create an detailed implementation plan for each spec and store it in plans folder
- Strictly don't push any sensitive information to LLM, GIT, etc., 
- Create a Log file under Logs folder for each feature 