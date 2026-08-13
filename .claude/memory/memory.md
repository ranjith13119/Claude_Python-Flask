# memory.md — project memory index

Updated whenever a memory file is created or modified.

Entries: date | what | why

2026-08-13 | memory system initialized for expense-tracker | structuring per AGENTS.md alongside CLAUDE.md and AGENTS.md
2026-08-13 | general.md created | core project facts: demo credentials, port 5001, DB path, werkzeug scrypt, no-ORM rule
2026-08-13 | domain/Database.md created | DB layer: get_db/init_db/seed_db, seed data, scrypt hashing, monkeypatch DB_PATH
2026-08-13 | domain/Frontend.md created | CSS :root variables, template conventions, navbar states, no hex rule
2026-08-13 | tools/frontend-design.md removed | skill banned by user — Steps 04–06 (profile/expenses UI refactor) rolled back to Step 03
2026-08-13 | Step 05 backend connection implemented + tested | /profile now live: get_expenses_by_user_id(), ₹ formatting, top category Shopping for seed, pct-0..100 CSS classes, stale-session redirect; test_04 updated to real values; 74/74 suite green
2026-08-13 | Step 06 date filter implemented + tested | /profile?from_date&to_date query-param filter (valid_date helper, YYYY-MM-DD string compare, invalid ignored), filter form + empty state in profile.html, .filter-* CSS block; 18/18 new, 92/92 suite green
