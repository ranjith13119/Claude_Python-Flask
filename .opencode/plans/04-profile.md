# Plan: Step 04 — Profile (static UI)

Branch: `feature/profile` (based on rollback commit f3b5849 / Step 03 state)

## Steps

1. **app.py — `/profile` route**
   - Replace `"Profile page — coming in Step 4"` placeholder with a session-guarded route:
     `if session.get("user_id") is None: return redirect(url_for("login"))`
   - `render_template("profile.html", ...)` with hardcoded context: name, email, member_since, stats dict (total_spent, transaction_count, top_category), transactions list (3 rows, ₹-formatted), category_breakdown (4 entries, percents 38/25/14/23). No DB calls this step.

2. **templates/profile.html** (create, extends base.html)
   - Identity header: avatar initials via `{{ name.split() | map("first") | join("") | upper }}`, name, email, member-since.
   - Account card (email, member since), 3 stat cards, transactions table (Date/Description/Category/Amount + `.cat-badge`), category breakdown with `.bar-fill.pct-{n}` progress bars.
   - No hex colors, no inline styles, all routes via `url_for()`.

3. **static/css/style.css** — append Profile block
   - New classes: `.profile-*`, `.avatar`, `.stat-card`, `.stats-row`, `.expenses-table`, `.cat-badge`, `.bar-track`, `.bar-fill.pct-*`, `.breakdown-*`.
   - Only `:root` variables; pct widths via exact-value classes (25/14/23/38). Responsive: stats-row collapses at 600px.

4. **tests/test_04-profile.py** (create, from spec — 12 tests)
   - Fixtures: `fresh_db` (tmp DB_PATH + init/seed) and `client` (TESTING), `logged_in` helper (POST /login).
   - Access control, content (identity, stat cards, table, breakdown percents), navbar logged-in state, no hash leak, extends base.html, no hex/inline styles.

5. **Verify** — `python -m pytest tests/test_04-profile.py -v` (12/12) then full suite (59/59).

6. **Docs** — spec already at `.claude/spec/04-profile.md` (+ `.opencode/spec/` mirror); this plan mirrored to `.opencode/plans/04-profile.md`; `Logs/04-profile.md` per AGENTS.md; update `memory/memory.md`.

7. **Ship** — commit on `feature/profile`, push, PR (Conventional Commit, squash-merge convention).

## Notes / decisions

- UI first: hardcoded data, no DB queries (Step 05 wires backend).
- Reuse existing design language (ink/paper/accent palette, DM fonts) — no new design system, no frontend-design skill (banned per user).
- `git status` pre-start was clean on Step 03 baseline; test file naming follows `tests/test_<step>-<slug>.py`.