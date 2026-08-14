# Plan: Step 07 — Add Expense

Branch: `feature/add-expense` (based on main state — Steps 01–04 merged; Steps 05/06 live on the unmerged `feature/date-filter-profile` branch; spec at `.claude/spec/07-add-expense.md`)

## Steps

1. **database/db.py — add `create_expense()`**
   - `create_expense(user_id, amount, category, date, description)` — parameterised `INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)`, returns `cur.lastrowid`
   - Mirrors `create_user` style; no schema change (`expenses` table exists from Step 01)

2. **app.py — replace `/expenses/add` placeholder (line 108)**
   - Decorator: `methods=["GET", "POST"]`
   - Auth guard: `session.get("user_id") is None` → `redirect(url_for("login"))` (same pattern as `/profile`)
   - GET: render `add_expense.html` with `categories=CATEGORIES`, `today=date.today().isoformat()`
   - POST validation (all failures re-render form with `error`, insert nothing):
     - amount: present, `float()` parses, `> 0`
     - category: `in CATEGORIES`
     - date: `date.fromisoformat()` strict, not in the future
     - description: optional, `.strip()`, `None` if empty
   - Success: `create_expense(...)` then `redirect(url_for("landing"))` — PRG, never render on success

3. **templates/add_expense.html** (create)
   - Extends `base.html`; title "Add expense — Spendly"
   - Reuse existing classes: `auth-section`, `auth-card`, `auth-error`, `form-group`, `form-input`, `btn-submit`
   - Fields: amount (`type="number" step="0.01" min="0.01"`), category `<select class="form-select">` iterating `categories`, date (`type="date"` default `today`), description (optional)
   - No inline styles, no hex

4. **static/css/style.css** — add `.form-select` styled to match `.form-input` (border/background via `:root` variables)

5. **tests/test_07-add-expense.py** (create, from spec — ~16 tests)
   - Fixtures mirror test_04-profile.py: `fresh_db` (monkeypatch `db.DB_PATH` → tmp), `client`, `login()` helper
   - Access control: logged-out GET + POST → 302 `/login`
   - GET logged-in → 200, form fields present, all 7 categories in dropdown, date defaults to today
   - Valid POST → 302 `/`; row in DB with correct `user_id`, amount, category, date
   - Validation: missing amount/category/date, non-numeric amount, zero/negative amount, invalid date, future date → 200 + error, zero rows inserted
   - Description optional → stored as NULL
   - Template rules: extends base.html, no hex, no inline styles

6. **Verify** — `python -m pytest tests/test_07-add-expense.py -v` green, then `python -m pytest -q` full suite stays green

7. **Docs** — plan mirrored to `.opencode/plans/07-add-expense.md`; `Logs/07-add-expense.md`; update `memory/memory.md` + `.claude/memory/` index; update CLAUDE.md roadmap (Step 07 → complete after ship)

8. **Ship** — Conventional Commits (`feat:`, `docs:`) on `feature/add-expense`, push, PR (squash-merge convention)

## Notes / decisions

- No nav link to the form on landing/base.html — spec doesn't require it; Step 08/09 can add nav once list/edit exist
- Amount accepts standard float syntax; stored as REAL per convention
- Date defaults to today on fresh GET; no value repopulation on error (spec silent; keeps template simple)
- Builds on main's state — Steps 05/06 are NOT on this branch