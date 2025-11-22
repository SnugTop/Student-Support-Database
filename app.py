from flask import Flask, render_template
import sqlite3
from pathlib import Path

app = Flask(__name__)

DATABASE = "student_support_center.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    conn = get_db_connection()
    try:
        cur = conn.execute("SELECT COUNT(*) AS student_count FROM Student;")
        row = cur.fetchone()
        student_count = row["student_count"] if row else 0
    except sqlite3.OperationalError:
        # Tables not created yet
        student_count = None
    finally:
        conn.close()

    return render_template("index.html", student_count=student_count)


if __name__ == "__main__":
    app.run(debug=True)
