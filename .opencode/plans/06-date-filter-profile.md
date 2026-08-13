# Plan: Step 06 — Date Filter for Profile Page

Branch: `feature/date-filter-profile` (based on Step 05 state — live-data profile page; spec at `.claude/spec/06-date-filter-profile.md`)

## Steps

1. **app.py — `/profile` route: read + validate filter params**
   - `from_date = request.args.get("from_date", "")`, `to_date = request.args.get("to_date", "")`
   - Validate with `datetime.date.fromisoformat`; on `ValueError` (malformed/out-of-range) treat as absent (empty string) — never 400/500
   - Filter the `transactions` list: keep row when `(not from_date or row["date"] >= from_date)` and `(not to_date or row["date"] <= to_date)` — string compare on YYYY-MM-DD only
   - Do not mutate the original list (build a new filtered list)
   - Pass `from_date` and `to_date` back to `render_template` so the form stays filled

2. **templates/profile.html — filter bar above "Recent transactions"**
   - Add `<form method="GET" action="{{ url_for('profile') }}" class="filter-form">` with:
     - `<label>` From: `<input type="date" name="from_date" value="{{ from_date }}">`
     - `<label>` To: `<input type="date" name="to_date" value="{{ to_date }}">`
     - Filter submit button (class `filter-btn`)
     - Reset link `<a href="{{ url_for('profile') }}" class="filter-reset">Reset</a>` (clears both params)
   - Empty state: when `transactions` is empty after filtering, render a `<tr>` with `<td colspan="4">` message ("No transactions in this date range." or "No transactions yet." when unfiltered)
   - No inline styles; all classes styled in style.css

3. **static/css/style.css — append filter block**
   - `.filter-form`, `.filter-field`, `.filter-btn`, `.filter-reset`, `.filter-empty` — all colors via `:root` variables, no hex, no inline styles
   - Date inputs styled to match existing form controls if present (reuse variables)

4. **tests/test_06-date-filter-profile.py** (create, from spec — ~12 tests)
   - Fixtures: `fresh_db`, `client`, `logged_in` (mirror test_05 style)
   - Filter behavior (seed expenses are dated `today - offset` for offset 0..7):
     - `from_date` = today → only "Lunch at cafe" visible
     - `to_date` = today-7 → only "Miscellaneous" visible
     - both set → inclusive range rows only
     - empty range (e.g. from_date=tomorrow) → empty-state message, 200
   - Invalid dates (`abc`, `2026-02-30`) → 200 with full list (no 500)
   - Reset link present in page and clears params (`href` ends with `/profile`)
   - Form inputs pre-filled after filtering
   - Access control: logged-out still 302 → /login
   - Template rules: extends base.html, no hex, no inline styles
   - Stats/breakdown unchanged by filter (spec: filter applies to transactions list only)

5. **Verify** — `python -m pytest tests/test_06-date-filter-profile.py -v` (all green), then full suite `python -m pytest -q` (stays green)

6. **Docs** — plan mirrored to `.opencode/plans/06-date-filter-profile.md`; `Logs/06-date-filter-profile.md`; update `memory/memory.md` + `.claude/memory/` index; update CLAUDE.md roadmap (Step 06 → complete)

7. **Ship** — commit on `feature/date-filter-profile` (Conventional Commits: `feat:` + `docs:`), push, PR (squash-merge convention)

## Notes / decisions

- Filter applies ONLY to the transactions table; stat cards and category breakdown stay full-range (spec scopes it to the transaction list)
- Dates compared as strings — seed format is already `YYYY-MM-DD` (ISO from `date.today().isoformat()`)
- Empty state text distinguishes filtered vs unfiltered empty (filtered: "No transactions in this date range.")
- Use `datetime.date.fromisoformat` — `datetime.datetime` would also accept `2026-08-13T00:00`, but spec says strict YYYY-MM-DD
- `from_date`/`to_date` default to `""` so the template `value=""` renders empty inputs on first visit