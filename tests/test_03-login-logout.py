import sqlite3

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


def test_landing_redirects_after_login(client):
    response = client.post(
        "/login",
        data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


class TestLoginPage:
    def test_get_login_renders_form_fields(self, client):
        response = client.get("/login")
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert 'name="email"' in body
        assert 'name="password"' in body

    def test_get_login_has_submit_button(self, client):
        body = client.get("/login").get_data(as_text=True)
        assert 'type="submit"' in body


class TestSuccessfulLogin:
    def test_redirects_to_landing(self, client):
        response = client.post(
            "/login",
            data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        )
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")

    def test_session_contains_user_id(self, client):
        client.post(
            "/login",
            data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        )
        with client.session_transaction() as session:
            assert session["user_id"] == 1

    def test_session_persists_across_requests(self, client):
        client.post(
            "/login",
            data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        )
        landing = client.get("/")
        navbar = landing.get_data(as_text=True)
        assert "demo@spendly.com" in navbar
        assert "Log out" in navbar

    def test_navbar_shows_sign_in_when_logged_out(self, client):
        body = client.get("/").get_data(as_text=True)
        assert "Sign in" in body
        assert "Get started" in body
        assert "Log out" not in body

    def test_email_matching_is_case_insensitive(self, client):
        response = client.post(
            "/login",
            data={"email": DEMO_EMAIL.upper(), "password": DEMO_PASSWORD},
        )
        assert response.status_code == 302


class TestFailedLogin:
    def test_wrong_password_shows_generic_error(self, client):
        response = client.post(
            "/login",
            data={"email": DEMO_EMAIL, "password": "wrong-password"},
        )
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Invalid email or password" in body

    def test_unknown_email_shows_same_generic_error(self, client):
        response = client.post(
            "/login",
            data={"email": "nobody@example.com", "password": DEMO_PASSWORD},
        )
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Invalid email or password" in body

    def test_empty_fields_shows_generic_error(self, client):
        response = client.post("/login", data={"email": "", "password": ""})
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Invalid email or password" in body

    def test_failed_login_does_not_start_session(self, client):
        client.post(
            "/login",
            data={"email": DEMO_EMAIL, "password": "wrong-password"},
        )
        with client.session_transaction() as session:
            assert "user_id" not in session


class TestLogout:
    def test_post_logout_clears_session_and_redirects(self, client):
        client.post(
            "/login",
            data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        )
        response = client.post("/logout")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")
        with client.session_transaction() as session:
            assert "user_id" not in session

    def test_navbar_reverts_to_logged_out_after_logout(self, client):
        client.post(
            "/login",
            data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        )
        client.post("/logout")
        body = client.get("/").get_data(as_text=True)
        assert "Sign in" in body
        assert "Log out" not in body

    def test_get_logout_is_not_allowed(self, client):
        response = client.get("/logout")
        assert response.status_code == 405

    def test_logout_when_not_logged_in_is_harmless(self, client):
        response = client.post("/logout")
        assert response.status_code == 302


class TestStaleSession:
    def test_invalid_user_id_renders_logged_out_without_crash(self, client):
        with client.session_transaction() as session:
            session["user_id"] = 9999
        response = client.get("/")
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Sign in" in body
        assert "Log out" not in body


class TestLandingHero:
    def test_logged_out_landing_shows_hero_sign_in_button(self, client):
        body = client.get("/").get_data(as_text=True)
        assert 'class="btn-ghost">Sign in' in body

    def test_logged_in_landing_hides_hero_sign_in_button(self, client):
        client.post(
            "/login",
            data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        )
        body = client.get("/").get_data(as_text=True)
        assert 'class="btn-ghost">Sign in' not in body
        assert "My profile" in body

    def test_logged_in_landing_hides_create_account_cta(self, client):
        client.post(
            "/login",
            data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        )
        body = client.get("/").get_data(as_text=True)
        assert "Create free account" not in body