from datetime import date, timedelta

import pytest

from app import app
from database import db

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"
EDIT_TEMPLATE = "templates/edit_expense.html"
EXPECTED_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other", "Investment"]


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


def expense_row(expense_id):
    with db.get_db() as conn:
        return conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()


def other_user_expense_id():
    user_id = db.create_user("Other User", "other@test.com", "password123")
    return db.create_expense(user_id, 5.00, "Food", date.today().isoformat(), "Other user's expense")


def valid_data(**overrides):
    data = {
        "amount": "25.00",
        "category": "Transport",
        "date": date.today().isoformat(),
        "description": "Updated metro top-up",
    }
    data.update(overrides)
    return data


class TestAccessControl:
    def test_logged_out_get_redirects_to_login(self, client):
        response = client.get("/expenses/1/edit")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")

    def test_logged_out_post_redirects_to_login(self, client):
        response = client.post("/expenses/1/edit", data=valid_data())
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")


class TestOwnership:
    def test_missing_expense_returns_404(self, client):
        login(client)
        assert client.get("/expenses/9999/edit").status_code == 404

    def test_other_users_expense_returns_404(self, client):
        login(client)
        other_id = other_user_expense_id()
        assert client.get(f"/expenses/{other_id}/edit").status_code == 404


class TestEditPage:
    def test_logged_in_returns_200(self, client):
        login(client)
        response = client.get("/expenses/1/edit")
        assert response.status_code == 200

    def test_form_is_prefilled_with_expense_values(self, client):
        login(client)
        body = client.get("/expenses/1/edit").get_data(as_text=True)
        assert 'value="14.50"' in body
        assert "Lunch at cafe" in body
        assert f'value="{date.today().isoformat()}"' in body

    def test_current_category_is_selected(self, client):
        login(client)
        body = client.get("/expenses/1/edit").get_data(as_text=True)
        assert '<option value="Food" selected>' in body

    def test_all_eight_categories_present(self, client):
        login(client)
        body = client.get("/expenses/1/edit").get_data(as_text=True)
        for category in EXPECTED_CATEGORIES:
            assert f'value="{category}"' in body


class TestValidUpdate:
    def test_valid_update_redirects_to_profile(self, client):
        login(client)
        response = client.post("/expenses/1/edit", data=valid_data())
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/profile")

    def test_valid_update_changes_row(self, client):
        login(client)
        client.post("/expenses/1/edit", data=valid_data())
        row = expense_row(1)
        assert row["amount"] == pytest.approx(25.00)
        assert row["category"] == "Transport"
        assert row["date"] == date.today().isoformat()
        assert row["description"] == "Updated metro top-up"

    def test_cleared_description_stored_as_null(self, client):
        login(client)
        client.post("/expenses/1/edit", data=valid_data(description=""))
        assert expense_row(1)["description"] is None


class TestInvalidUpdate:
    @pytest.mark.parametrize("overrides", [
        {"amount": ""},
        {"amount": "abc"},
        {"amount": "0"},
        {"amount": "-5"},
        {"amount": "nan"},
        {"amount": "inf"},
        {"category": "Hack"},
        {"date": ""},
        {"date": "2026-02-30"},
        {"date": (date.today() + timedelta(days=1)).isoformat()},
    ])
    def test_invalid_update_rerenders_with_error_and_no_change(self, client, overrides):
        login(client)
        before = expense_row(1)
        response = client.post("/expenses/1/edit", data=valid_data(**overrides))
        assert response.status_code == 200
        assert "auth-error" in response.get_data(as_text=True)
        after = expense_row(1)
        assert after["amount"] == before["amount"]
        assert after["category"] == before["category"]
        assert after["date"] == before["date"]
        assert after["description"] == before["description"]


class TestTemplateRules:
    def test_template_extends_base(self):
        with open(EDIT_TEMPLATE, encoding="utf-8") as f:
            assert '{% extends "base.html" %}' in f.read()

    def test_template_has_no_hex_colors(self):
        with open(EDIT_TEMPLATE, encoding="utf-8") as f:
            assert "#" not in f.read()

    def test_template_has_no_inline_styles(self):
        with open(EDIT_TEMPLATE, encoding="utf-8") as f:
            assert "style=" not in f.read()