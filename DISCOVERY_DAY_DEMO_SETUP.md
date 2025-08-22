# 🚀 Discovery Day 데모 설정 가이드

이 문서는 LiveLabs AI Assistant Discovery Day 데모를 위한 완전한 설정 가이드입니다.

## 📋 목차
1. [사전 준비사항](#사전-준비사항)
2. [데이터베이스 설정](#데이터베이스-설정)
3. [데이터 로딩](#데이터-로딩)
4. [AI 프로필 설정](#ai-프로필-설정)
5. [데모 실행](#데모-실행)
6. [문제 해결](#문제-해결)

---

## 🛠️ 사전 준비사항

### 필수 요구사항
- **Oracle Cloud Infrastructure (OCI) 계정**
- **Python 3.8+** 설치
- **필요한 Python 패키지**: `requirements.txt` 참조
- **Oracle Instant Client** (로컬 연결용)

### 환경 변수 설정
```bash
export OCI_CONFIG_FILE=~/.oci/config
export TNS_ADMIN=/path/to/wallet
```

---

## 🗄️ 데이터베이스 설정

### Oracle Database 23ai 인스턴스 정보

**클라우드 위치**: Seoul Region  
**구획**: joungmin.ko compartment  
**데이터베이스명**: `discovery_day_demo`  
**관리자 계정**: `admin/Dhfkzmf#12345`  

### 지갑(Wallet) 정보
**지갑명**: `Wallet_FISQA4FO3MCEZC2E`  
**지갑 비밀번호**: `Dhfkzmf#12345`  

### 연결 설정
1. **지갑 다운로드**:
   ```bash
   # OCI Console에서 지갑 다운로드
   # 압축 해제 후 TNS_ADMIN 환경변수 설정
   ```

2. **연결 테스트**:
   ```python
   import oracledb
   
   connection = oracledb.connect(
       user="admin",
       password="Dhfkzmf#12345",
       dsn="discovery_day_demo_high"
   )
   print("Database connection successful!")
   ```

---

## 📊 데이터 로딩

### 1. LiveLabs 워크샵 데이터 스크래핑

**스크립트**: `workshop_text_scraper_refactored.py`

```bash
# 워크샵 데이터 스크래핑 실행
python workshop_text_scraper_refactored.py
```

**기능**:
- LiveLabs 웹사이트에서 워크샵 정보 수집
- 텍스트 콘텐츠 추출 및 정제
- 벡터 임베딩 생성
- Oracle Database에 저장

### 2. 기존 데이터 활용 (이미 저장된 경우)

#### 워크샵 데이터
**파일**: `data/livelabs_workshops.json`  
**대상 테이블**: `LIVELABS_WORKSHOPS2`  
**JSON Duality View**: `livelabs_workshops_json`  

```bash
# 워크샵 데이터 로딩
python workshop_data_importer.py --file data/livelabs_workshops.json
```

#### 사용자 데이터
**파일**: `data/livelabs_users.json`  
**대상 테이블**: `LIVELABS_USERS`  
**JSON Duality View**: `livelabs_users_json`  

```bash
# 사용자 데이터 로딩
python -c "
from utils.mongo_utils import load_json_to_duality_view
load_json_to_duality_view('data/livelabs_users.json', 'livelabs_users_json')
"
```

### 3. 데이터 검증

```sql
-- 워크샵 데이터 확인
SELECT COUNT(*) FROM LIVELABS_WORKSHOPS2;

-- 사용자 데이터 확인
SELECT COUNT(*) FROM LIVELABS_USERS;

-- JSON Duality View 테스트
SELECT * FROM livelabs_workshops_json WHERE ROWNUM <= 5;
```

---

## 🤖 AI 프로필 설정

### 1. 자격증명 생성

상세 설정은 [`LIVELABS_DATABASE_SCHEMA.md`](./LIVELABS_DATABASE_SCHEMA.md#oracle-select-ai-설정) 참조

```sql
-- Cohere 자격증명 생성
BEGIN 
  DBMS_CLOUD.CREATE_CREDENTIAL(
    credential_name => 'COHERE_CRED',
    -- 자격증명 정보는 보안상 별도 관리
  );
END;
```

### 2. AI 프로필 생성

```sql
BEGIN
  DBMS_CLOUD_AI.CREATE_PROFILE(
    profile_name => 'DISCOVERYDAY_AI_PROFILE',
    attributes   => '{
      "provider": "openai",
      "credential_name": "OPENAI_CRED",
      "object_list": [
        {"owner": "ADMIN", "name": "LIVELABS_USERS"},
        {"owner": "ADMIN", "name": "LIVELABS_USERS_SKILL"},
        {"owner": "ADMIN", "name": "USER_PROGRESS"},
        {"owner": "ADMIN", "name": "LIVELABS_WORKSHOPS2"}
      ]
    }'
  );
END;
```

### 3. 프로필 활성화

```sql
BEGIN
    DBMS_CLOUD_AI.SET_PROFILE('DISCOVERYDAY_AI_PROFILE');
END;
```

---

## 🎯 데모 실행

### Streamlit 애플리케이션 시작

```bash
# 메인 애플리케이션 실행
streamlit run streamlit_livelabs_app.py

# 또는 REST API 버전
streamlit run streamlit_livelabs_rest_app.py
```

### 데모 시나리오

#### 1. 워크샵 검색 및 추천
- **자연어 검색**: "Oracle Database 초보자를 위한 워크샵을 찾아줘"
- **시맨틱 검색**: 벡터 유사도 기반 추천
- **필터링**: 난이도, 카테고리, 소요시간별 검색

#### 2. 사용자 맞춤 추천
- **스킬 기반 추천**: 사용자의 기술 레벨에 맞는 워크샵
- **학습 진도 추적**: 완료한 워크샵 기록 및 다음 단계 제안
- **개인화된 학습 경로**: AI 기반 맞춤형 커리큘럼

#### 3. AI 어시스턴트 기능
- **자연어 쿼리**: "Python 개발자는 누구야?"
- **데이터 분석**: 워크샵 통계 및 트렌드 분석
- **학습 조언**: 개인별 학습 방향 제시

### 주요 기능 테스트

```python
# MCP 서버 테스트
python test/test_direct_mcp.py

# 임베딩 파이프라인 테스트
python test/test_batch_embedding.py

# AI 워크샵 플래너 테스트
python test/test_ai_workshop_planner.py
```

---

## 🔧 문제 해결

### 일반적인 문제

#### 1. 데이터베이스 연결 실패
```bash
# 지갑 경로 확인
echo $TNS_ADMIN

# 연결 문자열 확인
tnsping discovery_day_demo_high
```

#### 2. 임베딩 생성 오류
```python
# Cohere API 키 확인
from utils.genai_client import test_cohere_connection
test_cohere_connection()
```

#### 3. Streamlit 애플리케이션 오류
```bash
# 로그 확인
streamlit run streamlit_livelabs_app.py --logger.level=debug

# 포트 변경
streamlit run streamlit_livelabs_app.py --server.port=8502
```

### 로그 파일 위치
- **애플리케이션 로그**: `logs/livelabs_app.log`
- **데이터베이스 로그**: `logs/db_operations.log`
- **MCP 서버 로그**: `logs/mcp_server.log`

### 지원 연락처
- **기술 지원**: Oracle Cloud Support
- **프로젝트 문의**: joungmin.ko@oracle.com

---

## 📚 참고 문서

- [데이터베이스 스키마 문서](./LIVELABS_DATABASE_SCHEMA.md)
- [MCP 설정 가이드](./doc/MCP_SETUP_GUIDE.md)
- [Streamlit 애플리케이션 가이드](./doc/README_Streamlit.md)
- [아키텍처 문서](./아키텍처_문서.md)

