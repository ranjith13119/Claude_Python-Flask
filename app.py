import os
import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database.db import create_user, get_user_by_email, get_user_by_id, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SPENDLY_SECRET_KEY", "dev-secret-key")


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required")
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters")

        try:
            create_user(name, email, password)
        except sqlite3.IntegrityError:
            return render_template("register.html", error="An account with this email already exists")

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password")

        session["user_id"] = user["id"]
        return redirect(url_for("landing"))

    return render_template("login.html")


@app.context_processor
def inject_current_user():
    user = None
    user_id = session.get("user_id")
    if user_id is not None:
        user = get_user_by_id(user_id)
    return {"current_user": user}


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if session.get("user_id") is None:
        return redirect(url_for("login"))

    return render_template(
        "profile.html",
        name="Demo User",
        email="demo@spendly.com",
        member_since="March 2026",
        stats={
            "total_spent": "₹12,450",
            "transaction_count": 24,
            "top_category": "Food",
        },
        transactions=[
            {"date": "2026-03-14", "description": "Lunch at cafe", "category": "Food", "amount": "₹320"},
            {"date": "2026-03-12", "description": "Metro card top-up", "category": "Transport", "amount": "₹500"},
            {"date": "2026-03-10", "description": "Electricity bill", "category": "Bills", "amount": "₹2,400"},
        ],
        category_breakdown=[
            {"category": "Food", "total": "₹4,520", "percent": 38},
            {"category": "Bills", "total": "₹3,100", "percent": 25},
            {"category": "Transport", "total": "₹1,800", "percent": 14},
            {"category": "Other", "total": "₹3,030", "percent": 23},
        ],
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
