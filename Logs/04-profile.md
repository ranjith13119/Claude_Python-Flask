# Log: Step 04 — Profile (static UI)

Date: 2026-08-13
Branch: feature/profile
Status: implemented + tested (12/12 new, full suite 59/59)

## What was done

- `/profile` route: session guard (302 to /login when logged out) + `render_template("profile.html", ...)` with hardcoded context (Demo User, demo@spendly.com, March 2026, stats, 3 transactions, 4-category breakdown). No DB calls this step; Step 05 wires the backend.
- `templates/profile.html`: identity header with Jinja-derived avatar initials, account card, 3 stat cards, transactions table with `.cat-badge`, category breakdown with `.bar-fill.pct-{n}` progress bars. Extends base.html; no hex, no inline styles.
- `static/css/style.css`: appended Profile block using only `:root` variables; exact-value pct classes (25/14/23/38); responsive collapse of stats/breakdown at 600px.
- `tests/test_04-profile.py`: 12 tests (access control 2, content 6, template rules 4).

## Issues encountered

- Initial test included `url_for(` check on profile.html — wrong: url_for lives in base.html; template-rule tests only assert `{% extends "base.html" %}` + no hex + no inline styles (matches original Step 04 convention). Removed that test.

## Verification

- `python -m pytest tests/test_04-profile.py -v` → 12/12 passed
- `python -m pytest -q` → 59/59 passed

## Next

- Ship: commit, push, PR (step 04 returns profile UI to the app after the Step 03 rollback).
- Step 05 (Backend connection) will replace hardcoded context with DB queries.