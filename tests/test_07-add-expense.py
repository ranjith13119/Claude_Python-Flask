from datetime import date, timedelta

import pytest

from app import app
from database import db

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"
ADD_TEMPLATE = "templates/add_expense.html"
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


def expense_count():
    with db.get_db() as conn:
        return conn.execute("SELECT COUNT(*) AS count FROM expenses").fetchone()["count"]


def last_expense():
    with db.get_db() as conn:
        return conn.execute("SELECT * FROM expenses ORDER BY id DESC LIMIT 1").fetchone()


def valid_data(**overrides):
    data = {
        "amount": "320.50",
        "category": "Food",
        "date": date.today().isoformat(),
        "description": "Lunch at cafe",
    }
    data.update(overrides)
    return data


class TestAccessControl:
    def test_logged_out_get_redirects_to_login(self, client):
        response = client.get("/expenses/add")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")

    def test_logged_out_post_redirects_to_login(self, client):
        response = client.post("/expenses/add", data=valid_data())
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")


class TestAddExpensePage:
    def test_logged_in_returns_200(self, client):
        login(client)
        response = client.get("/expenses/add")
        assert response.status_code == 200

    def test_page_shows_amount_field(self, client):
        login(client)
        body = client.get("/expenses/add").get_data(as_text=True)
        assert 'name="amount"' in body

    def test_page_shows_all_eight_categories(self, client):
        login(client)
        body = client.get("/expenses/add").get_data(as_text=True)
        for category in EXPECTED_CATEGORIES:
            assert f'value="{category}"' in body

    def test_page_defaults_date_to_today(self, client):
        login(client)
        body = client.get("/expenses/add").get_data(as_text=True)
        assert f'value="{date.today().isoformat()}"' in body

    def test_page_shows_description_field(self, client):
        login(client)
        body = client.get("/expenses/add").get_data(as_text=True)
        assert 'name="description"' in body


class TestValidSubmission:
    def test_valid_submission_redirects_to_landing(self, client):
        login(client)
        response = client.post("/expenses/add", data=valid_data())
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")

    def test_valid_submission_inserts_one_row(self, client):
        login(client)
        before = expense_count()
        client.post("/expenses/add", data=valid_data())
        assert expense_count() == before + 1

    def test_inserted_row_has_correct_values(self, client):
        login(client)
        client.post("/expenses/add", data=valid_data())
        row = last_expense()
        assert row["amount"] == pytest.approx(320.50)
        assert row["category"] == "Food"
        assert row["date"] == date.today().isoformat()
        assert row["description"] == "Lunch at cafe"

    def test_inserted_row_uses_session_user(self, client):
        login(client)
        user_id = db.get_user_by_email(DEMO_EMAIL)["id"]
        client.post("/expenses/add", data=valid_data())
        assert last_expense()["user_id"] == user_id

    def test_optional_description_stored_as_null(self, client):
        login(client)
        client.post("/expenses/add", data=valid_data(description=""))
        assert last_expense()["description"] is None


class TestValidation:
    @pytest.mark.parametrize("overrides", [
        {"amount": ""},
        {"amount": "abc"},
        {"amount": "0"},
        {"amount": "-5"},
        {"category": ""},
        {"category": "Hack"},
        {"date": ""},
        {"date": "2026-02-30"},
        {"date": (date.today() + timedelta(days=1)).isoformat()},
    ])
    def test_invalid_submission_rerenders_form_without_inserting(self, client, overrides):
        login(client)
        before = expense_count()
        response = client.post("/expenses/add", data=valid_data(**overrides))
        assert response.status_code == 200
        assert "auth-error" in response.get_data(as_text=True)
        assert expense_count() == before


class TestTemplateRules:
    def test_template_extends_base(self):
        with open(ADD_TEMPLATE, encoding="utf-8") as f:
            assert '{% extends "base.html" %}' in f.read()

    def test_template_has_no_hex_colors(self):
        with open(ADD_TEMPLATE, encoding="utf-8") as f:
            assert "#" not in f.read().replace("{{ url_for('add_expense') }}", "")

    def test_template_has_no_inline_styles(self):
        with open(ADD_TEMPLATE, encoding="utf-8") as f:
            assert "style=" not in f.read()
