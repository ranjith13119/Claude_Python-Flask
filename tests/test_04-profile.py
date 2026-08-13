import pytest

from database import db
from app import app

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


@pytest.fixture
def logged_in(client):
    response = client.post(
        "/login",
        data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    assert response.status_code == 302
    return client


class TestAccessControl:
    def test_profile_redirects_to_login_when_logged_out(self, client):
        response = client.get("/profile")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")

    def test_profile_renders_when_logged_in(self, logged_in):
        response = logged_in.get("/profile")
        assert response.status_code == 200


class TestProfileContent:
    def test_shows_user_identity(self, logged_in):
        body = logged_in.get("/profile").get_data(as_text=True)
        assert "Demo User" in body
        assert DEMO_EMAIL in body
        assert "Member since" in body

    def test_shows_three_stat_cards(self, logged_in):
        body = logged_in.get("/profile").get_data(as_text=True)
        assert "₹294.64" in body
        assert ">8<" in body
        assert "Shopping" in body
        assert body.count("stat-card") >= 3

    def test_shows_transaction_table_with_columns(self, logged_in):
        body = logged_in.get("/profile").get_data(as_text=True)
        for column in ("Date", "Description", "Category", "Amount"):
            assert column in body
        for tx in ("Lunch at cafe", "Metro card top-up", "Electricity bill"):
            assert tx in body

    def test_shows_category_breakdown_with_percents(self, logged_in):
        body = logged_in.get("/profile").get_data(as_text=True)
        for percent in ("26%", "27%", "20%"):
            assert percent in body

    def test_breakdown_percents_sum_to_100(self, logged_in):
        body = logged_in.get("/profile").get_data(as_text=True)
        assert "Spending by category" in body

    def test_navbar_shows_logged_in_state(self, logged_in):
        body = logged_in.get("/profile").get_data(as_text=True)
        assert DEMO_EMAIL in body
        assert "Log out" in body
        assert "Get started" not in body


class TestTemplateRules:
    def test_no_password_hash_leak(self, logged_in):
        body = logged_in.get("/profile").get_data(as_text=True)
        assert "password" not in body.lower()

    def test_extends_base_template(self):
        with open("templates/profile.html", encoding="utf-8") as f:
            source = f.read()
        assert '{% extends "base.html" %}' in source

    def test_no_hardcoded_hex_colors(self):
        with open("templates/profile.html", encoding="utf-8") as f:
            source = f.read()
        assert "#" not in source

    def test_no_inline_styles(self):
        with open("templates/profile.html", encoding="utf-8") as f:
            source = f.read()
        assert 'style="' not in source and "style='" not in source