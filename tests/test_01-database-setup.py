import re
import sqlite3

import pytest
from werkzeug.security import check_password_hash

from database import db

EXPECTED_CATEGORIES = {"Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other", "Investment"}


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    db.seed_db()
    yield tmp_path / "test.db"


def get_user_count():
    with db.get_db() as conn:
        return conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]


def get_expense_count():
    with db.get_db() as conn:
        return conn.execute("SELECT COUNT(*) AS count FROM expenses").fetchone()["count"]


class TestDatabaseFile:
    def test_db_file_created_on_startup(self, fresh_db):
        assert fresh_db.exists()


class TestSchema:
    def test_both_tables_exist(self):
        with db.get_db() as conn:
            tables = {
                row["name"]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            }
        assert {"users", "expenses"} <= tables

    def test_users_schema(self):
        with db.get_db() as conn:
            columns = {row["name"]: row for row in conn.execute("PRAGMA table_info(users)").fetchall()}
        assert columns["id"]["type"].upper() == "INTEGER"
        assert columns["id"]["pk"] == 1
        assert columns["name"]["notnull"] == 1
        assert columns["email"]["notnull"] == 1
        assert columns["password_hash"]["notnull"] == 1
        assert "datetime" in columns["created_at"]["dflt_value"].lower()

    def test_email_is_unique(self):
        with db.get_db() as conn:
            indexes = conn.execute("PRAGMA index_list(users)").fetchall()
        assert any("unique" in row["origin"] or row["unique"] for row in indexes)

    def test_expenses_schema(self):
        with db.get_db() as conn:
            columns = {row["name"]: row for row in conn.execute("PRAGMA table_info(expenses)").fetchall()}
            foreign_keys = conn.execute("PRAGMA foreign_key_list(expenses)").fetchall()
        assert columns["id"]["pk"] == 1
        assert columns["amount"]["type"].upper() == "REAL"
        assert columns["amount"]["notnull"] == 1
        assert columns["category"]["notnull"] == 1
        assert columns["date"]["notnull"] == 1
        assert columns["description"]["notnull"] == 0
        assert any(row["table"] == "users" and row["from"] == "user_id" for row in foreign_keys)


class TestSeedData:
    def test_demo_user_exists_with_hashed_password(self):
        with db.get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()
        assert user is not None
        assert user["name"] == "Demo User"
        assert user["password_hash"] != "demo123"
        assert check_password_hash(user["password_hash"], "demo123")

    def test_eight_expenses_exist(self):
        assert get_expense_count() == 9

    def test_all_categories_covered(self):
        with db.get_db() as conn:
            categories = {
                row["category"] for row in conn.execute("SELECT DISTINCT category FROM expenses").fetchall()
            }
        assert categories == EXPECTED_CATEGORIES

    def test_expenses_linked_to_demo_user(self):
        with db.get_db() as conn:
            demo_id = conn.execute(
                "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
            ).fetchone()["id"]
            user_ids = {
                row["user_id"] for row in conn.execute("SELECT user_id FROM expenses").fetchall()
            }
        assert user_ids == {demo_id}

    def test_amounts_stored_as_real(self):
        with db.get_db() as conn:
            types = conn.execute("SELECT DISTINCT typeof(amount) AS t FROM expenses").fetchall()
        assert [row["t"] for row in types] == ["real"]

    def test_dates_follow_yyyy_mm_dd(self):
        with db.get_db() as conn:
            dates = [row["date"] for row in conn.execute("SELECT date FROM expenses").fetchall()]
        assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) for d in dates)

    def test_seed_is_idempotent(self):
        db.seed_db()
        assert get_user_count() == 1
        assert get_expense_count() == 9


class TestConstraints:
    def test_duplicate_email_fails(self):
        with pytest.raises(sqlite3.IntegrityError):
            with db.get_db() as conn:
                conn.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    ("Other User", "demo@spendly.com", "hash"),
                )

    def test_invalid_user_id_fails(self):
        with pytest.raises(sqlite3.IntegrityError):
            with db.get_db() as conn:
                conn.execute(
                    "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
                    (99999, 10.0, "Food", "2026-01-01"),
                )


class TestAppStartup:
    def test_app_starts_without_errors(self):
        from app import app

        client = app.test_client()
        for path in ("/", "/login", "/register"):
            assert client.get(path).status_code == 200