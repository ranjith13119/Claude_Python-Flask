import re
from pathlib import Path

import pytest

from database import db
from app import app

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"
PROFILE_TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "profile.html"


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
    response = client.post("/login", data={"email": email, "password": password})
    assert response.status_code == 302


class TestAccessControl:
    def test_logged_out_redirects_to_login(self, client):
        response = client.get("/profile")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")

    def test_logged_in_returns_200(self, client):
        login(client)
        response = client.get("/profile")
        assert response.status_code == 200

    def test_stale_session_redirects_to_login(self, client):
        with client.session_transaction() as sess:
            sess["user_id"] = 999999
        response = client.get("/profile")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")


class TestLiveData:
    def test_shows_real_user_name_and_email(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert "Demo User" in body
        assert DEMO_EMAIL in body

    def test_stats_computed_from_expenses(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert "₹294.64" in body
        assert "8" in body
        assert "Shopping" in body

    def test_transaction_table_shows_seeded_expenses(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        for description in ("Lunch at cafe", "Groceries for the week", "Electricity bill"):
            assert description in body

    def test_transactions_ordered_by_date_descending(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert body.index("Lunch at cafe") < body.index("Groceries for the week")
        assert body.index("Groceries for the week") < body.index("Metro card top-up")

    def test_amounts_rupee_formatted(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert "₹14.50" in body
        assert "₹79.99" in body

    def test_category_breakdown_with_computed_percents(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        for category in ("Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"):
            assert category in body
        assert "pct-26" in body
        assert "pct-27" in body

    def test_member_since_derived_from_created_at(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert re.search(r"Member since \w+ 2026", body)


class TestEmptyState:
    def test_user_with_no_expenses_renders_without_crash(self, client):
        db.create_user("Empty User", "empty@spendly.com", "password123")
        login(client, email="empty@spendly.com", password="password123")
        response = client.get("/profile")
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "₹0.00" in body
        assert ">0<" in body
        assert ">-<" in body


class TestTemplateRules:
    def test_no_password_hash_leak(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert "password" not in body.lower()
        assert "scrypt:" not in body

    def test_no_hex_colors_in_template(self):
        content = PROFILE_TEMPLATE.read_text(encoding="utf-8")
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b", content)

    def test_template_extends_base(self):
        content = PROFILE_TEMPLATE.read_text(encoding="utf-8")
        assert '{% extends "base.html" %}' in content

    def test_no_inline_styles(self):
        content = PROFILE_TEMPLATE.read_text(encoding="utf-8")
        assert 'style="' not in content and "style='" not in content