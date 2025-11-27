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
    country_filter = request.args.get("country", "")
    gender_filter = request.args.get("gender", "")
    zip_filter = request.args.get("zip", "")

    conn = get_db_connection()

    # Fetch unique options for dropdowns
    countries = [row["country_of_birth"] for row in conn.execute("SELECT DISTINCT country_of_birth FROM Student ORDER BY country_of_birth").fetchall()]
    genders = [row["gender"] for row in conn.execute("SELECT DISTINCT gender FROM Student ORDER BY gender").fetchall()]
    zips = [row["zip_code"] for row in conn.execute("SELECT DISTINCT zip_code FROM Student ORDER BY zip_code").fetchall()]

    # Build dynamic query
    query = "SELECT * FROM Student WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")
    if country_filter:
        query += " AND country_of_birth = ?"
        params.append(country_filter)
    if gender_filter:
        query += " AND gender = ?"
        params.append(gender_filter)
    if zip_filter:
        query += " AND zip_code = ?"
        params.append(zip_filter)

    query += " ORDER BY name"
    students = conn.execute(query, params).fetchall()
    conn.close()

    return render_template(
        "students.html",
        students=students,
        search=search,
        countries=countries,
        genders=genders,
        zips=zips,
        country_filter=country_filter,
        gender_filter=gender_filter,
        zip_filter=zip_filter
    )

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
        row = conn.execute(
            "SELECT COALESCE(MAX(student_id), 0) + 1 AS next_id FROM Student"
        ).fetchone()
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


@app.route("/students/<int:student_id>", methods=["GET", "POST"])
def view_student(student_id):
    conn = get_db_connection()

    # ---------- BASIC INFO ----------
    student = conn.execute(
        "SELECT * FROM Student WHERE student_id = ?", (student_id,)
    ).fetchone()

    # Update basic info
    if request.method == "POST" and request.form.get("form_type") == "basic_info":
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
        return redirect(url_for("view_student", student_id=student_id))

    # ---------- VISITS ----------
    visits = conn.execute("""
        SELECT * FROM Visit
        WHERE student_id = ?
        ORDER BY date DESC
    """, (student_id,)).fetchall()

    visit_data = []
    for visit in visits:
        # Get issues for each visit
        issues = conn.execute("""
            SELECT i.issue_id, i.issue_description, i.severity
            FROM Issue i
            WHERE i.visit_id = ?
        """, (visit["visit_id"],)).fetchall()

        issue_list = []
        for issue in issues:
            # Issue-Type
            types = conn.execute("""
                SELECT issue_type FROM Issue_Type
                WHERE issue_id = ?
            """, (issue["issue_id"],)).fetchall()
            type_list = [t["issue_type"] for t in types]

            # Issue-Category -> Category name
            categories = conn.execute("""
                SELECT c.name
                FROM Issue_Category ic
                JOIN Category c ON ic.category_id = c.category_id
                WHERE ic.issue_id = ?
            """, (issue["issue_id"],)).fetchall()
            category_list = [c["name"] for c in categories]

            # Suggestions for this visit
            suggestions = conn.execute("""
                SELECT s.details, c.name AS counselor_name
                FROM Suggestion s
                JOIN Counselor c ON s.counselor_id = c.counselor_id
                WHERE s.visit_id = ?
            """, (visit["visit_id"],)).fetchall()

            issue_list.append({
                "issue": issue,
                "types": type_list,
                "categories": category_list,
                "suggestions": suggestions
            })

        visit_data.append({
            "visit": visit,
            "issues": issue_list
        })

    # ---------- DIAGNOSIS ----------
    edit_diag_id = request.args.get("edit_diag_id", type=int)  # which diag is editable

    diagnoses = conn.execute("""
        SELECT d.diagnosis_id, d.diagnosis_date, d.provider_id, d.diagnosis_code,
            dl.diagnosis AS diagnosis_name,
            p.name AS provider_name
        FROM Diagnosis d
        JOIN Diagnosis_List dl ON d.diagnosis_code = dl.diagnosis_code
        JOIN Provider p ON d.provider_id = p.provider_id
        WHERE d.student_id = ?
    """, (student_id,)).fetchall()

    diagnosis_data = []
    for diag in diagnoses:
        symptoms = conn.execute("""
            SELECT sl.symptom
            FROM Symptom s
            JOIN Symptom_List sl ON s.symptom_code = sl.symptom_code
            WHERE s.diagnosis_id = ?
        """, (diag["diagnosis_id"],)).fetchall()
        symptom_list = [s["symptom"] for s in symptoms]

        diagnosis_data.append({
            "diagnosis_id": diag["diagnosis_id"],
            "diagnosis_date": diag["diagnosis_date"],
            "provider_id": diag["provider_id"],
            "provider_name": diag["provider_name"],
            "diagnosis_code": diag["diagnosis_code"],
            "diagnosis_name": diag["diagnosis_name"],
            "symptoms": symptom_list,
            "editable": diag["diagnosis_id"] == edit_diag_id
        })

    # ---------- DIAGNOSIS DROPDOWN DATA ----------
    providers = conn.execute("SELECT provider_id, name FROM Provider").fetchall()
    diag_list = conn.execute("SELECT diagnosis_code, diagnosis FROM Diagnosis_List").fetchall()
    symptoms_all = conn.execute("SELECT symptom_code, symptom FROM Symptom_List").fetchall()


    # ---------- COURSES ----------
    courses = conn.execute("""
        SELECT c.*
        FROM Student_Course sc
        JOIN Course c ON sc.course_id = c.course_id
        WHERE sc.student_id = ?
    """, (student_id,)).fetchall()

    # For adding new course
    all_courses = conn.execute("SELECT course_id, course_name FROM Course").fetchall()

    conn.close()

    return render_template(
        "student_view.html",
        student=student,
        visits=visit_data,
        diagnoses=diagnosis_data,
        courses=courses,
        providers=providers,
        diag_list=diag_list,
        symptoms_all=symptoms_all,
        all_courses=all_courses
    )




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
              COALESCE(MAX(i.severity), 0) AS has_critical_issue
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
              COALESCE(MAX(i.severity), 0) AS has_critical_issue
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

        severity_flag = 1 if request.form.get("severity") == "1" else 0

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
        """, (next_issue_id, next_visit_id, issue_description, severity_flag))

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

# ------------------ DIAGNOSIS ROUTES ------------------

@app.route("/diagnosis/<int:diagnosis_id>/edit", methods=["POST"])
def edit_diagnosis(diagnosis_id):
    conn = get_db_connection()
    diagnosis_date = request.form["diagnosis_date"]
    provider_id = request.form["provider_id"]
    diagnosis_code = request.form["diagnosis_code"]
    symptoms = request.form.getlist("symptoms")  # list of symptom_code

    # Update the diagnosis record
    conn.execute("""
        UPDATE Diagnosis
        SET diagnosis_date=?, provider_id=?, diagnosis_code=?
        WHERE diagnosis_id=?
    """, (diagnosis_date, provider_id, diagnosis_code, diagnosis_id))

    # Remove old symptoms
    conn.execute("DELETE FROM Symptom WHERE diagnosis_id=?", (diagnosis_id,))
    # Insert new symptoms
    for s in symptoms:
        conn.execute("INSERT INTO Symptom (diagnosis_id, symptom_code) VALUES (?, ?)",
                     (diagnosis_id, s))

    conn.commit()

    # Get the student_id to redirect back to their page
    student_id = conn.execute("SELECT student_id FROM Diagnosis WHERE diagnosis_id=?",
                              (diagnosis_id,)).fetchone()["student_id"]
    conn.close()
    return redirect(url_for("view_student", student_id=student_id))


@app.route("/diagnosis/<int:diagnosis_id>/delete", methods=["GET", "POST"])
def delete_diagnosis(diagnosis_id):
    conn = get_db_connection()
    # Get student_id before deleting
    student_id = conn.execute("SELECT student_id FROM Diagnosis WHERE diagnosis_id=?",
                              (diagnosis_id,)).fetchone()["student_id"]

    conn.execute("DELETE FROM Diagnosis WHERE diagnosis_id=?", (diagnosis_id,))
    # Also remove associated symptoms
    conn.execute("DELETE FROM Symptom WHERE diagnosis_id=?", (diagnosis_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("view_student", student_id=student_id))


@app.route("/students/<int:student_id>/diagnosis/add", methods=["POST"])
def add_diagnosis(student_id):
    conn = get_db_connection()
    diagnosis_date = request.form["diagnosis_date"]
    provider_id = request.form["provider_id"]
    diagnosis_code = request.form["diagnosis_code"]
    symptoms = request.form.getlist("symptoms")

    # Generate a new diagnosis_id
    row = conn.execute("SELECT COALESCE(MAX(diagnosis_id), 0) + 1 AS next_id FROM Diagnosis").fetchone()
    new_id = row["next_id"]

    # Insert new diagnosis
    conn.execute("""
        INSERT INTO Diagnosis (diagnosis_id, student_id, provider_id, diagnosis_code, diagnosis_date)
        VALUES (?, ?, ?, ?, ?)
    """, (new_id, student_id, provider_id, diagnosis_code, diagnosis_date))

    # Insert symptoms
    for s in symptoms:
        conn.execute("INSERT INTO Symptom (diagnosis_id, symptom_code) VALUES (?, ?)", (new_id, s))

    conn.commit()
    conn.close()
    return redirect(url_for("view_student", student_id=student_id))


# ------------------ COURSE ROUTES ------------------

@app.route("/students/<int:student_id>/course/add", methods=["POST"])
def add_course(student_id):
    course_id = request.form["course_id"]
    conn = get_db_connection()
    conn.execute("INSERT INTO Student_Course (student_id, course_id) VALUES (?, ?)", (student_id, course_id))
    conn.commit()
    conn.close()
    return redirect(url_for("view_student", student_id=student_id))


@app.route("/students/<int:student_id>/course/<int:course_id>/remove", methods=["GET", "POST"])
def remove_course(student_id, course_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM Student_Course WHERE student_id=? AND course_id=?", (student_id, course_id))
    conn.commit()
    conn.close()
    return redirect(url_for("view_student", student_id=student_id))


if __name__ == "__main__":
    app.run(debug=True)
