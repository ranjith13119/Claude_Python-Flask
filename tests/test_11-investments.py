from datetime import date, timedelta

import pytest

from app import app
from database import db

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"
PROFILE_TEMPLATE = "templates/profile.html"
EXPECTED_TYPES = ["MF", "Stocks", "Gold", "Bonds", "Crypto", "Real Estate", "Other"]
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


def investment_rows():
    with db.get_db() as conn:
        return conn.execute("SELECT * FROM investments").fetchall()


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
    data = {
        "type": "MF",
        "amount": "1000.00",
        "date": date.today().isoformat(),
        "note": "HDFC Midcap",
    }
    data.update(overrides)
    return data


class TestAccessControl:
    def test_logged_out_post_redirects_to_login(self, client):
        response = client.post("/investments", data=valid_data())
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")


class TestSaveInvestment:
    def test_valid_save_inserts_row(self, client):
        login(client)
        user_id = db.get_user_by_email(DEMO_EMAIL)["id"]
        response = client.post("/investments", data=valid_data())
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/profile")
        rows = investment_rows()
        assert len(rows) == 1
        assert rows[0]["user_id"] == user_id
        assert rows[0]["type"] == "MF"
        assert rows[0]["amount"] == pytest.approx(1000.00)
        assert rows[0]["date"] == date.today().isoformat()
        assert rows[0]["note"] == "HDFC Midcap"

    def test_empty_note_stored_as_null(self, client):
        login(client)
        client.post("/investments", data=valid_data(note=""))
        assert investment_rows()[0]["note"] is None

    def test_each_type_can_be_saved(self, client):
        login(client)
        for type in EXPECTED_TYPES:
            response = client.post("/investments", data=valid_data(type=type, amount="100.00"))
            assert response.status_code == 302
        assert len(investment_rows()) == 7

    @pytest.mark.parametrize("overrides", [
        {"type": ""},
        {"type": "Hack"},
        {"amount": ""},
        {"amount": "abc"},
        {"amount": "0"},
        {"amount": "-5"},
        {"amount": "nan"},
        {"amount": "inf"},
        {"date": ""},
        {"date": "2026-02-30"},
        {"date": (date.today() + timedelta(days=1)).isoformat()},
    ])
    def test_invalid_input_rerenders_with_error_and_no_row(self, client, overrides):
        login(client)
        response = client.post("/investments", data=valid_data(**overrides))
        assert response.status_code == 200
        assert "auth-error" in response.get_data(as_text=True)
        assert len(investment_rows()) == 0


class TestProfileInvestments:
    def test_form_renders_with_all_seven_types(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert "Investments" in body
        for type in EXPECTED_TYPES:
            assert f'value="{type}"' in body

    def test_total_invested_stat_starts_at_zero(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert "Total invested" in body
        assert "₹0.00" in body

    def test_total_invested_stat_updates_after_save(self, client):
        login(client)
        client.post("/investments", data=valid_data(amount="2500.00"))
        body = client.get("/profile").get_data(as_text=True)
        assert "₹2,500.00" in body

    def test_investment_list_shows_row(self, client):
        login(client)
        client.post("/investments", data=valid_data(type="Gold", amount="1500.00", note="SBI Gold"))
        body = client.get("/profile").get_data(as_text=True)
        assert "Gold" in body
        assert "₹1,500.00" in body
        assert "SBI Gold" in body

    def test_by_type_breakdown_shows_percent(self, client):
        login(client)
        client.post("/investments", data=valid_data(type="MF", amount="7500.00"))
        client.post("/investments", data=valid_data(type="Stocks", amount="2500.00"))
        body = client.get("/profile").get_data(as_text=True)
        assert "Investments by type" in body
        assert "75%" in body
        assert "₹7,500.00" in body

    def test_empty_state_when_nothing_recorded(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert "No investments yet." in body


class TestComparisonWithInvestments:
    def test_invested_column_shows_monthly_invested_amount(self, client):
        login(client)
        client.post("/investments", data=valid_data(amount="1000.00"))
        body = client.get("/profile").get_data(as_text=True)
        assert "Invested" in body
        assert "₹1,000.00" in body

    def test_net_is_still_earnings_minus_spent(self, client):
        login(client)
        client.post("/earnings", data={"month": CURRENT_MONTH, "amount": "5000.00"})
        client.post("/investments", data=valid_data(amount="1000.00"))
        body = client.get("/profile").get_data(as_text=True)
        spent = month_spent(CURRENT_MONTH)
        assert f"₹{5000.00 - spent:,.2f}" in body

    def test_month_with_investment_only_is_listed(self, client):
        login(client)
        client.post("/investments", data=valid_data(date="2020-01-15", amount="2000.00"))
        body = client.get("/profile").get_data(as_text=True)
        assert "2020-01" in body
        assert "₹2,000.00" in body


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