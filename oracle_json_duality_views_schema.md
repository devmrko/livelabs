## JSON Duality view creation scripts
```
-- for add user, update user, or get userId by name via momgo db interface
CREATE OR REPLACE JSON RELATIONAL DUALITY VIEW admin.livelabs_users_json AS
SELECT JSON {
  '_id' : lu.mongo_id,
  'userId' : lu.user_id,
  'name' : lu.name,
  'email' : lu.email,
  'createdDate' : CASE
    WHEN lu.created_date IS NOT NULL
    THEN TO_CHAR(lu.created_date, 'YYYY-MM-DD"T"HH24:MI:SS')
    ELSE null
  END
}
FROM admin.livelabs_users lu
WITH INSERT UPDATE DELETE;

-- for add or update workshop's user progression(completion date, rating(1-5), status('STARTED','COMPLETED') via momgo db interface
CREATE OR REPLACE JSON RELATIONAL DUALITY VIEW admin.user_progress_json AS
SELECT JSON {
    '_id' : up.progress_id,
    'userId' : up.user_id,
    'workshopId' : up.workshop_id,
    'status' : up.status,
    'completionDate' : CASE 
        WHEN up.completion_date IS NOT NULL 
        THEN TO_CHAR(up.completion_date, 'YYYY-MM-DD"T"HH24:MI:SS')
        ELSE null
    END,
    'rating' : up.rating,
    'created' : TO_CHAR(up.created_date, 'YYYY-MM-DD"T"HH24:MI:SS')
}
FROM admin.user_progress up
WITH INSERT UPDATE DELETE;

-- for add or update user's skill, skill's experienceLevel(BEGINNER, INTERMEDIATE, ADVANCED) via momgo db interface
CREATE OR REPLACE JSON RELATIONAL DUALITY VIEW admin.user_skills_json AS
SELECT JSON {
    '_id' : s.mongo_id,
    'userId' : s.user_id,
    'skillName' : s.skill,
    'experienceLevel' : s.experience_level,
    'skillAdded' : TO_CHAR(s.created_date, 'YYYY-MM-DD"T"HH24:MI:SS')
}
FROM admin.livelabs_users_skill s
WITH INSERT UPDATE DELETE;

```