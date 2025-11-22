USE `Student-Support-Center`;


LOAD DATA LOCAL INFILE 'data/Category.csv'
INTO TABLE Category
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(category_id, name, description);


LOAD DATA LOCAL INFILE 'data/Counselor.csv'
INTO TABLE Counselor
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(counselor_id, name, paid_volunteer, education, experience);

LOAD DATA LOCAL INFILE 'data/Counselor-Salary.csv'
INTO TABLE Counselor_Salary
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(counselor_id, salary);

LOAD DATA LOCAL INFILE 'data/Course.csv'
INTO TABLE Course
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(course_id, course_name, period, teacher, classroom);

LOAD DATA LOCAL INFILE 'data/Coursework.csv'
INTO TABLE Coursework
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(coursework_id, course_id, issue_id, student_report, created_at, student_reported_at);

LOAD DATA LOCAL INFILE 'data/Diagnosis.csv'
INTO TABLE Diagnosis
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(diagnosis_id, issue_id, provider_id, diagnosis_code, diagnosis_date);


LOAD DATA LOCAL INFILE 'data/DiagnosisList.csv'
INTO TABLE Diagnosis_List
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(diagnosis_code, diagnosis);

LOAD DATA LOCAL INFILE 'data/Financial.csv'
INTO TABLE Financial
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(financial_id, issue_id, student_report, job_notes, created_at, student_reported_at);

LOAD DATA LOCAL INFILE 'data/Followup.csv'
INTO TABLE Followup
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(followup_id, issue_id, counselor_id, date, notes, complete);

LOAD DATA LOCAL INFILE 'data/Issue.csv'
INTO TABLE Issue
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(issue_id, visit_id, issue_description, severity);

LOAD DATA LOCAL INFILE 'data/Issue-Category.csv'
INTO TABLE Issue_Category
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(issue_id, category_id);

LOAD DATA LOCAL INFILE 'data/Issue-Type.csv'
INTO TABLE Issue_Type
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(issue_id, issue_type);

LOAD DATA LOCAL INFILE 'data/Provider.csv'
INTO TABLE Provider
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(provider_id, name, organization, specialty);

LOAD DATA LOCAL INFILE 'data/Referral.csv'
INTO TABLE Referral
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(referral_id, issue_id, details, student_report, created_at, student_reported_at);

LOAD DATA LOCAL INFILE 'data/Student.csv'
INTO TABLE Student
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(student_id, name, dob, country_of_birth, gender, consent, zip_code);

LOAD DATA LOCAL INFILE 'data/Student-Course.csv'
INTO TABLE Student_Course
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(student_id, course_id);

LOAD DATA LOCAL INFILE 'data/Suggestion.csv'
INTO TABLE Suggestion
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(suggestion_id, visit_id, counselor_id, details);

LOAD DATA LOCAL INFILE 'data/Symptom-List.csv'
INTO TABLE Symptom_List
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(symptom_code, symptom);

LOAD DATA LOCAL INFILE 'data/Symptom.csv'
INTO TABLE Symptom
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(symptom_id, diagnosis_id, symptom_code);

LOAD DATA LOCAL INFILE 'data/Visit.csv'
INTO TABLE Visit
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(visit_id, student_id, date, mode);

LOAD DATA LOCAL INFILE 'data/Visit-Counselor.csv'
INTO TABLE Visit_Counselor
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(visit_id, counselor_id);

