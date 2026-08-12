# Implementation Plan — 04 Profile Page

**Branch:** `feature/profile`
**Spec:** `.claude/spec/04-profile.md` (identical copy in `.opencode/spec/`)
**Status:** Planned 2026-08-12 (static-UI version per user's revised spec)

## 1. Goal

Replace the `/profile` stub with a fully designed, **static** profile page: user info card, summary stats, transaction table, category breakdown — all hardcoded context, no DB calls. Establishes the UI before Step 05 wires real data, and the login guard pattern for protected routes.

## 2. Prerequisites

- Steps 01–03 complete (`users` table, registration, sessions + `current_user`)
- `feature/profile` branch created from clean `main`
- Spec revised by user: static/hardcoded data builds, no DB queries this step

## 3. Files

| File | Change |
| --- | --- |
| `app.py` | replace `/profile` stub: session guard + hardcoded context render |
| `templates/profile.html` | create — 4 sections, extends base.html, no inline styles |
| `static/css/style.css` | append `/* Profile page */` block — variables only, no hex |
| `tests/test_04-profile.py` | created in this run per mandatory-test rule |

## 4. Function-by-function

### 4.1 `app.py` — `profile()`

```python
@app.route("/profile")
def profile():
    if session.get("user_id") is None:
        return redirect(url_for("login"))
    return render_template("profile.html", ...)
```

- Guard BEFORE rendering (302 → /login)
- Context: `name="Demo User"`, `email="demo@spendly.com"`, `member_since="March 2026"`,
  `stats={total_spent:"₹12,450", transaction_count:24, top_category:"Food"}`,
  `transactions` = 3 dicts (date/description/category/amount),
  `category_breakdown` = 4 dicts (category/total/percent: 38/25/14/23)
- No `get_db()` calls anywhere in this route
- `current_user` context processor (Step 03) untouched — navbar still real

### 4.2 `templates/profile.html`

1. **User info card** — `.avatar` initials computed in Jinja
   (`{{ (name.split() | map('first') | join('')) | upper }}`), name, email, member-since
2. **Stats row** — 3 `.stat-card` cells (value + label)
3. **Transaction table** — `.profile-table`, header row + exactly 3 data rows, category as `.cat-badge`
4. **Category breakdown** — `.breakdown-row` grid: name · `.bar-track`+`.bar-fill pct-<n>` · total · percent text

No inline styles: bar fill widths via exact-value classes `.pct-14/23/25/38`.

### 4.3 `static/css/style.css` — appended block

- Layout/cards: `.profile-section/-container/-card`, `.stats-row`, `.stat-card`, `.section-title`
- Info: `.avatar`, `.profile-name/-email/-meta`
- Table: `.profile-table` (+ `.amount-col`)
- Badges: `.cat-badge` (uniform `--accent-light` on `--accent` — no per-color hex)
- Breakdown: `.breakdown-row/-name/-total/-pct`, `.bar-track`, `.bar-fill`, `.pct-*` widths
- All colors/typography from `:root` variables; zero hex values

## 5. Error handling table

| Scenario | Behavior |
| --- | --- |
| Logged out, GET /profile | 302 → /login |
| Logged in, GET /profile | 200, static profile UI |
| Any user logged in | same static page (intentional — Step 05 wires real data) |

## 6. Definition of done (from spec)

- [x] Visiting /profile without being logged in redirects to /login
- [x] Visiting /profile while logged in returns HTTP 200
- [x] The page displays a user info card with a name and email
- [x] The page displays at least three summary stat values
- [x] The page displays a transaction history table with at least three hardcoded rows
- [x] The page displays a category breakdown section with at least three categories
- [x] The navbar shows the logged-in state (username + logout link)
- [x] No hex colour values appear in profile.html — only CSS variables

## 7. Verification

- Automated: `tests/test_04-profile.py` — 11 tests (guard 302/200, all 4 sections, navbar state, no password hash, hex-free + extends-base file rules). Full suite: 58 passed.
- Manual: `python app.py` → logged-in /profile renders all four sections.

## 8. Ship steps

1. Commit: `feat: add static profile page with hardcoded data`
2. Push, PR title "Add profile page", squash-merge, delete branches
3. Update CLAUDE.md roadmap: Step 04 ✅ Complete (tests: 11/11); memory.md log entry