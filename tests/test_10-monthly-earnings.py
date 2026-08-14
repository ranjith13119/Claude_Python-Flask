from datetime import date

import pytest

from app import app
from database import db

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"
PROFILE_TEMPLATE = "templates/profile.html"
CURRENT_MONTH = date.today().strftime("%Y-%m")


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


def earnings_rows():
    with db.get_db() as conn:
        return conn.execute("SELECT * FROM earnings").fetchall()


def month_spent(month):
    user_id = db.get_user_by_email(DEMO_EMAIL)["id"]
    with db.get_db() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses "
            "WHERE user_id = ? AND substr(date, 1, 7) = ?",
            (user_id, month),
        ).fetchone()
    return row["total"]


def valid_data(**overrides):
    data = {"month": CURRENT_MONTH, "amount": "5000.00"}
    data.update(overrides)
    return data


class TestAccessControl:
    def test_logged_out_post_redirects_to_login(self, client):
        response = client.post("/earnings", data=valid_data())
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")


class TestSaveEarnings:
    def test_valid_save_inserts_row(self, client):
        login(client)
        user_id = db.get_user_by_email(DEMO_EMAIL)["id"]
        response = client.post("/earnings", data=valid_data())
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/profile")
        rows = earnings_rows()
        assert len(rows) == 1
        assert rows[0]["user_id"] == user_id
        assert rows[0]["month"] == CURRENT_MONTH
        assert rows[0]["amount"] == pytest.approx(5000.00)

    def test_same_month_overwrites_instead_of_duplicating(self, client):
        login(client)
        client.post("/earnings", data=valid_data(amount="5000.00"))
        client.post("/earnings", data=valid_data(amount="6000.00"))
        rows = earnings_rows()
        assert len(rows) == 1
        assert rows[0]["amount"] == pytest.approx(6000.00)

    @pytest.mark.parametrize("overrides", [
        {"month": ""},
        {"month": "abc"},
        {"month": "2026-1"},
        {"month": "2026-13"},
        {"amount": ""},
        {"amount": "abc"},
        {"amount": "0"},
        {"amount": "-5"},
        {"amount": "nan"},
        {"amount": "inf"},
    ])
    def test_invalid_input_rerenders_with_error_and_no_row(self, client, overrides):
        login(client)
        response = client.post("/earnings", data=valid_data(**overrides))
        assert response.status_code == 200
        assert "auth-error" in response.get_data(as_text=True)
        assert len(earnings_rows()) == 0


class TestProfileComparison:
    def test_profile_shows_earnings_form_with_current_month(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert "Monthly earnings" in body
        assert f'value="{CURRENT_MONTH}"' in body

    def test_comparison_shows_earnings_spent_and_net(self, client):
        login(client)
        client.post("/earnings", data=valid_data(amount="5000.00"))
        body = client.get("/profile").get_data(as_text=True)
        spent = month_spent(CURRENT_MONTH)
        assert "₹5,000.00" in body
        assert f"₹{spent:,.2f}" in body
        assert f"₹{5000.00 - spent:,.2f}" in body
        assert "net-positive" in body

    def test_month_with_earnings_only_is_listed(self, client):
        login(client)
        client.post("/earnings", data=valid_data(month="2020-01", amount="1000.00"))
        body = client.get("/profile").get_data(as_text=True)
        assert "2020-01" in body
        assert "₹1,000.00" in body

    def test_seed_expenses_show_in_comparison_without_earnings(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        spent = month_spent(CURRENT_MONTH)
        assert f"₹{spent:,.2f}" in body

    def test_empty_state_when_nothing_recorded(self, client):
        login(client)
        with db.get_db() as conn:
            conn.execute("DELETE FROM expenses")
        body = client.get("/profile").get_data(as_text=True)
        assert "No earnings or expenses recorded yet." in body


class TestAddExpenseEntryPoints:
    def test_navbar_has_add_expense_link(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert 'href="/expenses/add"' in body

    def test_profile_has_add_expense_button(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert "Add expense" in body


class TestTemplateRules:
    def test_template_extends_base(self):
        with open(PROFILE_TEMPLATE, encoding="utf-8") as f:
            assert '{% extends "base.html" %}' in f.read()

    def test_template_has_no_hex_colors(self):
        with open(PROFILE_TEMPLATE, encoding="utf-8") as f:
            assert "#" not in f.read()

    def test_template_has_no_inline_styles(self):
        with open(PROFILE_TEMPLATE, encoding="utf-8") as f:
            assert "style=" not in f.read()