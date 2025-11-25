from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DATABASE = "student_support_center.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # access columns by name
    return conn


@app.route("/")
def home():
    conn = get_db_connection()
    try:
        student_count = conn.execute(
            "SELECT COUNT(*) AS c FROM Student"
        ).fetchone()["c"]
    except sqlite3.OperationalError:
        student_count = None
    finally:
        conn.close()

    return render_template("index.html", student_count=student_count)


# ---------- STUDENTS ----------

@app.route("/students")
def list_students():
    search = request.args.get("search", "")

    conn = get_db_connection()
    if search:
        students = conn.execute(
            "SELECT * FROM Student WHERE name LIKE ? ORDER BY name",
            ("%" + search + "%",)
        ).fetchall()
    else:
        students = conn.execute(
            "SELECT * FROM Student ORDER BY name"
        ).fetchall()
    conn.close()

    return render_template("students.html", students=students, search=search)


@app.route("/students/new", methods=["GET", "POST"])
def new_student():
    if request.method == "POST":
        name = request.form["name"]
        dob = request.form["dob"]
        country_of_birth = request.form["country_of_birth"]
        gender = request.form["gender"]
        consent = 1 if request.form.get("consent") == "on" else 0
        zip_code = request.form["zip_code"]

        conn = get_db_connection()
        row = conn.execute("SELECT COALESCE(MAX(student_id), 0) + 1 AS next_id FROM Student").fetchone()
        next_id = row["next_id"]

        conn.execute(
            """
            INSERT INTO Student (student_id, name, dob, country_of_birth, gender, consent, zip_code)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (next_id, name, dob, country_of_birth, gender, consent, zip_code),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("list_students"))

    return render_template("student_form.html")


@app.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM Student WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("list_students"))



@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
def edit_student(student_id):
    conn = get_db_connection()
    student = conn.execute(
        "SELECT * FROM Student WHERE student_id = ?",
        (student_id,)
    ).fetchone()

    if request.method == "POST":
        name = request.form["name"]
        dob = request.form["dob"]
        country_of_birth = request.form["country_of_birth"]
        gender = request.form["gender"]
        consent = 1 if request.form.get("consent") == "on" else 0
        zip_code = request.form["zip_code"]

        conn.execute("""
            UPDATE Student
            SET name=?, dob=?, country_of_birth=?, gender=?, consent=?, zip_code=?
            WHERE student_id=?
        """, (name, dob, country_of_birth, gender, consent, zip_code, student_id))

        conn.commit()
        conn.close()
        return redirect(url_for('list_students'))

    conn.close()
    return render_template("student_form.html", student=student)


# ---------- COUNSELORS ----------

@app.route("/counselors")
def list_counselors():
    conn = get_db_connection()
    counselors = conn.execute(
        "SELECT * FROM Counselor ORDER BY name"
    ).fetchall()
    conn.close()
    return render_template("counselors.html", counselors=counselors)



# ---------- VISITS & ISSUES ----------

@app.route("/visits")
def list_visits():
    search = request.args.get("search", "")

    conn = get_db_connection()
    if search:
        visits = conn.execute(
            """
            SELECT
              v.visit_id,
              v.date,
              v.mode,
              s.name AS student_name,
              COUNT(i.issue_id) AS issue_count,
              COALESCE(ROUND(AVG(i.severity), 1), NULL) AS avg_severity
            FROM Visit v
            JOIN Student s ON s.student_id = v.student_id
            LEFT JOIN Issue i ON i.visit_id = v.visit_id
            WHERE s.name LIKE ?
               OR CAST(v.visit_id AS TEXT) LIKE ?
            GROUP BY v.visit_id
            ORDER BY v.date DESC, v.visit_id DESC
            """,
            ("%" + search + "%", "%" + search + "%")
        ).fetchall()
    else:
        visits = conn.execute(
            """
            SELECT
              v.visit_id,
              v.date,
              v.mode,
              s.name AS student_name,
              COUNT(i.issue_id) AS issue_count,
              COALESCE(ROUND(AVG(i.severity), 1), NULL) AS avg_severity
            FROM Visit v
            JOIN Student s ON s.student_id = v.student_id
            LEFT JOIN Issue i ON i.visit_id = v.visit_id
            GROUP BY v.visit_id
            ORDER BY v.date DESC, v.visit_id DESC
            """
        ).fetchall()

    conn.close()
    return render_template("visits.html", visits=visits, search=search)


@app.route("/visits/new", methods=["GET", "POST"])
def new_visit():
    if request.method == "POST":
        student_id = request.form["student_id"]
        date = request.form["date"]
        mode = request.form["mode"]
        issue_description = request.form["issue_description"]
        severity = int(request.form["severity"])

        conn = get_db_connection()

        visit_row = conn.execute(
            "SELECT COALESCE(MAX(visit_id), 0) + 1 AS next_id FROM Visit"
        ).fetchone()
        next_visit_id = visit_row["next_id"]

        conn.execute("""
            INSERT INTO Visit (visit_id, student_id, date, mode)
            VALUES (?, ?, ?, ?)
        """, (next_visit_id, student_id, date, mode))

        issue_row = conn.execute(
            "SELECT COALESCE(MAX(issue_id), 0) + 1 AS next_id FROM Issue"
        ).fetchone()
        next_issue_id = issue_row["next_id"]

        conn.execute("""
            INSERT INTO Issue (issue_id, visit_id, issue_description, severity)
            VALUES (?, ?, ?, ?)
        """, (next_issue_id, next_visit_id, issue_description, severity))

        conn.commit()
        conn.close()

        return redirect(url_for("list_visits"))

    return render_template("visit_form.html")


@app.route("/visits/<int:visit_id>/delete", methods=["POST"])
def delete_visit(visit_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM Visit WHERE visit_id = ?", (visit_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("list_visits"))


@app.route("/visits/<int:visit_id>")
def visit_detail(visit_id):
    conn = get_db_connection()

    visit = conn.execute(
        """
        SELECT
          v.visit_id,
          v.date,
          v.mode,
          s.student_id,
          s.name AS student_name
        FROM Visit v
        JOIN Student s ON s.student_id = v.student_id
        WHERE v.visit_id = ?
        """,
        (visit_id,)
    ).fetchone()

    if not visit:
        conn.close()
        return "Visit not found", 404

    issues = conn.execute(
        """
        SELECT
          issue_id,
          issue_description,
          severity
        FROM Issue
        WHERE visit_id = ?
        ORDER BY issue_id
        """,
        (visit_id,)
    ).fetchall()

    conn.close()
    return render_template("visit_detail.html", visit=visit, issues=issues)


# ---------- REFERRALS & FOLLOWUPS ----------

@app.route("/referrals")
def list_referrals():
    conn = get_db_connection()
    referrals = conn.execute(
        """
        SELECT
          r.referral_id,
          r.created_at,
          r.details,
          s.name AS student_name
        FROM Referral r
        JOIN Issue i ON i.issue_id = r.issue_id
        JOIN Visit v ON v.visit_id = i.visit_id
        JOIN Student s ON s.student_id = v.student_id
        ORDER BY r.created_at DESC, r.referral_id DESC
        """
    ).fetchall()

    followups = conn.execute(
        """
        SELECT
          f.followup_id,
          f.date,
          f.notes,
          f.complete,
          s.name AS student_name
        FROM Followup f
        JOIN Issue i ON i.issue_id = f.issue_id
        JOIN Counselor c ON c.counselor_id = f.counselor_id
        JOIN Visit v ON v.visit_id = i.visit_id
        JOIN Student s ON s.student_id = v.student_id
        ORDER BY f.date DESC, f.followup_id DESC
        """
    ).fetchall()
    conn.close()

    return render_template(
        "referrals.html",
        referrals=referrals,
        followups=followups,
    )


if __name__ == "__main__":
    app.run(debug=True)
