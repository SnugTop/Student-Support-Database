PRAGMA foreign_keys = ON;

--CREATE DATABASE `Student-Support-Center`;

--USE `Student-Support-Center`;


-- -----------------------------
-- STUDENT
-- -----------------------------
CREATE TABLE Student (
    student_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    country_of_birth VARCHAR(100) NOT NULL,
    gender CHAR(1) NOT NULL,
    consent BOOLEAN NOT NULL,
    zip_code CHAR(5) NOT NULL
);

-- -----------------------------
-- COURSE
-- -----------------------------
CREATE TABLE Course (
    course_id INT PRIMARY KEY,
    course_name VARCHAR(200) NOT NULL,
    period INT NOT NULL,
    teacher VARCHAR(100) NOT NULL,
    classroom CHAR(3) NOT NULL,
    CONSTRAINT course_unique UNIQUE (course_name, period, teacher)
);

-- -----------------------------
-- STUDENT-COURSE
-- -----------------------------
CREATE TABLE Student_Course (
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES Student(student_id),
    FOREIGN KEY (course_id) REFERENCES Course(course_id)
);

-- -----------------------------
-- COUNSELOR
-- -----------------------------
CREATE TABLE Counselor (
    counselor_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    paid_volunteer VARCHAR(10) NOT NULL CHECK (paid_volunteer IN ('paid', 'volunteer')),
    education VARCHAR(50) NOT NULL,
    experience INT NOT NULL
);

-- -----------------------------
-- COUNSELOR-SALARY
-- -----------------------------
CREATE TABLE Counselor_Salary (
    counselor_id INT PRIMARY KEY,
    salary INT NOT NULL,
    FOREIGN KEY (counselor_id) REFERENCES Counselor(counselor_id)
);

-- -----------------------------
-- VISIT
-- -----------------------------
CREATE TABLE Visit (
    visit_id INT PRIMARY KEY,
    student_id INT NOT NULL,
    date DATE NOT NULL,
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('in-person', 'virtual')),
    FOREIGN KEY (student_id) REFERENCES Student(student_id)
);

-- -----------------------------
-- VISIT-COUNSELOR
-- -----------------------------
CREATE TABLE Visit_Counselor (
    visit_id INT NOT NULL,
    counselor_id INT NOT NULL,
    PRIMARY KEY (visit_id, counselor_id),
    FOREIGN KEY (visit_id) REFERENCES Visit(visit_id),
    FOREIGN KEY (counselor_id) REFERENCES Counselor(counselor_id)
);

-- -----------------------------
-- ISSUE
-- -----------------------------
CREATE TABLE Issue (
    issue_id INT PRIMARY KEY,
    visit_id INT NOT NULL,
    issue_description TEXT NOT NULL,
    severity BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (visit_id) REFERENCES Visit(visit_id)
);

-- -----------------------------
-- CATEGORY
-- -----------------------------
CREATE TABLE Category (
    category_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL
);

-- -----------------------------
-- ISSUE-CATEGORY
-- -----------------------------
CREATE TABLE Issue_Category (
    issue_id INT NOT NULL,
    category_id INT NOT NULL,
    PRIMARY KEY (issue_id, category_id),
    FOREIGN KEY (issue_id) REFERENCES Issue(issue_id),
    FOREIGN KEY (category_id) REFERENCES Category(category_id)
);

-- -----------------------------
-- PROVIDER
-- -----------------------------
CREATE TABLE Provider (
    provider_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    organization VARCHAR(150) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    CONSTRAINT provider_unique UNIQUE (name, organization)
);

-- -----------------------------
-- DIAGNOSIS-LIST
-- -----------------------------
CREATE TABLE Diagnosis_List (
    diagnosis_code VARCHAR(10) PRIMARY KEY,
    diagnosis VARCHAR(150) NOT NULL UNIQUE
);

-- -----------------------------
-- DIAGNOSIS
-- -----------------------------
CREATE TABLE Diagnosis (
    diagnosis_id INT PRIMARY KEY,
    student_id INT NOT NULL,
    provider_id INT NOT NULL,
    diagnosis_code VARCHAR(10) NOT NULL,
    diagnosis_date DATE NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Student(student_id),
    FOREIGN KEY (provider_id) REFERENCES Provider(provider_id),
    FOREIGN KEY (diagnosis_code) REFERENCES Diagnosis_List(diagnosis_code)
);

-- -----------------------------
-- SYMPTOM-LIST
-- -----------------------------
CREATE TABLE Symptom_List (
    symptom_code VARCHAR(10) PRIMARY KEY,
    symptom VARCHAR(200) NOT NULL UNIQUE
);

-- -----------------------------
-- SYMPTOM
-- -----------------------------
CREATE TABLE Symptom (
    symptom_id INT PRIMARY KEY,
    diagnosis_id INT NOT NULL,
    symptom_code VARCHAR(10) NOT NULL,
    FOREIGN KEY (diagnosis_id) REFERENCES Diagnosis(diagnosis_id),
    FOREIGN KEY (symptom_code) REFERENCES Symptom_List(symptom_code),
    CONSTRAINT symptom_unique UNIQUE (diagnosis_id, symptom_code)
);

-- -----------------------------
-- FOLLOWUP
-- -----------------------------
CREATE TABLE Followup (
    followup_id INT PRIMARY KEY,
    visit_id INT NOT NULL,
    counselor_id INT NOT NULL,
    date DATE,
    notes TEXT,
    complete BOOLEAN,
    FOREIGN KEY (visit_id) REFERENCES Visit(visit_id),
    FOREIGN KEY (counselor_id) REFERENCES Counselor(counselor_id)
);

-- -----------------------------
-- SUGGESTION
-- -----------------------------
CREATE TABLE Suggestion (
    suggestion_id INT PRIMARY KEY,
    visit_id INT NOT NULL,
    counselor_id INT NOT NULL,
    details TEXT NOT NULL,
    FOREIGN KEY (visit_id) REFERENCES Visit(visit_id),
    FOREIGN KEY (counselor_id) REFERENCES Counselor(counselor_id)
);

-- -----------------------------
-- REFERRAL
-- -----------------------------
CREATE TABLE Referral (
    referral_id INT PRIMARY KEY,
    issue_id INT NOT NULL,
    details TEXT NOT NULL,
    student_report TEXT,
    created_at DATE NOT NULL,
    student_reported_at DATE,
    FOREIGN KEY (issue_id) REFERENCES Issue(issue_id)
);

-- -----------------------------
-- FINANCIAL
-- -----------------------------
CREATE TABLE Financial (
    financial_id INT PRIMARY KEY,
    issue_id INT NOT NULL,
    student_report TEXT,
    job_notes TEXT,
    created_at DATE NOT NULL,
    student_reported_at DATE,
    FOREIGN KEY (issue_id) REFERENCES Issue(issue_id)
);

-- -----------------------------
-- COURSEWORK
-- -----------------------------
CREATE TABLE Coursework (
    coursework_id INT PRIMARY KEY,
    course_id INT NOT NULL,
    issue_id INT NOT NULL,
    student_report TEXT,
    created_at DATE NOT NULL,
    student_reported_at DATE,
    FOREIGN KEY (course_id) REFERENCES Course(course_id),
    FOREIGN KEY (issue_id) REFERENCES Issue(issue_id)
);

-- -----------------------------
-- ISSUE-TYPE
-- -----------------------------
CREATE TABLE Issue_Type (
    issue_id INT NOT NULL,
    issue_type VARCHAR(50) NOT NULL,
    PRIMARY KEY (issue_id, issue_type),
    FOREIGN KEY (issue_id) REFERENCES Issue(issue_id)
);
