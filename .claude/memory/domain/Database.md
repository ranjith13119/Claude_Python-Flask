domain-specific knowledge: database layer

database/db.py implements the data layer (get_db(), init_db(), seed_db()) against expense_tracker.db at the project root
The DB file is local-only (listed in .gitignore, untracked since PR #2) and reseeded idempotently on app startup (python app.py)
Passwords use werkzeug's current default hash method (scrypt:...), not pbkdf2:
All queries use parameterized SQL queries only — no ORMs (no SQLAlchemy)
seed_db() creates 1 user + 8 expenses linked to the demo user, categories: Food, Transport, Bills, Other, Entertainment, Shopping
expenses table: id, user_id, amount (float), category (text), date (text, yyyy-mm-dd), description (text), created_at (datetime)
get_db() returns sqlite3 connection; init_db() creates tables if not exist; seed_db() populates demo data
monkeypatch database.db.DB_PATH to a tmp path for tests — never write to the committed expense_tracker.db
Demo credentials: demo@spendly.com / demo123