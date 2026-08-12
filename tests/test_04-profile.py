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
    client.post("/login", data={"email": email, "password": password})


class TestAccessControl:
    def test_logged_out_redirects_to_login(self, client):
        response = client.get("/profile")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")

    def test_logged_in_returns_200(self, client):
        login(client)
        response = client.get("/profile")
        assert response.status_code == 200


class TestProfilePageContent:
    def test_page_shows_user_info_card_with_name(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert "Demo User" in body

    def test_page_shows_email(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert DEMO_EMAIL in body

    def test_page_shows_three_summary_stats(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert body.count("stat-card") >= 3
        assert "Total spent" in body
        assert "Transactions" in body
        assert "Top category" in body

    def test_page_shows_transaction_table_with_three_rows(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert body.count("profile-table") == 1
        assert body.count("<tr>") >= 4
        assert "Lunch at cafe" in body
        assert "Metro card top-up" in body
        assert "Electricity bill" in body

    def test_page_shows_category_breakdown_with_three_categories(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert "breakdown-row" in body
        for category in ("Food", "Bills", "Transport", "Other"):
            assert category in body

    def test_navbar_shows_logged_in_state(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert DEMO_EMAIL in body
        assert "Log out" in body

    def test_page_does_not_show_password_hash(self, client):
        login(client)
        body = client.get("/profile").get_data(as_text=True)
        assert "scrypt:" not in body


class TestTemplateRules:
    def test_no_hex_colors_in_template(self):
        content = PROFILE_TEMPLATE.read_text(encoding="utf-8")
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b", content)

    def test_template_extends_base(self):
        content = PROFILE_TEMPLATE.read_text(encoding="utf-8")
        assert '{% extends "base.html" %}' in content