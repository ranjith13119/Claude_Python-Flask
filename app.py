import os
import sqlite3

from flask import Flask, redirect, render_template, request, url_for

from database.db import create_user, init_db, seed_db

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


@app.route("/login")
def login():
    return render_template("login.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


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
