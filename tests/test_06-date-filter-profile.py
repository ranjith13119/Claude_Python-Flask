from datetime import date, timedelta

import pytest

from database import db
from app import app

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"

TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
SEVEN_DAYS_AGO = (date.today() - timedelta(days=7)).isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()


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


class TestFilterFormRendering:
    def test_profile_shows_filter_form_when_logged_in(self, logged_in):
        body = logged_in.get("/profile").get_data(as_text=True)
        assert 'method="GET"' in body
        assert 'name="from_date"' in body
        assert 'name="to_date"' in body
        assert "Filter" in body
        assert "Reset" in body

    def test_form_submits_to_profile_route(self, logged_in):
        body = logged_in.get("/profile").get_data(as_text=True)
        assert 'action="/profile"' in body

    def test_inputs_empty_on_first_visit(self, logged_in):
        body = logged_in.get("/profile").get_data(as_text=True)
        assert 'name="from_date" value=""' in body
        assert 'name="to_date" value=""' in body


class TestFilterBehavior:
    def test_from_date_only(self, logged_in):
        body = logged_in.get(f"/profile?from_date={TODAY}").get_data(as_text=True)
        assert "Lunch at cafe" in body
        assert "Groceries for the week" not in body

    def test_to_date_only(self, logged_in):
        body = logged_in.get(f"/profile?to_date={SEVEN_DAYS_AGO}").get_data(as_text=True)
        assert "Miscellaneous" in body
        assert "Lunch at cafe" not in body

    def test_both_dates_inclusive(self, logged_in):
        body = logged_in.get(
            f"/profile?from_date={SEVEN_DAYS_AGO}&to_date={TODAY}"
        ).get_data(as_text=True)
        assert "Lunch at cafe" in body
        assert "Miscellaneous" in body

    def test_filter_matches_boundary_dates(self, logged_in):
        body = logged_in.get(f"/profile?from_date={YESTERDAY}&to_date={YESTERDAY}").get_data(
            as_text=True
        )
        assert "Groceries for the week" in body
        assert "Lunch at cafe" not in body
        assert "Metro card top-up" not in body


class TestEmptyState:
    def test_no_matching_transactions_shows_message(self, logged_in):
        body = logged_in.get(f"/profile?from_date={TOMORROW}").get_data(as_text=True)
        assert "No transactions in this date range." in body


class TestInvalidDates:
    def test_malformed_from_date_ignored(self, logged_in):
        response = logged_in.get("/profile?from_date=abc")
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "Lunch at cafe" in body

    def test_out_of_range_date_ignored(self, logged_in):
        response = logged_in.get("/profile?from_date=2026-02-30")
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "Lunch at cafe" in body

    def test_invalid_date_clears_input(self, logged_in):
        body = logged_in.get("/profile?from_date=abc").get_data(as_text=True)
        assert 'name="from_date" value=""' in body


class TestFormPersistence:
    def test_inputs_prefilled_after_filter(self, logged_in):
        body = logged_in.get(f"/profile?from_date={TODAY}").get_data(as_text=True)
        assert f'name="from_date" value="{TODAY}"' in body

    def test_reset_link_clears_params(self, logged_in):
        body = logged_in.get(f"/profile?from_date={TODAY}").get_data(as_text=True)
        assert 'href="/profile"' in body


class TestAccessAndRules:
    def test_logged_out_still_redirects_to_login(self, client):
        response = client.get("/profile?from_date=2026-01-01")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")

    def test_stats_unaffected_by_filter(self, logged_in):
        body = logged_in.get(f"/profile?from_date={TODAY}").get_data(as_text=True)
        assert "₹294.64" in body
        assert "8" in body

    def test_no_hex_colors_in_template(self):
        with open("templates/profile.html", encoding="utf-8") as f:
            source = f.read()
        assert "#" not in source

    def test_template_extends_base(self):
        with open("templates/profile.html", encoding="utf-8") as f:
            source = f.read()
        assert '{% extends "base.html" %}' in source

    def test_no_inline_styles(self):
        with open("templates/profile.html", encoding="utf-8") as f:
            source = f.read()
        assert 'style="' not in source and "style='" not in source