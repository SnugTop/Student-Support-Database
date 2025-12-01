from datetime import datetime
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

    # Get filter values from request
    type_filter = request.args.get("type", "")
    education_filter = request.args.get("education", "")
    exp_operator = request.args.get("exp_operator", ">=")
    exp_value = request.args.get("exp_value", "")
    salary_operator = request.args.get("salary_operator", ">=")
    salary_value = request.args.get("salary_value", "")

    # Base query
    query = """
        SELECT c.*, cs.salary
        FROM Counselor c
        LEFT JOIN Counselor_Salary cs ON c.counselor_id = cs.counselor_id
        WHERE 1=1
    """
    params = []

    if type_filter:
        query += " AND c.paid_volunteer = ?"
        params.append(type_filter)

    if education_filter:
        query += " AND c.education = ?"
        params.append(education_filter)

    if exp_value:
        query += f" AND c.experience {exp_operator} ?"
        params.append(exp_value)

    if salary_value:
        query += f" AND (cs.salary {salary_operator} ?) "
        params.append(salary_value)

    query += " ORDER BY c.name"
    counselors = conn.execute(query, params).fetchall()

    # Get distinct education options for dropdown
    educations = [row["education"] for row in conn.execute("SELECT DISTINCT education FROM Counselor").fetchall()]

    conn.close()

    return render_template(
        "counselors.html",
        counselors=counselors,
        type_filter=type_filter,
        education_filter=education_filter,
        exp_operator=exp_operator,
        exp_value=exp_value,
        salary_operator=salary_operator,
        salary_value=salary_value,
        educations=educations
    )

# ---------- COUNSELOR VIEW ----------

@app.route("/counselor/<int:counselor_id>", methods=["GET"])
def counselor_view(counselor_id):
    conn = get_db_connection()

    # Basic counselor info (including salary if exists)
    counselor = conn.execute("""
        SELECT c.*, cs.salary
        FROM Counselor c
        LEFT JOIN Counselor_Salary cs ON c.counselor_id = cs.counselor_id
        WHERE c.counselor_id = ?
    """, (counselor_id,)).fetchone()

    # --- Students and number of visits ---
    students = conn.execute("""
        SELECT s.student_id, s.name, COUNT(vc.visit_id) AS visit_count
        FROM Visit_Counselor vc
        JOIN Visit v ON vc.visit_id = v.visit_id
        JOIN Student s ON v.student_id = s.student_id
        WHERE vc.counselor_id = ?
        GROUP BY s.student_id, s.name
        ORDER BY visit_count DESC
    """, (counselor_id,)).fetchall()

    # --- Visits (most recent first) ---
    visits = conn.execute("""
        SELECT v.visit_id, v.date, s.student_id, s.name AS student_name
        FROM Visit_Counselor vc
        JOIN Visit v ON vc.visit_id = v.visit_id
        JOIN Student s ON v.student_id = s.student_id
        WHERE vc.counselor_id = ?
        ORDER BY v.date DESC
    """, (counselor_id,)).fetchall()

    # --- Followups ---
    # Incomplete (NULL, empty string, or 0)
    incomplete_followups = conn.execute("""
        SELECT 
            f.followup_id,
            f.visit_id,
            v.date AS visit_date,
            s.student_id,
            s.name AS student_name,
            f.date AS followup_date,
            f.notes
        FROM Followup f
        JOIN Visit v ON v.visit_id = f.visit_id
        JOIN Student s ON s.student_id = v.student_id
        WHERE f.counselor_id = ?
        AND (
            f.complete IS NULL
            OR f.complete = ''
            OR f.complete = 0
        )
        ORDER BY f.followup_id ASC
    """, (counselor_id,)).fetchall()



    # Completed (complete is present and not empty/zero)
    completed_followups = conn.execute("""
        SELECT 
            f.followup_id,
            f.visit_id,
            f.date,
            f.notes,
            f.complete,
            s.student_id,
            s.name AS student_name,
            v.date AS visit_date
        FROM Followup f
        JOIN Visit v ON v.visit_id = f.visit_id
        JOIN Student s ON s.student_id = v.student_id
        WHERE f.counselor_id = ?
        AND NOT (
            f.complete IS NULL
            OR f.complete = ''
            OR f.complete = 0
        )
        ORDER BY f.date DESC
    """, (counselor_id,)).fetchall()



    # --- Referrals (include student_reported_at) ---
    referrals = conn.execute("""
        SELECT r.*, v.student_id, s.name AS student_name
        FROM Referral r
        JOIN Issue i ON i.issue_id = r.issue_id
        JOIN Visit v ON v.visit_id = i.visit_id
        JOIN Visit_Counselor vc ON vc.visit_id = v.visit_id
        JOIN Student s ON s.student_id = v.student_id
        WHERE vc.counselor_id = ?
        ORDER BY (r.student_reported_at IS NOT NULL) ASC, r.created_at DESC
    """, (counselor_id,)).fetchall()

    # --- Financial Issues ---
    financial = conn.execute("""
        SELECT f.*, v.student_id, s.name AS student_name
        FROM Financial f
        JOIN Issue i ON i.issue_id = f.issue_id
        JOIN Visit v ON v.visit_id = i.visit_id
        JOIN Visit_Counselor vc ON vc.visit_id = v.visit_id
        JOIN Student s ON s.student_id = v.student_id
        WHERE vc.counselor_id = ?
        ORDER BY (f.student_reported_at IS NOT NULL) ASC, f.created_at DESC
    """, (counselor_id,)).fetchall()

    # --- Coursework Issues ---
    coursework = conn.execute("""
        SELECT c.*, v.student_id, s.name AS student_name
        FROM Coursework c
        JOIN Issue i ON i.issue_id = c.issue_id
        JOIN Visit v ON v.visit_id = i.visit_id
        JOIN Visit_Counselor vc ON vc.visit_id = v.visit_id
        JOIN Student s ON s.student_id = v.student_id
        WHERE vc.counselor_id = ?
        ORDER BY (c.student_reported_at IS NOT NULL) ASC, c.created_at DESC
    """, (counselor_id,)).fetchall()

    conn.close()

    return render_template(
        "counselor_view.html",
        counselor=counselor,
        counselor_id=counselor_id,
        students=students,
        visits=visits,
        incomplete_followups=incomplete_followups,
        completed_followups=completed_followups,
        referrals=referrals,
        financial=financial,
        coursework=coursework
    )

@app.route("/counselors/new", methods=["GET", "POST"])
def add_counselor():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        paid_volunteer = request.form.get("paid_volunteer", "").strip()  # 'paid' or 'volunteer'
        education = request.form.get("education", "").strip()
        experience = request.form.get("experience", "") or None
        salary = request.form.get("salary", "") or None

        conn = get_db_connection()
        # next id
        row = conn.execute("SELECT COALESCE(MAX(counselor_id), 0) + 1 AS next_id FROM Counselor").fetchone()
        next_id = row["next_id"]

        conn.execute("""
            INSERT INTO Counselor (counselor_id, name, paid_volunteer, education, experience)
            VALUES (?, ?, ?, ?, ?)
        """, (next_id, name, paid_volunteer, education, experience))
        # add salary only if paid and salary provided
        if paid_volunteer.lower() == "paid" and salary not in (None, ""):
            conn.execute("INSERT OR REPLACE INTO Counselor_Salary (counselor_id, salary) VALUES (?, ?)",
                         (next_id, salary))
        conn.commit()
        conn.close()
        return redirect(url_for("list_counselors"))

    # GET
    return render_template("counselors_new.html")


# ---------- UPDATE Followup ----------

@app.route("/update_followup/<int:followup_id>", methods=["POST"])
def update_followup(followup_id):
    date = request.form.get("date")
    notes = request.form.get("notes")
    complete_checkbox = request.form.get("complete")  # None if unchecked

    conn = get_db_connection()

    # 1. Look up the followup being edited
    f = conn.execute("""
        SELECT followup_id, visit_id, counselor_id
        FROM Followup
        WHERE followup_id = ?
    """, (followup_id,)).fetchone()

    if not f:
        return "Followup not found", 404

    visit_id = f["visit_id"]
    counselor_id = f["counselor_id"]

    # 2. Always mark current followup as "completed" (complete = 1)
    conn.execute("""
        UPDATE Followup
        SET date = ?, notes = ?, complete = 1
        WHERE followup_id = ?
    """, (date, notes, followup_id))

    # 3. If the counselor did NOT check "complete", create a new future followup
    cur = conn.execute("SELECT COALESCE(MAX(followup_id), 0) + 1 FROM Followup")
    new_id = cur.fetchone()[0]

    if not complete_checkbox:
        conn.execute("""
            INSERT INTO Followup (followup_id, visit_id, counselor_id, date, notes, complete)
            VALUES (?, ?, ?, NULL, NULL, NULL)
        """, (new_id, visit_id, counselor_id))

    conn.commit()

    return redirect(url_for("counselor_view", counselor_id=counselor_id))




# ---------- UPDATE Referral ----------
@app.route("/update_referral/<int:referral_id>", methods=["POST"])
def update_referral(referral_id):
    student_report = request.form.get("student_report", None) or None
    student_reported_at = request.form.get("student_reported_at", None) or None
    details = request.form.get("details", None) or None

    conn = get_db_connection()
    # optional: fetch counselor id to redirect back
    row = conn.execute("SELECT r.* FROM Referral r WHERE referral_id = ?", (referral_id,)).fetchone()
    if not row:
        conn.close()
        return "Referral not found", 404

    # Find counselor via visit -> issue -> visit_counselor
    issue_id = row["issue_id"]
    visit_row = conn.execute("SELECT visit_id FROM Issue WHERE issue_id = ?", (issue_id,)).fetchone()
    counselor_row = conn.execute("SELECT counselor_id FROM Visit_Counselor WHERE visit_id = ?", (visit_row["visit_id"],)).fetchone()
    counselor_id = counselor_row["counselor_id"] if counselor_row else None

    conn.execute("""
        UPDATE Referral
        SET student_report = ?, student_reported_at = ?, details = ?
        WHERE referral_id = ?
    """, (student_report, student_reported_at, details, referral_id))

    conn.commit()
    conn.close()
    if counselor_id:
        return redirect(url_for("counselor_view", counselor_id=counselor_id))
    return redirect(url_for("list_counselors"))


# ---------- UPDATE Financial ----------
@app.route("/update_financial/<int:financial_id>", methods=["POST"])
def update_financial(financial_id):
    student_report = request.form.get("student_report", None) or None
    student_reported_at = request.form.get("student_reported_at", None) or None
    job_notes = request.form.get("job_notes", None) or None

    conn = get_db_connection()
    row = conn.execute("SELECT f.* FROM Financial f WHERE financial_id = ?", (financial_id,)).fetchone()
    if not row:
        conn.close()
        return "Financial not found", 404

    issue_id = row["issue_id"]
    visit_row = conn.execute("SELECT visit_id FROM Issue WHERE issue_id = ?", (issue_id,)).fetchone()
    counselor_row = conn.execute("SELECT counselor_id FROM Visit_Counselor WHERE visit_id = ?", (visit_row["visit_id"],)).fetchone()
    counselor_id = counselor_row["counselor_id"] if counselor_row else None

    conn.execute("""
        UPDATE Financial
        SET student_report = ?, student_reported_at = ?, job_notes = ?
        WHERE financial_id = ?
    """, (student_report, student_reported_at, job_notes, financial_id))

    conn.commit()
    conn.close()
    if counselor_id:
        return redirect(url_for("counselor_view", counselor_id=counselor_id))
    return redirect(url_for("list_counselors"))


# ---------- UPDATE Coursework ----------
@app.route("/update_coursework/<int:coursework_id>", methods=["POST"])
def update_coursework(coursework_id):
    student_report = request.form.get("student_report", None) or None
    student_reported_at = request.form.get("student_reported_at", None) or None
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM Coursework WHERE coursework_id = ?", (coursework_id,)).fetchone()
    if not row:
        conn.close()
        return "Coursework not found", 404

    issue_id = row["issue_id"]
    visit_row = conn.execute("SELECT visit_id FROM Issue WHERE issue_id = ?", (issue_id,)).fetchone()
    counselor_row = conn.execute("SELECT counselor_id FROM Visit_Counselor WHERE visit_id = ?", (visit_row["visit_id"],)).fetchone()
    counselor_id = counselor_row["counselor_id"] if counselor_row else None

    conn.execute("""
        UPDATE Coursework
        SET student_report = ?, student_reported_at = ?
        WHERE coursework_id = ?
    """, (student_report, student_reported_at, coursework_id))

    conn.commit()
    conn.close()
    if counselor_id:
        return redirect(url_for("counselor_view", counselor_id=counselor_id))
    return redirect(url_for("list_counselors"))


# ---------- VISITS & ISSUES ----------

@app.route("/visits")
def list_visits():
    conn = get_db_connection()
    all_students = conn.execute("SELECT student_id, name FROM Student").fetchall()

    # Grab filters
    selected_students = request.args.getlist("students")
    mode = request.args.get("mode")
    issue_op = request.args.get("issue_op")
    issue_val = request.args.get("issue_val")
    critical = request.args.get("critical")

    query = """
        SELECT
            v.visit_id,
            v.date,
            v.mode,
            s.name AS student_name,
            COUNT(i.issue_id) AS issue_count,
            -- Evaluate severity robustly: treat various truthy values as 1
            COALESCE(MAX(
                CASE
                    WHEN i.severity IN (1, '1', 'TRUE', 'True', 'true') THEN 1
                    ELSE 0
                END
            ), 0) AS has_critical_issue
        FROM Visit v
        JOIN Student s ON s.student_id = v.student_id
        LEFT JOIN Issue i ON i.visit_id = v.visit_id
    """
    conditions = []
    params = []

    # Students filter
    if selected_students:
        conditions.append("v.student_id IN ({})".format(",".join("?"*len(selected_students))))
        params.extend(selected_students)

    # Mode filter
    if mode:
        conditions.append("v.mode = ?")
        params.append(mode)

    # Apply WHERE conditions
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Grouping needed for issue_count and critical
    query += " GROUP BY v.visit_id HAVING 1=1"

    # Issue count filter
    if issue_val:
        try:
            issue_val_int = int(issue_val)
            # validate operator
            if issue_op in (">", "<", "=", ">=", "<="):
                query += f" AND COUNT(i.issue_id) {issue_op} ?"
                params.append(issue_val_int)
        except ValueError:
            pass

    # Critical filter (visit is critical if ANY linked issue has severity true)
    # We use the same CASE expression in HAVING to compare against 0/1.
    if critical in ("0", "1"):
        query += """
         AND COALESCE(MAX(
             CASE
                 WHEN i.severity IN (1, '1', 'TRUE', 'True', 'true') THEN 1
                 ELSE 0
             END
         ), 0) = ?
        """
        params.append(int(critical))

    query += " ORDER BY v.date DESC, v.visit_id DESC"

    visits = conn.execute(query, params).fetchall()
    conn.close()
    return render_template("visits.html", visits=visits, all_students=all_students,
                           selected_students=selected_students,
                           mode=mode, issue_op=issue_op, issue_val=issue_val,
                           critical=critical)




@app.route("/visits/new", methods=["GET", "POST"])
def new_visit():
    conn = get_db_connection()
    cursor = conn.cursor()

    students = cursor.execute("SELECT student_id, name FROM Student ORDER BY name").fetchall()
    counselors = cursor.execute("SELECT counselor_id, name FROM Counselor ORDER BY name").fetchall()
    categories = cursor.execute("SELECT category_id, name FROM Category ORDER BY name").fetchall()
    courses = cursor.execute("SELECT course_id, course_name FROM Course ORDER BY course_id").fetchall()

    HEAD_COUNSELOR_ID = 113  # hardcoded

    if request.method == "POST":
        app.logger.info("Form data: %s", request.form.to_dict(flat=False))

        student_id = request.form.get("student_id", "").strip()
        date = request.form.get("date", "").strip()
        mode = request.form.get("mode", "").strip()

        # Collect counselor IDs from form
        form_values = request.form.getlist("counselor_ids") + request.form.getlist("counselor_ids[]")
        selected_counselor_ids = set()
        for v in form_values:
            try:
                selected_counselor_ids.add(int(v))
            except ValueError:
                continue

        # Check if any issue is critical
        issueCount = int(request.form.get("issueCount", 0))
        critical_issue_added = False
        for i in range(issueCount):
            if request.form.get(f"issues[{i}][critical]") == "1":
                critical_issue_added = True
                break

        if critical_issue_added:
            selected_counselor_ids.add(HEAD_COUNSELOR_ID)
            app.logger.info("Critical issue detected, added counselor 113")

        # Insert Visit
        next_visit_id = cursor.execute("SELECT COALESCE(MAX(visit_id),0)+1 FROM Visit").fetchone()[0]
        cursor.execute(
            "INSERT INTO Visit (visit_id, student_id, date, mode) VALUES (?, ?, ?, ?)",
            (next_visit_id, student_id, date, mode)
        )

        # Insert Visit_Counselor
        for cid in sorted(selected_counselor_ids):
            cursor.execute(
                "INSERT OR IGNORE INTO Visit_Counselor (visit_id, counselor_id) VALUES (?, ?)",
                (next_visit_id, cid)
            )

        # Process issues
        for i in range(issueCount):
            desc = request.form.get(f"issues[{i}][description]", "").strip()
            if not desc:
                continue
            critical = request.form.get(f"issues[{i}][critical]") == "1"
            next_issue_id = cursor.execute("SELECT COALESCE(MAX(issue_id),0)+1 FROM Issue").fetchone()[0]
            cursor.execute(
                "INSERT INTO Issue (issue_id, visit_id, issue_description, severity) VALUES (?, ?, ?, ?)",
                (next_issue_id, next_visit_id, desc, int(critical))
            )
            for cat_id in request.form.getlist(f"issues[{i}][categories][]"):
                if cat_id.strip():
                    try:
                        cursor.execute(
                            "INSERT INTO Issue_Category (issue_id, category_id) VALUES (?, ?)",
                            (next_issue_id, int(cat_id))
                        )
                    except Exception:
                        pass
            # Referral/Coursework/Financial types
            if f"issues[{i}][referral]" in request.form:
                cursor.execute("INSERT INTO Issue_Type (issue_id, issue_type) VALUES (?, 'Referral')", (next_issue_id,))
                details = request.form.get(f"issues[{i}][referral_details]", "")
                next_ref_id = cursor.execute("SELECT COALESCE(MAX(referral_id),0)+1 FROM Referral").fetchone()[0]
                cursor.execute("INSERT INTO Referral (referral_id, issue_id, details) VALUES (?, ?, ?)",
                               (next_ref_id, next_issue_id, details))
            if f"issues[{i}][coursework]" in request.form:
                cursor.execute("INSERT INTO Issue_Type (issue_id, issue_type) VALUES (?, 'Coursework')", (next_issue_id,))
            if f"issues[{i}][financial]" in request.form:
                cursor.execute("INSERT INTO Issue_Type (issue_id, issue_type) VALUES (?, 'Financial')", (next_issue_id,))

        # Suggestions
        suggestionCount = int(request.form.get("suggestionCount", 0))
        for i in range(suggestionCount):
            raw_cid = request.form.get(f"suggestions[{i}][counselor_id]")
            details = request.form.get(f"suggestions[{i}][details]", "").strip()
            if not raw_cid or not details:
                continue
            try:
                c_id = int(raw_cid)
            except ValueError:
                continue
            next_sugg_id = cursor.execute("SELECT COALESCE(MAX(suggestion_id),0)+1 FROM Suggestion").fetchone()[0]
            cursor.execute(
                "INSERT INTO Suggestion (suggestion_id, visit_id, counselor_id, details) VALUES (?, ?, ?, ?)",
                (next_sugg_id, next_visit_id, c_id, details)
            )

        conn.commit()
        app.logger.info("Visit %s saved with counselors %s", next_visit_id, sorted(selected_counselor_ids))
        conn.close()
        return redirect(url_for("list_visits"))

    conn.close()
    return render_template(
        "visit_form.html",
        students=students,
        counselors=counselors,
        categories=categories,
        courses=courses
    )




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

    # Fetch visit info
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

    # Fetch counselors
    counselors = conn.execute(
        """
        SELECT c.name
        FROM Counselor c
        JOIN Visit_Counselor vc ON vc.counselor_id = c.counselor_id
        WHERE vc.visit_id = ?
        """,
        (visit_id,)
    ).fetchall()

    # Fetch issues
    issues_raw = conn.execute(
        """
        SELECT
            i.issue_id,
            i.issue_description,
            CASE
              WHEN i.severity IN (1, '1', 'TRUE', 'True', 'true', 't', 'T') THEN 1
              ELSE 0
            END AS severity
        FROM Issue i
        WHERE i.visit_id = ?
        ORDER BY i.issue_id
        """,
        (visit_id,)
    ).fetchall()

    issues = []
    for i in issues_raw:
        issue = dict(i)

        # Categories
        categories = conn.execute(
            """
            SELECT c.name
            FROM Category c
            JOIN Issue_Category ic ON ic.category_id = c.category_id
            WHERE ic.issue_id = ?
            """,
            (i["issue_id"],)
        ).fetchall()
        issue["categories"] = ", ".join([c["name"] for c in categories]) if categories else ""

        # Types
        types_rows = conn.execute(
            "SELECT issue_type FROM Issue_Type WHERE issue_id = ?",
            (i["issue_id"],)
        ).fetchall()
        issue_types_list = [t["issue_type"] for t in types_rows] if types_rows else []
        issue["issue_types_list"] = issue_types_list
        issue["issue_types"] = ", ".join(issue_types_list) if issue_types_list else ""

        # Referral
        if "Referral" in issue_types_list:
            referral_rows = conn.execute(
                "SELECT referral_id, details FROM Referral WHERE issue_id = ?",
                (i["issue_id"],)
            ).fetchall()
            issue["referrals"] = [dict(r) for r in referral_rows]
        else:
            issue["referrals"] = []

        issues.append(issue)

    # Fetch suggestions for this visit
    suggestions_raw = conn.execute(
        """
        SELECT
            s.suggestion_id,
            s.counselor_id,
            s.details,
            s.student_report,
            s.student_reported_at,
            c.name AS counselor_name
        FROM Suggestion s
        JOIN Counselor c ON c.counselor_id = s.counselor_id
        WHERE s.visit_id = ?
        ORDER BY s.suggestion_id
        """,
        (visit_id,)
    ).fetchall()

    suggestions = [dict(row) for row in suggestions_raw]

    conn.close()

    return render_template(
        "visit_detail.html",
        visit=visit,
        counselors=counselors,
        issues=issues,
        suggestions=suggestions
    )


@app.route("/suggestions/<int:suggestion_id>/update", methods=["POST"])
def update_suggestion(suggestion_id):
    student_report = request.form.get("student_report")
    reported_at = request.form.get("student_reported_at")

    conn = get_db_connection()
    conn.execute(
        """
        UPDATE Suggestion
        SET student_report = ?, student_reported_at = ?
        WHERE suggestion_id = ?
        """,
        (student_report, reported_at, suggestion_id)
    )
    conn.commit()

    # fetch visit_id to redirect properly
    visit_id = conn.execute(
        "SELECT visit_id FROM Suggestion WHERE suggestion_id = ?",
        (suggestion_id,)
    ).fetchone()["visit_id"]

    conn.close()
    return redirect(url_for("visit_detail", visit_id=visit_id))





@app.route("/visits/<int:visit_id>/edit", methods=["GET", "POST"])
def edit_visit(visit_id):
    conn = get_db_connection()
    
    # Get visit info
    visit = conn.execute(
        "SELECT * FROM Visit WHERE visit_id = ?", (visit_id,)
    ).fetchone()
    if not visit:
        conn.close()
        return "Visit not found", 404

    # Students and counselors for dropdowns
    students = conn.execute("SELECT student_id, name FROM Student").fetchall()
    counselors = conn.execute("SELECT counselor_id, name FROM Counselor").fetchall()
    selected_counselors = [c['counselor_id'] for c in conn.execute(
        "SELECT counselor_id FROM Visit_Counselor WHERE visit_id = ?", (visit_id,)
    ).fetchall()]

    if request.method == "POST":
        student_id = request.form["student_id"]
        date = request.form["date"]
        mode = request.form["mode"]
        counselor_ids = request.form.getlist("counselor_ids")

        # Update visit table
        conn.execute(
            "UPDATE Visit SET student_id = ?, date = ?, mode = ? WHERE visit_id = ?",
            (student_id, date, mode, visit_id)
        )

        # Update counselors
        conn.execute("DELETE FROM Visit_Counselor WHERE visit_id = ?", (visit_id,))
        for c_id in counselor_ids:
            conn.execute(
                "INSERT INTO Visit_Counselor (visit_id, counselor_id) VALUES (?, ?)",
                (visit_id, c_id)
            )

        conn.commit()
        conn.close()
        return redirect(url_for("visit_detail", visit_id=visit_id))

    conn.close()
    return render_template("edit_visit.html",
                           visit=visit,
                           students=students,
                           counselors=counselors,
                           selected_counselors=selected_counselors)


@app.route("/issues/<int:issue_id>/edit", methods=["GET", "POST"])
def edit_issue(issue_id):
    conn = get_db_connection()

    # Fetch issue info
    issue = conn.execute("SELECT * FROM Issue WHERE issue_id = ?", (issue_id,)).fetchone()
    if not issue:
        conn.close()
        return "Issue not found", 404

    # Fetch categories and types
    categories = conn.execute("SELECT category_id, name FROM Category").fetchall()
    selected_categories = [c['category_id'] for c in conn.execute(
        "SELECT category_id FROM Issue_Category WHERE issue_id = ?", (issue_id,)
    ).fetchall()]

    types = conn.execute(
        "SELECT issue_type FROM Issue_Type WHERE issue_id = ?", (issue_id,)
    ).fetchall()
    type_list = [t['issue_type'] for t in types]

    referral_details = ''
    if 'Referral' in type_list:
        referral = conn.execute(
            "SELECT details FROM Referral WHERE issue_id = ?", (issue_id,)
        ).fetchone()
        if referral:
            referral_details = referral['details']

    if request.method == "POST":
        description = request.form["description"]
        critical = int(request.form["critical"])
        selected_category_ids = request.form.getlist("categories")
        issue_types = []
        referral_flag = request.form.get("referral")
        coursework_flag = request.form.get("coursework")
        financial_flag = request.form.get("financial")
        referral_text = request.form.get("referral_details", "")

        # Update issue
        conn.execute(
            "UPDATE Issue SET issue_description = ?, severity = ? WHERE issue_id = ?",
            (description, critical, issue_id)
        )

        # Update categories
        conn.execute("DELETE FROM Issue_Category WHERE issue_id = ?", (issue_id,))
        for cat_id in selected_category_ids:
            conn.execute(
                "INSERT INTO Issue_Category (issue_id, category_id) VALUES (?, ?)",
                (issue_id, cat_id)
            )

        # Update issue types
        conn.execute("DELETE FROM Issue_Type WHERE issue_id = ?", (issue_id,))
        if referral_flag:
            conn.execute(
                "INSERT INTO Issue_Type (issue_id, issue_type) VALUES (?, ?)",
                (issue_id, "Referral")
            )
            # Update referral table
            exists = conn.execute("SELECT COUNT(*) FROM Referral WHERE issue_id = ?", (issue_id,)).fetchone()[0]
            if exists:
                conn.execute("UPDATE Referral SET details = ? WHERE issue_id = ?", (referral_text, issue_id))
            else:
                next_ref_id = conn.execute("SELECT COALESCE(MAX(referral_id),0)+1 FROM Referral").fetchone()[0]
                conn.execute("INSERT INTO Referral (referral_id, issue_id, details) VALUES (?, ?, ?)",
                             (next_ref_id, issue_id, referral_text))
        if coursework_flag:
            conn.execute(
                "INSERT INTO Issue_Type (issue_id, issue_type) VALUES (?, ?)",
                (issue_id, "Coursework")
            )
        if financial_flag:
            conn.execute(
                "INSERT INTO Issue_Type (issue_id, issue_type) VALUES (?, ?)",
                (issue_id, "Financial")
            )

        conn.commit()
        conn.close()
        return redirect(url_for("visit_detail", visit_id=issue["visit_id"]))

    conn.close()
    return render_template("edit_issue.html",
                           issue=issue,
                           categories=categories,
                           selected_categories=selected_categories,
                           referral_flag='Referral' in type_list,
                           coursework_flag='Coursework' in type_list,
                           financial_flag='Financial' in type_list,
                           referral_details=referral_details)


# ---------- SQL Console ----------
@app.route("/sql", methods=["GET", "POST"])
def sql_console():
    query = ""
    headers = []
    rows = []
    error = None

    if request.method == "POST":
        query = request.form.get("query", "").strip()

        if query:
            upper = query.lstrip().upper()
            if not upper.startswith("SELECT"):
                error = "Only SELECT queries are allowed (read-only)."
            else:
                conn = None
                try:
                    conn = get_db_connection()
                    cur = conn.execute(query)
                    rows = cur.fetchall()
                    # cur.description has column metadata
                    if cur.description:
                        headers = [col[0] for col in cur.description]
                except sqlite3.Error as e:
                    error = f"SQL error: {e}"
                finally:
                    if conn:
                        conn.close()

    return render_template(
        "sql_console.html",
        query=query,
        headers=headers,
        rows=rows,
        error=error,
    )

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
          s.name AS student_name,
          c.name AS counselor_name
        FROM Followup f
        JOIN Visit v ON v.visit_id = f.visit_id
        JOIN Student s ON s.student_id = v.student_id
        JOIN Counselor c ON c.counselor_id = f.counselor_id
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


# ---------- REPORTS / ANALYTICS ----------

@app.route("/reports")
def reports_index():
    """
    Landing page that lists all available reports. each report is a link to a new page that displays the
    report corresponding to a specific requirement in the assignment.
    """
    reports = [
        {"id": 1,  "title": "1. Counselor data (directory)"},
        {"id": 2,  "title": "2. Student data (directory)"},
        {"id": 3,  "title": "3. Demographics: students by country"},
        {"id": 4,  "title": "4. Types of issues & categories"},
        {"id": 5,  "title": "5. Visit frequency by student"},
        {"id": 6,  "title": "6. Number of students per counselor"},
        {"id": 7,  "title": "7. Number of students per issue category"},
        {"id": 8,  "title": "8. Counts of referrals / financial / coursework help"},
        {"id": 9,  "title": "9. Students flagged as critical"},
        {"id": 10, "title": "10. Students who have not reported back after support"},
        {"id": 11, "title": "11. Counselors who have open follow ups"},
        {"id": 12, "title": "12. Counselors on payroll vs volunteers"},
        {"id": 13, "title": "13. Min / Max / Avg salary of paid counselors"},
        {"id": 14, "title": "14. Students with multiple issues"},
        {"id": 15, "title": "15. Students with {keyword}-related issues"},
        {"id": 16, "title": "16. Students with health issues per ZIP code"},
        {"id": 17, "title": "17. Courses with academic difficulty"},
    ]
    return render_template("reports.html", reports=reports)


@app.route("/reports/<int:report_id>")
def report_detail(report_id):
    """
    Runs a specific pre-written SQL report that corresponds to one of the requirements from the assignment
    and shows the result in a table.
    """
    title = ""
    description = ""
    headers = []
    rows = []
    error = None

    conn = get_db_connection()
    try:
        # ---------- 1. Counselor data ----------
        if report_id == 1:
            title = "1. Counselor data (directory)"
            description = "Lists all counselors with their type, education, and experience."
            sql = """
                SELECT
                    counselor_id,
                    name,
                    paid_volunteer,
                    education,
                    experience
                FROM Counselor
                ORDER BY name
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 2. Student data ----------
        elif report_id == 2:
            title = "2. Student data (directory)"
            description = "Lists all students with basic demographics."
            sql = """
                SELECT
                    student_id,
                    name,
                    dob,
                    country_of_birth,
                    gender,
                    consent,
                    zip_code
                FROM Student
                ORDER BY name
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 3. Demographics: which country is most common ----------
        elif report_id == 3:
            title = "3. Student demographics by country"
            description = (
                "Counts how many students come from each country of birth, "
                "sorted by the most common country."
            )
            sql = """
                SELECT
                    country_of_birth AS Country,
                    COUNT(*) AS num_students
                FROM Student
                GROUP BY country_of_birth
                ORDER BY num_students DESC, country_of_birth
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 4. Different types of issues / concerns ----------
        elif report_id == 4:
            title = "4. Types of issues & categories"
            description = (
                "Shows counts of issues by issue type and by category "
                "in a single combined table."
            )
            sql = """
                SELECT
                    'Issue type' AS dimension_kind,
                    it.issue_type AS dimension,
                    COUNT(*) AS num_issues
                FROM Issue_Type it
                GROUP BY it.issue_type

                UNION ALL

                SELECT
                    'Category' AS dimension_kind,
                    c.name AS dimension,
                    COUNT(*) AS num_issues
                FROM Category c
                JOIN Issue_Category ic ON ic.category_id = c.category_id
                GROUP BY c.category_id, c.name

                ORDER BY dimension_kind, num_issues DESC, dimension
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 5. Frequency of visit by each student ----------
        elif report_id == 5:
            title = "5. Visit frequency by student"
            description = "Shows how many counseling visits each student has had."
            sql = """
                SELECT
                    s.student_id,
                    s.name,
                    COUNT(v.visit_id) AS num_visits
                FROM Student s
                LEFT JOIN Visit v ON v.student_id = s.student_id
                GROUP BY s.student_id, s.name
                ORDER BY num_visits DESC, s.name
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 6. Number of students per counselor ----------
        elif report_id == 6:
            title = "6. Number of students per counselor"
            description = "For each counselor, shows how many distinct students they have seen."
            sql = """
                SELECT
                    c.counselor_id,
                    c.name,
                    COUNT(DISTINCT v.student_id) AS num_students
                FROM Counselor c
                LEFT JOIN Visit_Counselor vc
                    ON vc.counselor_id = c.counselor_id
                LEFT JOIN Visit v
                    ON v.visit_id = vc.visit_id
                GROUP BY c.counselor_id, c.name
                ORDER BY num_students DESC, c.name
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 7. Number of students for each category of problems ----------
        elif report_id == 7:
            title = "7. Number of students per issue category"
            description = (
                "Counts how many distinct students have at least one issue "
                "in each problem category."
            )
            sql = """
                SELECT
                    cat.category_id,
                    cat.name AS category_name,
                    COUNT(DISTINCT v.student_id) AS num_students
                FROM Category cat
                LEFT JOIN Issue_Category ic
                    ON ic.category_id = cat.category_id
                LEFT JOIN Issue i
                    ON i.issue_id = ic.issue_id
                LEFT JOIN Visit v
                    ON v.visit_id = i.visit_id
                GROUP BY cat.category_id, cat.name
                ORDER BY num_students DESC, cat.name
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 8. Number of times referred to healthcare / jobs / dean, etc. ----------
        elif report_id == 8:
            title = "8. Counts of referrals / financial / coursework help"
            description = (
                "Shows how many records there are for healthcare referrals, "
                "job/financial help, and coursework/dean/tutor support."
            )
            sql = """
                SELECT 'Healthcare referrals' AS type, COUNT(*) AS num_records
                FROM Referral

                UNION ALL

                SELECT 'Job / financial help' AS type, COUNT(*) AS num_records
                FROM Financial

                UNION ALL

                SELECT 'Coursework / dean / tutor support' AS type, COUNT(*) AS num_records
                FROM Coursework
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 9. Students flagged as critical ----------
        elif report_id == 9:
            title = "9. Students flagged as critical (severity = TRUE)"
            description = (
                "Lists students who have at least one issue marked as critical "
                "(severity marked as TRUE / 1 / similar)."
            )
            sql = """
                SELECT DISTINCT
                    s.student_id,
                    s.name,
                    s.zip_code
                FROM Student s
                JOIN Visit v ON v.student_id = s.student_id
                JOIN Issue i ON i.visit_id = v.visit_id
                WHERE i.severity IN (1, '1', 'TRUE', 'True', 'true', 't', 'T')
                ORDER BY s.name
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 10. Students who did not report back after receiving advice ----------
        elif report_id == 10:
            title = "10. Students who have not reported back after support"
            description = (
                "Shows students who have outstanding items (suggestions, referrals, "
                "financial, or coursework) with no student_reported_at date."
            )
            sql = """
                SELECT DISTINCT
                    s.student_id,
                    s.name,
                    src.source
                FROM (
                    -- Suggestions
                    SELECT
                        v.student_id,
                        'Suggestion' AS source,
                        sug.student_reported_at AS reported_at
                    FROM Suggestion sug
                    JOIN Visit v ON v.visit_id = sug.visit_id

                    UNION ALL

                    -- Referrals
                    SELECT
                        v.student_id,
                        'Referral' AS source,
                        r.student_reported_at AS reported_at
                    FROM Referral r
                    JOIN Issue i ON i.issue_id = r.issue_id
                    JOIN Visit v ON v.visit_id = i.visit_id

                    UNION ALL

                    -- Financial
                    SELECT
                        v.student_id,
                        'Financial' AS source,
                        f.student_reported_at AS reported_at
                    FROM Financial f
                    JOIN Issue i ON i.issue_id = f.issue_id
                    JOIN Visit v ON v.visit_id = i.visit_id

                    UNION ALL

                    -- Coursework
                    SELECT
                        v.student_id,
                        'Coursework' AS source,
                        cw.student_reported_at AS reported_at
                    FROM Coursework cw
                    JOIN Issue i ON i.issue_id = cw.issue_id
                    JOIN Visit v ON v.visit_id = i.visit_id
                ) src
                JOIN Student s ON s.student_id = src.student_id
                WHERE src.reported_at IS NULL
                   OR src.reported_at = ''
                ORDER BY s.name, src.source
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 11. Counselors who never followed up with any student ----------
        elif report_id == 11:
            title = "11. Counselors With Open Follow-Ups"
            description = "Shows counselors that have no records in the Followup table."
            sql = """
                SELECT DISTINCT
                    c.counselor_id,
                    c.name,
                    c.paid_volunteer
                FROM Counselor c
                JOIN Followup f ON f.counselor_id = c.counselor_id
                WHERE f.complete IS NULL
                   OR f.complete = ''
                   OR f.complete = 0
                ORDER BY c.name;
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 12. Counselors on payroll vs volunteers ----------
        elif report_id == 12:
            title = "12. Counselors on payroll vs volunteers"
            description = "Shows each counselor's role and also the counts by type."

            sql_list = """
                SELECT
                    counselor_id,
                    name,
                    paid_volunteer AS role
                FROM Counselor
                ORDER BY role, name
            """
            cur = conn.execute(sql_list)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

            sql_counts = """
                SELECT
                    paid_volunteer AS role,
                    COUNT(*) AS num_counselors
                FROM Counselor
                GROUP BY paid_volunteer
                ORDER BY role
            """
            cur2 = conn.execute(sql_counts)
            rows2 = cur2.fetchall()
            headers2 = [col[0] for col in cur2.description]

        # ---------- 13. Min, max, avg salary of paid counselors ----------
        elif report_id == 13:
            title = "13. Min / Max / Avg salary of paid counselors"
            description = "Summary statistics for counselor salaries."
            sql = """
                SELECT
                    MIN(salary) AS min_salary,
                    MAX(salary) AS max_salary,
                    AVG(salary) AS avg_salary
                FROM Counselor_Salary
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 14. Students who have multiple issues ----------
        elif report_id == 14:
            title = "14. Students with multiple issues"
            description = (
                "Lists students who have 2 or more distinct issues recorded."
            )
            sql = """
                SELECT
                    s.student_id,
                    s.name,
                    COUNT(DISTINCT i.issue_id) AS num_issues
                FROM Student s
                JOIN Visit v ON v.student_id = s.student_id
                JOIN Issue i ON i.visit_id = v.visit_id
                GROUP BY s.student_id, s.name
                HAVING COUNT(DISTINCT i.issue_id) >= 2
                ORDER BY num_issues DESC, s.name
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 15. Students who reported a certain issue (e.g. bullying) ----------
        elif report_id == 15:
            title = "15. Students with a specific issue keyword"
            description = (
                "Enter a keyword below to find all students who reported issues containing that word."
            )

            keyword = request.args.get("keyword", "").strip()
            if keyword:
                like_pattern = f"%{keyword}%"
                sql = """
                    SELECT DISTINCT
                        s.student_id,
                        s.name,
                        i.issue_id,
                        i.issue_description
                    FROM Issue i
                    JOIN Visit v ON v.visit_id = i.visit_id
                    JOIN Student s ON s.student_id = v.student_id
                    WHERE i.issue_description LIKE ?
                    ORDER BY s.name
                """
                cur = conn.execute(sql, (like_pattern,))
                rows = cur.fetchall()
                headers = [col[0] for col in cur.description]
            else:
                rows = []
                headers = []


        # ---------- 16. Number of students with health issues per ZIP code ----------
        elif report_id == 16:
            title = "16. Students with health issues per ZIP code"
            description = (
                "Counts how many distinct students with at least one diagnosis live in each ZIP code."
            )
            sql = """
                SELECT
                    s.zip_code,
                    COUNT(DISTINCT s.student_id) AS num_students_with_health_issues
                FROM Diagnosis d
                JOIN Student s ON s.student_id = d.student_id
                GROUP BY s.zip_code
                ORDER BY num_students_with_health_issues DESC, s.zip_code
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        # ---------- 17. Courses & number of students with academic difficulty ----------
        elif report_id == 17:
            title = "17. Courses with academic difficulty"
            description = (
                "Shows courses and how many distinct students have coursework-related issues in those courses."
            )
            sql = """
                SELECT
                    c.course_id,
                    c.course_name,
                    COUNT(DISTINCT s.student_id) AS num_students_with_difficulty
                FROM Coursework cw
                JOIN Course c ON c.course_id = cw.course_id
                JOIN Issue i ON i.issue_id = cw.issue_id
                JOIN Visit v ON v.visit_id = i.visit_id
                JOIN Student s ON s.student_id = v.student_id
                GROUP BY c.course_id, c.course_name
                ORDER BY num_students_with_difficulty DESC, c.course_name
            """
            cur = conn.execute(sql)
            rows = cur.fetchall()
            headers = [col[0] for col in cur.description]

        else:
            error = f"Unknown report id: {report_id}"

    except sqlite3.Error as e:
        error = f"SQL error while running report {report_id}: {e}"
    finally:
        conn.close()

    return render_template(
        "report_detail.html",
        report_id=report_id,
        title=title,
        description=description,
        headers=headers,
        rows=rows,
        error=error,
    )

if __name__ == "__main__":
    app.run(debug=True)
