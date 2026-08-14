# Log: Step 10 — Monthly Earnings

Date: 2026-08-14
Branch: feature/crud-earnings
Status: implemented + tested (19/19 new, full suite 172/172)

## What was done

- `database/db.py`: new `earnings` table appended to `SCHEMA` (id, user_id FK→users.id, month TEXT `YYYY-MM`, amount REAL NOT NULL, created_at, `UNIQUE (user_id, month)`; `CREATE TABLE IF NOT EXISTS` means existing local DBs pick it up on next startup). New functions: `upsert_earnings(user_id, month, amount)` — `INSERT ... ON CONFLICT(user_id, month) DO UPDATE SET amount = excluded.amount` (re-saving the same month overwrites, never duplicates); `get_earnings_by_user_id(user_id)` — SELECT ordered by month DESC.
- `app.py`: new `POST /earnings` route. Auth guard → 302 `/login`. Validation: month must match `re.fullmatch(r"\d{4}-\d{2}")` AND parse via `date.fromisoformat(month + "-01")` (catches 2026-13 and non-ASCII digits the regex alone would pass); amount via the same finite/positive rule as expenses. Failure → re-renders profile with `earnings_error` (uses refactored `render_profile(error=None)`), no write. Success → `upsert_earnings` → 302 `/profile`.
- Refactor: `profile()` became `render_profile(error=None)` (kept the `/profile` route wrapper) and gained `build_monthly_comparison(expenses, earnings_rows)` — union of expense months + earnings months, sorted DESC, net = earnings − spent only when both exist. Passes `monthly_comparison`, `current_month`, `earnings_error` to the template.
- `templates/profile.html`: new Monthly earnings card — form (month `type="month"` defaulting to current month + amount) and comparison table (Month | Earnings | Spent | Net; `—` for missing values; `net-positive`/`net-negative` classes). Also added an "Add expense" button in the transactions card header (making Step 07 reachable from the UI).
- `templates/base.html`: "Add expense" nav link for logged-in users (`nav-link`, styled by existing `.nav-links a`).
- `static/css/style.css`: added `.card-header`, `.earnings-form`, `.earnings-save`, `.earnings-table`, `.net-value`, `.net-positive` (var `--green`), `.net-negative` (var `--red`) — no hex.

## Issues encountered

- Same NaN/Infinity finding as Step 08 — earnings amount validation applies `math.isfinite` too; `nan`/`inf` regression cases included in tests.
- Note: the reviewer subagents (quality/security) were unavailable in this environment, so the review was performed inline by the main agent.

## Verification

- `python -m pytest tests/test_10-monthly-earnings.py -v` → 19/19 passed
- `python -m pytest -q` → 172/172 passed (Steps 01–10)

## Next

- Ship Steps 08–10 together: commit, push `feature/crud-earnings`, PR (squash-merge), delete branch.