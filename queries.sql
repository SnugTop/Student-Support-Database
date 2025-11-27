-- 1: Finding Counselor Data
SELECT counselor_id, name, paid_volunteer, education, experience
FROM Counselor
ORDER BY name;

-- 2: Finding Student Data
SELECT student_id, name, dob, country_of_birth, gender, consent, zip_code
FROM Student
ORDER BY name;

-- 3:
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
