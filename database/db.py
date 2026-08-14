import sqlite3
from datetime import date, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent.parent / "expense_tracker.db"

CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other", "Investment"]

INVESTMENT_TYPES = ["MF", "Stocks", "Gold", "Bonds", "Crypto", "Real Estate", "Other"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    date TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS earnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    month TEXT NOT NULL,
    amount REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE (user_id, month)
);

CREATE TABLE IF NOT EXISTS investments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id)
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_user(name, email, password):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        return cur.lastrowid


def get_user_by_email(email):
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_user_by_id(user_id):
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_expenses_by_user_id(user_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC",
            (user_id,),
        ).fetchall()


def create_expense(user_id, amount, category, date, description):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description),
        )
        return cur.lastrowid


def get_expense_by_id(expense_id):
    with get_db() as conn:
        return conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()


def update_expense(expense_id, amount, category, date, description):
    with get_db() as conn:
        conn.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ?",
            (amount, category, date, description, expense_id),
        )


def delete_expense(expense_id):
    with get_db() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


def upsert_earnings(user_id, month, amount):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO earnings (user_id, month, amount) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, month) DO UPDATE SET amount = excluded.amount",
            (user_id, month, amount),
        )


def get_earnings_by_user_id(user_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM earnings WHERE user_id = ? ORDER BY month DESC",
            (user_id,),
        ).fetchall()


def create_investment(user_id, type, amount, date, note):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO investments (user_id, type, amount, date, note) VALUES (?, ?, ?, ?, ?)",
            (user_id, type, amount, date, note),
        )
        return cur.lastrowid


def get_investments_by_user_id(user_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM investments WHERE user_id = ? ORDER BY date DESC",
            (user_id,),
        ).fetchall()


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA)


def seed_db():
    with get_db() as conn:
        has_users = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        if has_users:
            return

        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()["id"]

        today = date.today()
        sample_expenses = [
            ("Lunch at cafe", "Food", 14.50, 0),
            ("Groceries for the week", "Food", 62.75, 1),
            ("Metro card top-up", "Transport", 25.00, 2),
            ("Electricity bill", "Bills", 58.20, 3),
            ("Pharmacy", "Health", 19.90, 4),
            ("Cinema tickets", "Entertainment", 22.00, 5),
            ("New sneakers", "Shopping", 79.99, 6),
            ("Miscellaneous", "Other", 12.30, 7),
            ("Gold coin", "Investment", 50.00, 8),
        ]

        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    user_id,
                    amount,
                    category,
                    (today - timedelta(days=offset)).isoformat(),
                    description,
                )
                for description, category, amount, offset in sample_expenses
            ],
        )