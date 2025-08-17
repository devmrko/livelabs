### 1. 테이블 생성
CREATE TABLE ADMIN.LIVELABS_WORKSHOPS 
(
  ID           VARCHAR2(24),
  TITLE        VARCHAR2(200),
  DESCRIPTION  VARCHAR2(4000),
  DURATION     VARCHAR2(50),
  VIEWS        NUMBER,
  URL          VARCHAR2(1000),
  PAGE_NUMBER  NUMBER,
  MONGO_ID     VARCHAR2(100)
)
TABLESPACE DATA
LOGGING;

### 2. PRIMARY KEY 및 인덱스 생성 (MONGO_ID 기준)
CREATE UNIQUE INDEX ADMIN.NEW_UK_1 ON ADMIN.LIVELABS_WORKSHOPS (MONGO_ID)
  TABLESPACE DATA
  LOGGING;

ALTER TABLE ADMIN.LIVELABS_WORKSHOPS
  ADD PRIMARY KEY (MONGO_ID)
  USING INDEX ADMIN.NEW_UK_1;

### 3. 컬럼 주석 및 어노테이션 (Select AI 지원)
COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS.ID IS
'@ORA_JSON_PROPERTY id
@ORA_TEXT_SEARCH
LiveLabs 워크숍의 내부 고유 ID입니다.';

COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS.TITLE IS
'@ORA_JSON_PROPERTY title
@ORA_TEXT_SEARCH
워크숍 제목입니다. 예: "Getting Started with OCI"';

COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS.DESCRIPTION IS
'@ORA_JSON_PROPERTY description
@ORA_TEXT_SEARCH
워크숍 설명 요약입니다. 예: "OCI 컴퓨트 및 네트워크를 소개합니다."';

COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS.DURATION IS
'@ORA_JSON_PROPERTY duration
워크숍 예상 소요 시간입니다. 예: "2 hrs, 30 mins"';

COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS.VIEWS IS
'@ORA_JSON_PROPERTY views
해당 워크숍의 조회 수입니다.';

COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS.URL IS
'@ORA_JSON_PROPERTY url
워크숍 상세 페이지 URL입니다.';

COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS.PAGE_NUMBER IS
'@ORA_JSON_PROPERTY page_number
워크숍이 포함된 카탈로그 페이지 번호입니다.';

COMMENT ON COLUMN ADMIN.LIVELABS_WORKSHOPS.MONGO_ID IS
'@ORA_JSON_PROPERTY _id
@ORA_TEXT_SEARCH
MongoDB 원본 ObjectId로 매핑되는 고유 식별자입니다.';

### 4. 테이블 설명 주석
COMMENT ON TABLE ADMIN.LIVELABS_WORKSHOPS IS
'Oracle LiveLabs 워크숍 정보를 저장하는 테이블이며, Select AI 및 JSON Duality View 기반 검색을 위해 구성됨.';

### 5. JSON Duality View 생성 (DML 지원)
drop view admin.livelabs_workshops_json;

CREATE OR REPLACE JSON RELATIONAL DUALITY VIEW admin.livelabs_workshops_json AS
SELECT JSON {
  '_id'         : mongo_id,
  'id'          : id,
  'title'       : title,
  'description' : description,
  'duration'    : duration,
  'views'       : views,
  'url'         : url,
  'page_number' : page_number
}
FROM admin.livelabs_workshops
  WITH INSERT UPDATE DELETE;

select * FROM admin.livelabs_workshops