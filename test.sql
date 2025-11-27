-- Question 10:
SELECT DISTINCT
  s.student_id,
  s.name,
  'Healthcare referral' AS context
FROM Referral r
JOIN Issue i ON i.issue_id = r.issue_id
JOIN Visit v ON v.visit_id = i.visit_id
JOIN Student s ON s.student_id = v.student_id
WHERE r.student_reported_at IS NULL
   OR TRIM(r.student_reported_at) = ''

UNION

SELECT DISTINCT
  s.student_id,
  s.name,
  'Financial/job help' AS context
FROM Financial f
JOIN Issue i ON i.issue_id = f.issue_id
JOIN Visit v ON v.visit_id = i.visit_id
JOIN Student s ON s.student_id = v.student_id
WHERE f.student_reported_at IS NULL
   OR TRIM(f.student_reported_at) = ''

UNION

SELECT DISTINCT
  s.student_id,
  s.name,
  'Coursework/tutor support' AS context
FROM Coursework cw
JOIN Issue i ON i.issue_id = cw.issue_id
JOIN Visit v ON v.visit_id = i.visit_id
JOIN Student s ON s.student_id = v.student_id
WHERE cw.student_reported_at IS NULL
   OR TRIM(cw.student_reported_at) = ''
ORDER BY name;
