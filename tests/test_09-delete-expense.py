from datetime import date

import pytest

from app import app
from database import db

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    db.seed_db()
    yield tmp_path / "test.db"


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def login(client, email=DEMO_EMAIL, password=DEMO_PASSWORD):
    client.post("/login", data={"email": email, "password": password})


def expense_count():
    with db.get_db() as conn:
        return conn.execute("SELECT COUNT(*) AS count FROM expenses").fetchone()["count"]


def other_user_expense_id():
    user_id = db.create_user("Other User", "other@test.com", "password123")
    return db.create_expense(user_id, 5.00, "Food", date.today().isoformat(), "Other user's expense")


class TestMethodRestriction:
    def test_get_returns_405(self, client):
        login(client)
        assert client.get("/expenses/1/delete").status_code == 405

    def test_logged_out_post_redirects_to_login(self, client):
        response = client.post("/expenses/1/delete")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")


class TestOwnership:
    def test_missing_expense_returns_404_and_nothing_deleted(self, client):
        login(client)
        before = expense_count()
        response = client.post("/expenses/9999/delete")
        assert response.status_code == 404
        assert expense_count() == before

    def test_other_users_expense_returns_404_and_nothing_deleted(self, client):
        login(client)
        other_id = other_user_expense_id()
        before = expense_count()
        response = client.post(f"/expenses/{other_id}/delete")
        assert response.status_code == 404
        assert expense_count() == before


class TestDelete:
    def test_owner_delete_removes_row_and_redirects_to_profile(self, client):
        login(client)
        before = expense_count()
        response = client.post("/expenses/1/delete")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/profile")
        assert expense_count() == before - 1

    def test_deleted_row_is_gone_from_db(self, client):
        login(client)
        client.post("/expenses/1/delete")
        with db.get_db() as conn:
            assert conn.execute("SELECT * FROM expenses WHERE id = 1").fetchone() is None

    def test_deleting_all_expenses_still_renders_profile(self, client):
        login(client)
        with db.get_db() as conn:
            ids = [row["id"] for row in conn.execute("SELECT id FROM expenses").fetchall()]
        for expense_id in ids:
            client.post(f"/expenses/{expense_id}/delete")
        response = client.get("/profile")
        assert response.status_code == 200
        assert "No transactions yet." in response.get_data(as_text=True)


class TestProfileButtons:
    def test_profile_shows_delete_button_per_row(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert body.count("/delete") >= 8
        assert "btn-danger-sm" in body

    def test_profile_shows_edit_link_per_row(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert "/edit" in body