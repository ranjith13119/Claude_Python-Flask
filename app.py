import math
import os
import re
import sqlite3
from datetime import date, datetime

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database.db import (
    CATEGORIES,
    create_expense,
    create_user,
    delete_expense,
    get_earnings_by_user_id,
    get_expense_by_id,
    get_expenses_by_user_id,
    get_user_by_email,
    get_user_by_id,
    init_db,
    seed_db,
    update_expense,
    upsert_earnings,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SPENDLY_SECRET_KEY", "dev-secret-key")


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def valid_date(value):
    try:
        if value:
            datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def format_rupee(amount):
    return f"₹{amount:,.2f}"


def build_category_breakdown(expenses):
    totals = {}
    for expense in expenses:
        totals[expense["category"]] = totals.get(expense["category"], 0.0) + expense["amount"]

    grand_total = sum(totals.values())
    if grand_total <= 0:
        return []

    breakdown = []
    for category in CATEGORIES:
        if category not in totals:
            continue
        breakdown.append(
            {
                "category": category,
                "total": format_rupee(totals[category]),
                "percent": round(totals[category] / grand_total * 100),
            }
        )
    return breakdown


def validate_expense_input(amount_raw, category, date_raw):
    error = None
    try:
        amount = float(amount_raw)
        if not math.isfinite(amount):
            error = "Amount must be a valid number"
        elif amount <= 0:
            error = "Amount must be greater than zero"
    except ValueError:
        error = "Amount must be a valid number"

    if error is None and category not in CATEGORIES:
        error = "Please choose a valid category"

    if error is None:
        try:
            expense_date = date.fromisoformat(date_raw)
            if expense_date > date.today():
                error = "Date cannot be in the future"
        except ValueError:
            error = "Date must be a valid date (YYYY-MM-DD)"

    return amount if error is None else None, error


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


def build_monthly_comparison(expenses, earnings_rows):
    spent_by_month = {}
    for expense in expenses:
        month = expense["date"][:7]
        spent_by_month[month] = spent_by_month.get(month, 0.0) + expense["amount"]

    earnings_by_month = {row["month"]: row["amount"] for row in earnings_rows}
    months = sorted(set(spent_by_month) | set(earnings_by_month), reverse=True)

    comparison = []
    for month in months:
        earnings_amount = earnings_by_month.get(month)
        spent = spent_by_month.get(month)
        comparison.append(
            {
                "month": month,
                "earnings": earnings_amount,
                "spent": spent,
                "net": earnings_amount - spent if earnings_amount is not None and spent is not None else None,
            }
        )
    return comparison


def render_profile(error=None):
    if session.get("user_id") is None:
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])
    if user is None:
        return redirect(url_for("login"))

    expenses = get_expenses_by_user_id(user["id"])

    total_spent = sum(expense["amount"] for expense in expenses)
    transaction_count = len(expenses)

    category_totals = {}
    for expense in expenses:
        category_totals[expense["category"]] = (
            category_totals.get(expense["category"], 0.0) + expense["amount"]
        )
    top_category = max(category_totals, key=category_totals.get) if category_totals else "-"

    transactions = [
        {
            "id": expense["id"],
            "date": expense["date"],
            "description": expense["description"] or "",
            "category": expense["category"],
            "amount": format_rupee(expense["amount"]),
        }
        for expense in expenses
    ]

    from_date = request.args.get("from_date", "")
    to_date = request.args.get("to_date", "")

    if not valid_date(from_date):
        from_date = ""
    if not valid_date(to_date):
        to_date = ""

    filtered_transactions = [
        tx
        for tx in transactions
        if (not from_date or tx["date"] >= from_date)
        and (not to_date or tx["date"] <= to_date)
    ]

    member_since = user["created_at"][:7]
    if len(member_since) == 7:
        try:
            member_since = datetime.strptime(member_since, "%Y-%m").strftime("%B %Y")
        except ValueError:
            pass

    return render_template(
        "profile.html",
        name=user["name"],
        email=user["email"],
        member_since=member_since,
        stats={
            "total_spent": format_rupee(total_spent),
            "transaction_count": transaction_count,
            "top_category": top_category,
        },
        transactions=filtered_transactions,
        from_date=from_date,
        to_date=to_date,
        category_breakdown=build_category_breakdown(expenses),
        monthly_comparison=build_monthly_comparison(expenses, get_earnings_by_user_id(user["id"])),
        current_month=date.today().strftime("%Y-%m"),
        earnings_error=error,
    )


@app.route("/profile")
def profile():
    return render_profile()


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if session.get("user_id") is None:
        return redirect(url_for("login"))

    if request.method == "POST":
        amount_raw = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date_raw = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip() or None

        amount, error = validate_expense_input(amount_raw, category, date_raw)

        if error is not None:
            return render_template(
                "add_expense.html", error=error, categories=CATEGORIES, today=date.today().isoformat()
            )

        create_expense(session["user_id"], amount, category, date_raw, description)
        return redirect(url_for("landing"))

    return render_template(
        "add_expense.html", categories=CATEGORIES, today=date.today().isoformat()
    )


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if session.get("user_id") is None:
        return redirect(url_for("login"))

    expense = get_expense_by_id(id)
    if expense is None or expense["user_id"] != session["user_id"]:
        return "Expense not found", 404

    if request.method == "POST":
        amount_raw = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date_raw = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip() or None

        amount, error = validate_expense_input(amount_raw, category, date_raw)

        if error is not None:
            return render_template(
                "edit_expense.html", expense=expense, error=error, categories=CATEGORIES
            )

        update_expense(id, amount, category, date_raw, description)
        return redirect(url_for("profile"))

    return render_template("edit_expense.html", expense=expense, categories=CATEGORIES)


@app.route("/expenses/<int:id>/delete", methods=["POST"])
def delete_expense_route(id):
    if session.get("user_id") is None:
        return redirect(url_for("login"))

    expense = get_expense_by_id(id)
    if expense is None or expense["user_id"] != session["user_id"]:
        return "Expense not found", 404

    delete_expense(id)
    return redirect(url_for("profile"))


@app.route("/earnings", methods=["POST"])
def earnings():
    if session.get("user_id") is None:
        return redirect(url_for("login"))

    month = request.form.get("month", "").strip()
    amount_raw = request.form.get("amount", "").strip()

    error = None
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        error = "Month must be a valid month (YYYY-MM)"
    else:
        try:
            date.fromisoformat(month + "-01")
        except ValueError:
            error = "Month must be a valid month (YYYY-MM)"

    if error is None:
        try:
            amount = float(amount_raw)
            if not math.isfinite(amount):
                error = "Amount must be a valid number"
            elif amount <= 0:
                error = "Amount must be greater than zero"
        except ValueError:
            error = "Amount must be a valid number"

    if error is not None:
        return render_profile(error=error)

    upsert_earnings(session["user_id"], month, amount)
    return redirect(url_for("profile"))


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
