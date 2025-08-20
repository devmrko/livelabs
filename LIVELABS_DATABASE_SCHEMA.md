## Oracle Database Table Schema
```
-- ADMIN.LIVELABS_WORKSHOPS2 definition

CREATE TABLE "ADMIN"."LIVELABS_WORKSHOPS2" 
(
    "ID" VARCHAR2(100) PRIMARY KEY,
    "MONGO_ID" VARCHAR2(100) NOT NULL UNIQUE,
    "TITLE" VARCHAR2(500),
    "DESCRIPTION" CLOB,
    "TEXT_CONTENT" CLOB,
    "KEYWORDS" JSON,
    "AUTHOR" VARCHAR2(200),
    "CREATED_AT" DATE,
    "DIFFICULTY" VARCHAR2(50),
    "CATEGORY" VARCHAR2(200),
    "DURATION_ESTIMATE" VARCHAR2(50),
    "RESOURCE_TYPE" VARCHAR2(100),
    "SOURCE" VARCHAR2(100),
    "URL" VARCHAR2(500),
    "LANGUAGE" VARCHAR2(10),
    "COHERE4_EMBEDDING" VECTOR(1536, FLOAT32)
);

COMMENT ON TABLE ADMIN.LIVELABS_WORKSHOPS2 IS 'Oracle LiveLabs workshops and training courses catalog. Contains available learning content with descriptions, difficulty levels, categories, and metadata. Use this table to find workshops, search courses by topic, filter by difficulty, analyze workshop popularity, get course details, or recommend appropriate training content to users based on their skill level and interests.';

COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.ID IS 'Unique identifier for each learning resource record';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.MONGO_ID IS 'Original MongoDB document ID for data lineage tracking';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.TITLE IS 'Main title/headline of the learning resource (searchable text)';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.DESCRIPTION IS 'Detailed summary, overview, and learning objectives';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.TEXT_CONTENT IS 'Full text content for comprehensive search and analysis';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.KEYWORDS IS 'JSON array of tags and keywords (e.g., ["javascript", "tutorial", "beginner"])';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.AUTHOR IS 'Content creator, instructor, or author name';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.CREATED_AT IS 'Publication or creation date';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.DIFFICULTY IS 'Skill level: Beginner, Intermediate, Advanced, Expert';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.CATEGORY IS 'Subject area: Programming, Data Science, Design, etc.';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.DURATION_ESTIMATE IS 'Time to complete: "30 minutes", "2 hours", "1 week"';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.RESOURCE_TYPE IS 'Content format: Article, Video, Course, Tutorial, Documentation';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2."SOURCE" IS 'Origin platform: YouTube, Medium, Coursera, etc.';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.URL IS 'Direct web link to access the original resource';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2."LANGUAGE" IS 'Content language code (EN, ES, FR, etc.)';
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS2.COHERE4_EMBEDDING IS 'AI vector embedding for semantic similarity search and recommendations';
```

## JSON Duality view creation scripts
```
-- for add workshop, update workshop, or get workshop by id via momgo db interface
CREATE OR REPLACE FORCE EDITIONABLE JSON RELATIONAL DUALITY VIEW "ADMIN"."LIVELABS_WORKSHOPS_JSON2"  DEFAULT COLLATION "USING_NLS_COMP"  AS 
  SELECT JSON {
  '_id'               : mongo_id,  -- or use : mongo_id if available
  'id'                : id,
  'title'             : title,
  'description'       : description,
  'text_content'      : text_content,
  'keywords'          : keywords,
  'author'            : author,
  'created_at'        : TO_CHAR(created_at, 'YYYY-MM-DD'),
  'difficulty'        : difficulty,
  'category'          : category,
  'duration_estimate' : duration_estimate,
  'resource_type'     : resource_type,
  'source'            : source,
  'url'               : url,
  'language'          : language
}
FROM admin.livelabs_workshops2
  WITH INSERT UPDATE DELETE;

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

## JSON Duality View's value exmaple
```
{
  "title": "Get Started with Oracle Exadata Database Service @Azure",
  "url": "/pls/apex/r/dbpm/livelabs/view-workshop?wid=4010&clear=RR,180&session=11192223075513",
  "created_at": null,
  "keywords": [
    "Oracle Exadata",
    "Azure",
    "Database Service",
    "Provisioning",
    "VNet",
    "Subnet",
    "VM Cluster",
    "CDB",
    "PDB",
    "OCI"
  ],
  "author": "Sanjay Rahane",
  "description": null,
  "category": "Database",
  "language": "en",
  "duration_estimate": "2 Hours 30 Minutes",
  "_id": "4010",
  "source": "Oracle LiveLabs",
  "_metadata": {
    "etag": "4EF46EBBDC6970B44494032909324DA4",
    "asof": "000028D46548A4FB"
  },
  "resource_type": "WORKSHOP",
  "id": "4010",
  "difficulty": "INTERMEDIATE",
  "text_content": "Introduction\nAbout this Workshop\n\nThis hands-on workshop provides users with step-by-step instructions on provisioning Oracle Exadata Database @Azure. It provides detailed technical steps about pre-requisites steps and preparation needed for creating an Oracle Exadata infrastructure and Oracle Exadata VM Cluster and then create CDBs and PDBs.\n\nOracle Exadata Database @Azure helps to run Oracle Database natively in Microsoft Azure with the highest levels of performance, availability, security, and cost-effectiveness available in the cloud.\n\nEstimated Workshop Time: 2 Hours 30 Minutes\n\nWorkshop Objectives\n\nIn this workshop, you will learn how to:\n\nStep 1. Create Resource Group in Azure Cloud\nStep 2. Create VNet in Azure Cloud\nStep 3. Add Subnet and Delegate to the Oracle Database @Azure service\nStep 4. Create Oracle Exadata Infrastructure resource through Microsoft Azure Portal\nStep 5. Create Oracle Exadata VM Cluster resource through Microsoft Azure Portal\nStep 6. Create Oracle Database on an Exadata Database Service @Azure\nPrerequisites\nAn Oracle Free Tier, Always Free, Paid or LiveLabs Cloud Account\nFamiliarity with Oracle Cloud Infrastructure (OCI) is helpful\nBasic knowledge about DB @Azure concepts is helpful\nFamiliarity with Oracle Exadata Database is helpful\nCollapse All Tasks\nLearn More\nYou can find more information about Oracle Exadata Database @Azure here\nTechnical support\n\nFor all OCI related issues, Oracle Cloud Support is the first line of support. For any technical issues related to Oracle Exadata Database @Azure, please sign in to the OCI Console, then click the life raft icon.\n\nFor all Azure related issues and questions. Get help in the Help + support section of the Azure portal.\n\nAcknowledgements\nAuthor - Sanjay Rahane, Principal Cloud Architect, North America Cloud Engineering\nContributors - Bhaskar Sudarshan, Director, North America Cloud Engineering\nLast Updated By/Date - Sanjay Rahane, August 2024"
}
```