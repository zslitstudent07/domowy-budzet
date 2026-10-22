
import os
from datetime import date
from decimal import Decimal, InvalidOperation

import mysql.connector
from flask import Flask, flash, redirect, render_template, request, url_for
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "user": os.getenv("DB_USER", "finasee"),
    "password": os.getenv("DB_PASSWORD", "finasee"),
    "database": os.getenv("DB_NAME", "finasee"),
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def calculate_total(amounts):
    """Oblicza sumę kwot bez błędów zaokrągleń typowych dla float."""
    return sum((Decimal(str(amount)) for amount in amounts), Decimal("0.00"))


def init_db():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                amount DECIMAL(10, 2) NOT NULL,
                expense_date DATE NOT NULL,
                category VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        cursor.close()
    finally:
        connection.close()


@app.route("/", methods=["GET", "POST"])
def index():
    try:
        if request.method == "POST":
            amount = Decimal(request.form.get("amount", ""))
            expense_date = date.fromisoformat(
                request.form.get("expense_date", "")
            )
            category = request.form.get("category", "").strip()

            if not amount.is_finite() or amount <= 0:
                raise ValueError("Kwota musi być większa od zera.")
            if amount.as_tuple().exponent < -2:
                raise ValueError("Kwota może mieć maksymalnie 2 miejsca po przecinku.")
            if amount > Decimal("99999999.99"):
                raise ValueError("Kwota przekracza dopuszczalny limit.")
            if not category or len(category) > 100:
                raise ValueError("Podaj kategorię o długości 1–100 znaków.")
            if expense_date > date.today():
                raise ValueError("Data wydatku nie może być z przyszłości.")

            connection = get_connection()
            try:
                cursor = connection.cursor()
                cursor.execute(
                    """INSERT INTO expenses
                       (amount, expense_date, category)
                       VALUES (%s, %s, %s)""",
                    (amount, expense_date, category),
                )
                connection.commit()
                cursor.close()
            finally:
                connection.close()

            flash("Wydatek został zapisany.", "success")
            return redirect(url_for("index"))

        connection = get_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, amount, expense_date, category
                FROM expenses
                ORDER BY expense_date DESC, id DESC
            """)
            expenses = cursor.fetchall()
            cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses")
            total = cursor.fetchone()["total"]
            cursor.close()
        finally:
            connection.close()

        return render_template(
            "index.html",
            expenses=expenses,
            total=total,
            today=date.today().isoformat(),
        )

    except (InvalidOperation, ValueError, TypeError) as error:
        flash(f"Nieprawidłowe dane: {error}", "danger")
        return redirect(url_for("index"))
    except Error:
        app.logger.exception("Błąd połączenia z bazą danych")
        return "Baza danych jest chwilowo niedostępna.", 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
