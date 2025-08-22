# 🧪 LiveLabs AI Assistant 테스트 스위트 문서

이 문서는 LiveLabs AI Assistant 시스템의 테스트 파일들에 대한 상세한 설명을 제공합니다.

## 📋 목차
1. [테스트 파일 개요](#테스트-파일-개요)
2. [핵심 기능 테스트](#핵심-기능-테스트)
3. [데이터베이스 테스트](#데이터베이스-테스트)
4. [API 및 서비스 테스트](#api-및-서비스-테스트)
5. [실행 방법](#실행-방법)

---

## 📊 테스트 파일 개요

현재 테스트 디렉토리에는 **12개의 핵심 테스트 파일**이 있으며, 각각 시스템의 특정 기능을 검증합니다.

| 파일명 | 크기 | 주요 기능 |
|--------|------|-----------|
| `test_ai_workshop_planner.py` | 3.3KB | AI 워크샵 플래너 및 추천 시스템 |
| `test_batch_embedding.py` | 2.6KB | 배치 벡터 임베딩 처리 |
| `test_direct_mcp.py` | 1.6KB | MCP 서비스 직접 호출 테스트 |
| `test_embedding_text_prep.py` | 3.3KB | 임베딩용 텍스트 전처리 |
| `test_enhanced_workflow.py` | 2.0KB | 향상된 AI 추론 워크플로우 |
| `test_mcp_connection.py` | 3.5KB | MCP 서비스 연결성 테스트 |
| `test_mongo_db.py` | 11.3KB | MongoDB 운영 및 데이터 관리 |
| `test_new_apis.py` | 5.0KB | 최신 REST API 엔드포인트 |
| `test_nl_query.py` | 2.6KB | 자연어 쿼리 처리 |
| `test_oracle_db.py` | 6.6KB | Oracle Database 연결 및 쿼리 |
| `test_rest_apis.py` | 4.5KB | REST API 엔드포인트 테스트 |
| `test_user_skills_mcp_client.py` | 3.1KB | 사용자 스킬 관리 MCP 클라이언트 |

---

## 🤖 핵심 기능 테스트

### 1. `test_ai_workshop_planner.py`
**목적**: AI 기반 워크샵 추천 및 계획 시스템 테스트

**주요 기능**:
- 사용자 관리 (추가, 조회, 업데이트)
- 스킬 관리 (추가, 레벨 설정)
- 워크샵 추천 알고리즘
- 학습 진도 추적

**테스트 시나리오**:
```python
# 사용자 관리
"새로운 사용자 김철수를 추가해주세요. 이메일은 kim@example.com입니다"
"사용자 정보를 조회해주세요"

# 스킬 관리
"김철수의 Python 스킬을 중급으로 설정해주세요"
"Oracle Database 고급 스킬을 추가해주세요"

# 워크샵 추천
"김철수에게 적합한 워크샵을 추천해주세요"
"초보자를 위한 Oracle 워크샵을 찾아주세요"
```

**실행 방법**:
```bash
python test/test_ai_workshop_planner.py
```

### 2. `test_enhanced_workflow.py`
**목적**: AI 추론기의 다단계 워크플로우 테스트

**주요 기능**:
- 쿼리 분석 및 의도 파악
- 서비스 라우팅 결정
- 다단계 워크플로우 실행
- 결과 통합 및 응답 생성

**테스트 예시**:
```python
query = "고정민의 skill을 감안해서 추천할 workshop을 알려줘"
# Step 1: NL Query로 사용자 스킬 조회
# Step 2: Semantic Search로 적합한 워크샵 검색
```

---

## 🗄️ 데이터베이스 테스트

### 3. `test_oracle_db.py`
**목적**: Oracle Database 23ai 연결 및 쿼리 테스트

**주요 기능**:
- 데이터베이스 연결 검증
- `LIVELABS_WORKSHOPS2` 테이블 쿼리
- 벡터 검색 기능 테스트
- JSON Duality Views 검증

**테스트 쿼리**:
```sql
-- 워크샵 데이터 조회
SELECT COUNT(*) FROM admin.livelabs_workshops2;

-- 벡터 유사도 검색
SELECT title, VECTOR_DISTANCE(cohere4_embedding, :query_vector) as similarity
FROM admin.livelabs_workshops2
ORDER BY similarity
FETCH FIRST 5 ROWS ONLY;
```

### 4. `test_mongo_db.py`
**목적**: MongoDB 운영 및 JSON 데이터 처리 테스트

**주요 기능**:
- MongoDB 연결 및 인증
- 워크샵 데이터 로딩 (`livelabs_workshops.json`)
- CRUD 연산 테스트
- 데이터 검증 및 통계

**데이터 처리 흐름**:
1. JSON 파일에서 워크샵 데이터 로드
2. MongoDB에 데이터 삽입/업데이트
3. 인덱스 생성 및 최적화
4. 쿼리 성능 테스트

---

## 🔗 API 및 서비스 테스트

### 5. `test_rest_apis.py`
**목적**: REST API 엔드포인트 전체 테스트

**테스트 엔드포인트**:
```bash
# 시맨틱 검색 서비스 (포트 8001)
GET  /health
POST /search
GET  /statistics

# 자연어 쿼리 서비스 (포트 8002)  
GET  /health
POST /users/search/nl

# 사용자 스킬 서비스 (포트 8003)
GET  /health
GET  /users/connection-status
```

### 6. `test_new_apis.py`
**목적**: 최신 API 기능 및 새로운 엔드포인트 테스트

**새로운 기능**:
- 향상된 검색 알고리즘
- 개선된 사용자 관리
- 새로운 통계 엔드포인트
- 성능 최적화 검증

### 7. `test_nl_query.py`
**목적**: 자연어 쿼리 처리 시스템 테스트

**테스트 쿼리 예시**:
```python
test_queries = [
    "Who are the Python developers?",
    "Find users with advanced Oracle skills", 
    "Show me data scientists",
    "Who has machine learning experience?",
    "List all users with their skills"
]
```

---

## 🔌 MCP (Model Context Protocol) 테스트

### 8. `test_direct_mcp.py`
**목적**: MCP 서비스 직접 호출 테스트 (프로토콜 우회)

**테스트 방식**:
- MCP 프로토콜 없이 직접 함수 호출
- 빠른 단위 테스트 실행
- 핵심 로직 검증

### 9. `test_mcp_connection.py`
**목적**: MCP 프로토콜을 통한 서비스 연결성 테스트

**테스트 서비스**:
- `mcp_livelabs_semantic_search.py`
- `mcp_livelabs_user_profiles.py`
- `mcp_livelabs_user_skills_progression.py`

### 10. `test_user_skills_mcp_client.py`
**목적**: 사용자 스킬 관리 MCP 클라이언트 테스트

**테스트 기능**:
- 사용자 추가/조회
- 스킬 추가/업데이트
- 진도 추적
- 워크샵 완료 기록

---

## 🧬 데이터 처리 테스트

### 11. `test_batch_embedding.py`
**목적**: 배치 벡터 임베딩 처리 파이프라인 테스트

**처리 단계**:
1. 워크샵 데이터 조회
2. 텍스트 전처리 및 정제
3. Cohere API를 통한 벡터 생성
4. Oracle Database에 벡터 저장
5. 처리 결과 통계 생성

**테스트 설정**:
```python
# 소규모 테스트 (3개 워크샵만 처리)
success = processor.process_workshops(limit=3)
```

### 12. `test_embedding_text_prep.py`
**목적**: 임베딩용 텍스트 전처리 로직 테스트

**전처리 과정**:
- HTML 태그 제거
- 특수 문자 정제
- 텍스트 길이 최적화
- 키워드 추출 및 가중치 적용

**샘플 데이터 구조**:
```python
sample_workshop = {
    "_id": "test_123",
    "title": "Sample Workshop Title",
    "description": "Workshop description...",
    "duration": "2 hours",
    "views": 1500,
    "keywords": ["python", "database", "tutorial"]
}
```

---

## 🚀 실행 방법

### 전체 테스트 실행
```bash
# 모든 테스트 파일 실행
for test_file in test/test_*.py; do
    echo "Running $test_file..."
    python "$test_file"
    echo "---"
done
```

### 카테고리별 테스트 실행

#### 데이터베이스 테스트
```bash
python test/test_oracle_db.py
python test/test_mongo_db.py
```

#### API 테스트
```bash
python test/test_rest_apis.py
python test/test_new_apis.py
python test/test_nl_query.py
```

#### MCP 테스트
```bash
python test/test_direct_mcp.py
python test/test_mcp_connection.py
python test/test_user_skills_mcp_client.py
```

#### AI 기능 테스트
```bash
python test/test_ai_workshop_planner.py
python test/test_enhanced_workflow.py
```

#### 데이터 처리 테스트
```bash
python test/test_batch_embedding.py
python test/test_embedding_text_prep.py
```

### 테스트 환경 설정

#### 필수 환경 변수
```bash
export TNS_ADMIN=/path/to/wallet
export COHERE_API_KEY=your_cohere_api_key
export MONGODB_URI=your_mongodb_connection_string
```

#### 서비스 시작 (테스트 전 필요)
```bash
# MCP 서비스들 시작
python MCP/rest_livelabs_semantic_search.py &
python MCP/rest_livelabs_nl_query.py &
python MCP/rest_livelabs_user_skills_progression.py &
```

---

## 📈 테스트 결과 해석

### 성공 지표
- ✅ **PASS**: 테스트 성공
- 📊 **통계 정보**: 처리된 데이터 수량
- 🔍 **검색 결과**: 반환된 결과의 품질과 정확성

### 실패 시 확인사항
- ❌ **데이터베이스 연결**: 지갑 파일 및 연결 문자열 확인
- ❌ **API 키**: Cohere, OpenAI API 키 유효성 확인
- ❌ **서비스 상태**: MCP 서비스들이 실행 중인지 확인
- ❌ **데이터 존재**: 필요한 테스트 데이터가 로드되었는지 확인

---

## 🔧 문제 해결

### 일반적인 오류

#### 1. 데이터베이스 연결 오류
```bash
# 지갑 경로 확인
echo $TNS_ADMIN
tnsping discovery_day_demo_high
```

#### 2. MCP 서비스 연결 실패
```bash
# 서비스 포트 확인
netstat -an | grep :800[1-3]

# 서비스 재시작
pkill -f "rest_livelabs"
python MCP/rest_livelabs_semantic_search.py &
```

#### 3. 임베딩 생성 오류
```python
# API 키 테스트
from utils.genai_client import test_cohere_connection
test_cohere_connection()
```

### 로그 확인
```bash
# 애플리케이션 로그
tail -f logs/livelabs_app.log

# 테스트 실행 로그
python test/test_name.py 2>&1 | tee test_results.log
```

---

## 📚 관련 문서

- [데이터베이스 스키마](../LIVELABS_DATABASE_SCHEMA.md)
- [Discovery Day 데모 설정](../DISCOVERY_DAY_DEMO_SETUP.md)
- [MCP 설정 가이드](../doc/MCP_SETUP_GUIDE.md)
- [아키텍처 문서](../아키텍처_문서.md)

---

**마지막 업데이트**: 2025-08-22  
**테스트 환경**: Oracle Database 23ai, Python 3.8+, MCP Protocol 2024-11-05
