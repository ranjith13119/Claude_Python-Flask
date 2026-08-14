# Spec: Profile

## Overview

Logged-in users can view a personal Profile page that shows who they are (name, email, member since) plus a read-only snapshot of their spending: three stat cards (total spent, transaction count, top category), a recent-transactions table, and a category breakdown with progress bars. This step is deliberately UI-first: the page renders hardcoded demo data so the layout and styling can be reviewed before real data is wired in. Step 05 ("Backend connection") will replace the hardcoded context with real queries against the `expenses` table; nothing in this step touches the database beyond what already exists.

## Depends on

- Step 01 — Database setup (`users` / `expenses` tables exist)
- Step 03 — Login / Logout (`session["user_id"]` and the `current_user` context processor)

## Routes

- `GET /profile` — render the profile page — logged-in only (302 to `/login` when there is no session)

## Database changes

No schema changes and no new queries. The route receives all context from hardcoded Python data in `app.py` (Step 05 replaces it with DB calls).

## Templates

- **Create:** `templates/profile.html` — extends `base.html`; four sections:
  - Avatar initials block (derive initials from the first letters of the name) + name + email + member-since line
  - User info card (email, member since)
  - Three stat cards: total spent, transaction count, top category
  - Recent transactions table with rows of date / description / category / amount and a category badge
  - Category breakdown with progress bars showing percentage per category
- **Modify:** none — the navbar already renders the logged-in state via `current_user` from Step 03

## Files to change

- `app.py` — replace the `/profile` placeholder ("Profile page — coming in Step 4") with a session-guarded route that renders `profile.html` with hardcoded context (name, email, member_since, stats dict, transactions list, category_breakdown list with percents)

## Files to create

- `templates/profile.html`
- (test file `tests/test_04-profile.py` is created by the test-feature step)

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — parameterized queries only (no new queries this step, but keep the rule for anything touched)
- Passwords hashed with werkzeug — never render or expose any hash in the template
- Session guard first: `if session.get("user_id") is None: return redirect(url_for("login"))`
- No inline styles or hardcoded hex colors in the template — all colors from CSS variables in `:root` in `static/css/style.css`; use the existing look first, extend `:root` variables for new elements if needed (no UI redesign, no new design system)
- Bar widths in the category breakdown via exact percentage classes (e.g. `.pct-38`) — never arbitrary inline `width:` values
- Amounts formatted as strings with the rupee symbol (e.g. "₹12,450") in the hardcoded context — no currency logic in the template
- All templates extend `base.html`; use `url_for()` for routes and static assets
- Do not add any new product-wide design language: reuse the current page layouts, typography, and spacing from the existing landing/register/login pages
- Category names must match the fixed list: Food, Transport, Bills, Health, Entertainment, Shopping, Other

## Definition of done

- [ ] GET /profile while logged out responds 302 and redirects to /login
- [ ] GET /profile while logged in responds 200 and renders four sections: avatar/identity, user info card, three stat cards, transactions table, category breakdown with progress bars
- [ ] The page shows the demo user's name, email, and a member-since value
- [ ] The three stat cards show total spent, transaction count, and top category
- [ ] The transactions table has rows with date, description, category, and amount columns
- [ ] The category breakdown shows percentages that sum to 100
- [ ] The navbar on /profile shows the logged-in state (email + Log out), not Sign in / Get started
- [ ] No password hash or password-related value appears anywhere on the page
- [ ] `templates/profile.html` extends `base.html` via `url_for()`, uses no hex colors, and has no inline styles
- [ ] `python -m pytest tests/test_04-profile.py -v` passes