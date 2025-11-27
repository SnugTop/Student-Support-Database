-- -----------------------------
-- Question 3:
--  Finding Counselor Data
-- -----------------------------
SELECT counselor_id, name, paid_volunteer, education, experience
FROM Counselor
ORDER BY name;

-- -----------------------------
-- Question 3:
-- Finding Student Data
-- -----------------------------
SELECT student_id, name, dob, country_of_birth, gender, consent, zip_code
FROM Student
ORDER BY name;

-- -----------------------------
-- Question 3:
-- -----------------------------

-- By Birth Country
SELECT country_of_birth, COUNT(*) AS num_students
FROM Student
GROUP BY country_of_birth
ORDER BY num_students DESC;

-- By Gender
SELECT gender, COUNT(*) AS num_students
FROM Student
GROUP BY gender
ORDER BY num_students DESC;

-- By Age
SELECT age, COUNT(*) AS num_students
FROM Student
GROUP BY age
ORDER BY num_students DESC;


-- -----------------------------
-- Question 4:
-- Different Types of issues / concerns
-- -----------------------------

-- Issue Type
SELECT issue_type, COUNT(*) AS num_issues
FROM Issue_Type
GROUP BY issue_type
ORDER BY num_issues DESC;

-- Category
SELECT c.name AS category_name, COUNT(*) AS num_issues
FROM Category c
JOIN Issue_Category ic ON ic.category_id = c.category_id
GROUP BY c.category_id, c.name
ORDER BY num_issues DESC;


-- -----------------------------
-- Question 5:
-- Frequency of Visits by Students
-- -----------------------------
SELECT
  s.student_id,
  s.name,
  COUNT(v.visit_id) AS visit_count
FROM Student s
LEFT JOIN Visit v ON v.student_id = s.student_id
GROUP BY s.student_id, s.name
ORDER BY visit_count DESC, s.name;

-- -----------------------------
-- Question 6:
-- Number of students per counselor
-- -----------------------------
SELECT
  c.counselor_id,
  c.name,
  COUNT(DISTINCT v.student_id) AS num_students
FROM Counselor c
LEFT JOIN Visit_Counselor vc ON vc.counselor_id = c.counselor_id
LEFT JOIN Visit v ON v.visit_id = vc.visit_id
GROUP BY c.counselor_id, c.name
ORDER BY num_students DESC, c.name;

-- -----------------------------
-- Question 7:
-- Number of students for each category of problems
-- -----------------------------
SELECT
  c.name AS category_name,
  COUNT(DISTINCT s.student_id) AS num_students
FROM Category c
JOIN Issue_Category ic ON ic.category_id = c.category_id
JOIN Issue i ON i.issue_id = ic.issue_id
JOIN Visit v ON v.visit_id = i.visit_id
JOIN Student s ON s.student_id = v.student_id
GROUP BY c.category_id, c.name
ORDER BY num_students DESC, c.name;


-- -----------------------------
-- Question 8:
-- Number of times referred to healthcare / jobs / dean, etc.
-- -----------------------------
SELECT 'Healthcare referrals' AS type, COUNT(*) AS num_records
FROM Referral

UNION ALL

SELECT 'Job / financial help' AS type, COUNT(*) AS num_records
FROM Financial

UNION ALL

SELECT 'Coursework / dean / tutor support' AS type, COUNT(*) AS num_records
FROM Coursework;

-- -----------------------------
-- Question 9:
-- Students flagged as critical (severity TRUE)
-- -----------------------------
SELECT DISTINCT
  s.student_id,
  s.name,
  s.zip_code
FROM Student s
JOIN Visit v ON v.student_id = s.student_id
JOIN Issue i ON i.visit_id = v.visit_id
WHERE i.severity = 'TRUE'
ORDER BY s.name;

-- -----------------------------
-- Question 10:
-- Students who did not report back after receiving advice
-- -----------------------------



-- -----------------------------
-- Question 11:
-- Counselors who never followed up with any student (We dont have any data for this)
-- -----------------------------
SELECT
  c.counselor_id,
  c.name,
  c.paid_volunteer
FROM Counselor c
LEFT JOIN Followup f ON f.counselor_id = c.counselor_id
WHERE f.counselor_id IS NULL
ORDER BY c.name;


-- -----------------------------
-- Question 12:
-- Counselors on payroll vs volunteers
-- -----------------------------

-- list with type
SELECT
  c.counselor_id,
  c.name,
  c.paid_volunteer
FROM Counselor c
ORDER BY c.paid_volunteer, c.name;

-- counts by type
SELECT
  paid_volunteer,
  COUNT(*) AS num_counselors
FROM Counselor
GROUP BY paid_volunteer
ORDER BY paid_volunteer;


-- -----------------------------
-- Question 13:
-- Min, max, avg salary of paid counselors
-- -----------------------------
SELECT
  MIN(salary) AS min_salary,
  MAX(salary) AS max_salary,
  AVG(salary) AS avg_salary
FROM Counselor_Salary;

-- -----------------------------
-- Question 14:
-- Students who have multiple issues
-- -----------------------------
SELECT
  s.student_id,
  s.name,
  COUNT(DISTINCT i.issue_id) AS num_issues
FROM Student s
JOIN Visit v ON v.student_id = s.student_id
JOIN Issue i ON i.visit_id = v.visit_id
GROUP BY s.student_id, s.name
HAVING COUNT(DISTINCT i.issue_id) >= 2
ORDER BY num_issues DESC, s.name;

-- -----------------------------
-- Question 15:
-- Students who reported a certain issue
-- -----------------------------
SELECT DISTINCT
  s.student_id,
  s.name,
  i.issue_id,
  i.issue_description
FROM Issue i
JOIN Visit v ON v.visit_id = i.visit_id
JOIN Student s ON s.student_id = v.student_id
WHERE i.issue_description LIKE '%bullying%'
ORDER BY s.name;

-- -----------------------------
-- Question 16:
-- Number of students with health issues per zip code
-- -----------------------------
SELECT
  s.zip_code,
  COUNT(DISTINCT s.student_id) AS num_students_with_health_issues
FROM Diagnosis d
JOIN Issue i ON i.issue_id = d.issue_id
JOIN Visit v ON v.visit_id = i.visit_id
JOIN Student s ON s.student_id = v.student_id
GROUP BY s.zip_code
ORDER BY num_students_with_health_issues DESC, s.zip_code;

-- -----------------------------
-- Question 17:
-- Courses & number of students with academic difficulty in those courses
-- -----------------------------
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
ORDER BY num_students_with_difficulty DESC, c.course_name;

-- -----------------------------
-- Question 18 Security:
-- SQL Injection for Add Student
-- -----------------------------
-- Add student and enter name:
Robert'); DROP TABLE Student;--

-- -----------------------------
-- Question 19 Security:
-- Drop Table on SQL Console
-- ----------------------------
DROP TABLE Student;

-- -----------------------------
-- Question 20 Security:
-- SQL injection test on search fields
-- ----------------------------
-- in search field enter:
' OR 1=1--
