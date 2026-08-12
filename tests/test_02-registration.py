import sqlite3

import pytest
from werkzeug.security import check_password_hash

from database import db
from app import app


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


def fetch_user(email=None):
    with sqlite3.connect(str(db.DB_PATH)) as conn:
        if email is None:
            return conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()[0]
        return conn.execute(
            "SELECT name, email, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()


class TestRegistrationPage:
    def test_get_register_renders_form_fields(self, client):
        response = client.get("/register")
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert 'name="name"' in body
        assert 'name="email"' in body
        assert 'name="password"' in body

    def test_get_register_has_submit_button(self, client):
        body = client.get("/register").get_data(as_text=True)
        assert 'type="submit"' in body


class TestSuccessfulRegistration:
    def test_valid_submission_redirects_to_login(self, client):
        response = client.post(
            "/register",
            data={"name": "Nitish Kumar", "email": "nitish@example.com", "password": "password123"},
        )
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")

    def test_valid_submission_creates_user_row(self, client):
        client.post(
            "/register",
            data={"name": "Nitish Kumar", "email": "nitish@example.com", "password": "password123"},
        )
        user = fetch_user("nitish@example.com")
        assert user is not None
        assert user[0] == "Nitish Kumar"

    def test_password_stored_hashed_not_plaintext(self, client):
        client.post(
            "/register",
            data={"name": "Nitish Kumar", "email": "nitish@example.com", "password": "password123"},
        )
        user = fetch_user("nitish@example.com")
        assert user[2] != "password123"
        assert check_password_hash(user[2], "password123")

    def test_email_normalized_to_lowercase(self, client):
        client.post(
            "/register",
            data={"name": "Nitish Kumar", "email": "Nitish@Example.COM", "password": "password123"},
        )
        user = fetch_user("nitish@example.com")
        assert user is not None

    def test_seed_data_not_duplicated(self, client):
        client.post(
            "/register",
            data={"name": "Nitish Kumar", "email": "nitish@example.com", "password": "password123"},
        )
        assert fetch_user() == 2


class TestValidationErrors:
    def test_duplicate_email_shows_friendly_error(self, client):
        client.post(
            "/register",
            data={"name": "Nitish Kumar", "email": "nitish@example.com", "password": "password123"},
        )
        response = client.post(
            "/register",
            data={"name": "Nitish Kumar", "email": "nitish@example.com", "password": "password123"},
        )
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "already exists" in body

    def test_duplicate_email_with_different_case_also_rejected(self, client):
        client.post(
            "/register",
            data={"name": "Nitish Kumar", "email": "nitish@example.com", "password": "password123"},
        )
        response = client.post(
            "/register",
            data={"name": "Nitish Kumar", "email": "NITISH@example.com", "password": "password123"},
        )
        assert "already exists" in response.get_data(as_text=True)

    def test_short_password_shows_friendly_error(self, client):
        response = client.post(
            "/register",
            data={"name": "Nitish Kumar", "email": "nitish@example.com", "password": "short"},
        )
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "at least 8 characters" in body
        assert fetch_user("nitish@example.com") is None

    def test_empty_fields_shows_friendly_error(self, client):
        response = client.post("/register", data={"name": "", "email": "", "password": ""})
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "required" in body
        assert fetch_user() == 1

    def test_whitespace_only_fields_are_rejected(self, client):
        response = client.post(
            "/register",
            data={"name": "   ", "email": "   ", "password": "        "},
        )
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "required" in body
        assert fetch_user() == 1