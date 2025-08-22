# 🛠️ LiveLabs AI Assistant 유틸리티 모듈 문서

이 문서는 `utils/` 디렉토리에 있는 유틸리티 모듈들의 목적과 기능을 설명합니다.

## 📋 목차
1. [모듈 개요](#모듈-개요)
2. [AI 및 추론 모듈](#ai-및-추론-모듈)
3. [데이터베이스 연결 모듈](#데이터베이스-연결-모듈)
4. [벡터 검색 및 임베딩](#벡터-검색-및-임베딩)
5. [웹 스크래핑 및 파싱](#웹-스크래핑-및-파싱)
6. [모듈 간 의존성](#모듈-간-의존성)
7. [사용 예시](#사용-예시)

---

## 📊 모듈 개요

`utils/` 디렉토리는 LiveLabs AI Assistant 시스템의 **핵심 유틸리티 모듈**들을 포함합니다. 총 **8개의 주요 모듈**이 있으며, 각각 특정 기능을 담당합니다.

| 파일명 | 크기 | 주요 기능 | 카테고리 |
|--------|------|-----------|----------|
| `ai_reasoner.py` | 25.2KB | AI 추론 엔진 및 서비스 선택 | 🤖 AI/추론 |
| `genai_client.py` | 12.6KB | Oracle GenAI API 클라이언트 | 🤖 AI/추론 |
| `oracle_db.py` | 10.0KB | Oracle Database 연결 관리 | 🗄️ 데이터베이스 |
| `mongo_utils.py` | 5.2KB | MongoDB 연결 및 운영 | 🗄️ 데이터베이스 |
| `vector_search.py` | 9.3KB | 벡터 검색 및 시맨틱 매칭 | 🔍 검색/임베딩 |
| `oci_embedding.py` | 6.2KB | OCI 벡터 임베딩 생성 | 🔍 검색/임베딩 |
| `selenium_utils.py` | 14.1KB | 웹 스크래핑 (안티-디텍션) | 🌐 웹/파싱 |
| `workshop_parser.py` | 4.5KB | 워크샵 데이터 파싱 | 🌐 웹/파싱 |

---

## 🤖 AI 및 추론 모듈

### 1. `ai_reasoner.py` - AI 추론 엔진

**목적**: 사용자 쿼리를 분석하여 적절한 MCP 서비스를 선택하고 다단계 워크플로우를 실행

**핵심 클래스**: `AIReasoner`

**주요 기능**:
- **쿼리 분석**: 자연어 쿼리의 의도 파악
- **서비스 선택**: `services.json` 설정을 기반으로 적절한 MCP 서비스 결정
- **다단계 워크플로우**: 복잡한 쿼리를 여러 단계로 분해하여 처리
- **동적 추론**: 이전 결과를 바탕으로 다음 단계 결정

**사용 시나리오**:
```python
# 사용자 쿼리: "고정민의 스킬을 바탕으로 추천 워크샵을 찾아줘"
# Step 1: livelabs-nl-query 서비스로 사용자 스킬 조회
# Step 2: livelabs-semantic-search 서비스로 관련 워크샵 검색
```

**의존성**: `genai_client.py`, `services.json`

### 2. `genai_client.py` - Oracle GenAI 클라이언트

**목적**: Oracle Generative AI 서비스와의 통신을 위한 래퍼 클라이언트

**핵심 클래스**: `OracleGenAIClient`

**주요 기능**:
- **OCI 인증**: Oracle Cloud Infrastructure 설정 관리
- **모델 호출**: Cohere Command 모델을 통한 텍스트 생성
- **에러 처리**: API 호출 실패 시 적절한 예외 처리
- **설정 관리**: 모델 파라미터 및 엔드포인트 관리

**지원 모델**:
- `cohere.command-r-plus-08-2024` (추론용)
- `cohere.command-r-08-2024` (일반 생성용)

**사용 예시**:
```python
client = OracleGenAIClient()
response = client.generate_text(
    prompt="사용자 쿼리를 분석해주세요",
    model_id="cohere.command-r-plus-08-2024"
)
```

---

## 🗄️ 데이터베이스 연결 모듈

### 3. `oracle_db.py` - Oracle Database 관리자

**목적**: Oracle Database 23ai 연결 풀 관리 및 쿼리 실행

**핵심 클래스**: `DatabaseManager`

**주요 기능**:
- **연결 풀 관리**: 효율적인 데이터베이스 연결 재사용
- **지갑 인증**: Oracle Autonomous Database 지갑 기반 인증
- **벡터 쿼리**: Oracle AI Vector Search 지원
- **트랜잭션 관리**: 안전한 데이터베이스 작업

**환경 변수**:
```bash
DB_USER=admin
DB_PASSWORD=your_password
DB_DSN=discovery_day_demo_high
TNS_ADMIN=/path/to/wallet
WALLET_LOCATION=/path/to/wallet
```

**사용 예시**:
```python
db_manager = DatabaseManager()
with db_manager.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM livelabs_workshops2")
    results = cursor.fetchall()
```

### 4. `mongo_utils.py` - MongoDB 유틸리티

**목적**: MongoDB 연결 및 JSON Duality View와의 데이터 동기화

**핵심 클래스**: `MongoManager`

**주요 기능**:
- **MongoDB 연결**: 안전한 인증 및 연결 관리
- **데이터 동기화**: Oracle JSON Duality View와 MongoDB 간 데이터 동기화
- **CRUD 작업**: 워크샵 및 사용자 데이터 관리
- **인덱스 관리**: 검색 성능 최적화

**환경 변수**:
```bash
MONGO_USER=your_username
MONGO_PASSWORD=your_password
MONGO_HOST=cluster.mongodb.net
MONGO_PORT=27017
```

---

## 🔍 벡터 검색 및 임베딩

### 5. `vector_search.py` - 벡터 검색 엔진

**목적**: 시맨틱 검색을 위한 벡터 검색 및 유사도 계산

**주요 기능**:
- **텍스트 임베딩**: 입력 텍스트를 벡터로 변환
- **유사도 검색**: Oracle AI Vector Search를 사용한 코사인 유사도 계산
- **결과 랭킹**: 유사도 점수 기반 결과 정렬
- **필터링**: 난이도, 카테고리별 검색 필터

**검색 프로세스**:
1. 사용자 쿼리를 벡터로 변환
2. Oracle Database에서 벡터 유사도 검색 실행
3. 결과를 유사도 점수순으로 정렬
4. 메타데이터와 함께 반환

**사용 예시**:
```python
from utils.vector_search import VectorSearchEngine

engine = VectorSearchEngine()
results = engine.search(
    query="Oracle Database tutorial",
    top_k=5,
    similarity_threshold=0.7
)
```

### 6. `oci_embedding.py` - OCI 임베딩 생성기

**목적**: Oracle Cloud Infrastructure의 Cohere 임베딩 모델을 사용한 벡터 생성

**주요 기능**:
- **배치 임베딩**: 여러 텍스트를 한 번에 벡터로 변환
- **모델 관리**: Cohere embed-v4.0 모델 사용
- **에러 처리**: API 호출 실패 시 재시도 로직
- **성능 최적화**: 배치 크기 및 타임아웃 관리

**지원 모델**:
- `cohere.embed-v4.0` (다국어 지원)
- `cohere.embed-english-v3.0` (영어 전용)

**사용 예시**:
```python
from utils.oci_embedding import get_embeddings, init_client

client = init_client(oci_config)
embeddings = get_embeddings(
    client, 
    compartment_id, 
    ["텍스트1", "텍스트2", "텍스트3"]
)
```

---

## 🌐 웹 스크래핑 및 파싱

### 7. `selenium_utils.py` - 웹 스크래핑 도구

**목적**: LiveLabs 웹사이트에서 워크샵 데이터를 수집하는 안티-디텍션 웹 스크래퍼

**핵심 클래스**: `SeleniumDriver`

**주요 기능**:
- **안티-디텍션**: 봇 탐지 회피를 위한 다양한 기법
- **동적 로딩**: JavaScript로 렌더링되는 콘텐츠 처리
- **에러 복구**: 네트워크 오류 및 요소 로딩 실패 시 재시도
- **성능 최적화**: 헤드리스 모드 및 리소스 로딩 제한

**안티-디텍션 기법**:
- 랜덤 User-Agent 설정
- 마우스 움직임 시뮬레이션
- 페이지 로딩 지연 시간 랜덤화
- 브라우저 핑거프린팅 방지

**사용 예시**:
```python
from utils.selenium_utils import SeleniumDriver

driver = SeleniumDriver(headless=True)
driver.setup_driver()
content = driver.get_page_content("https://livelabs.oracle.com")
driver.quit()
```

### 8. `workshop_parser.py` - 워크샵 파싱 도구

**목적**: 스크래핑된 HTML에서 워크샵 정보를 구조화된 데이터로 추출

**핵심 클래스**: `WorkshopParser`

**주요 기능**:
- **HTML 파싱**: BeautifulSoup을 사용한 DOM 요소 추출
- **데이터 정제**: 텍스트 클리닝 및 정규화
- **메타데이터 추출**: 제목, 설명, 난이도, 카테고리 등 추출
- **에러 처리**: 누락된 필드에 대한 기본값 설정

**추출 데이터**:
- 워크샵 ID 및 URL
- 제목 및 설명
- 작성자 및 생성일
- 난이도 및 카테고리
- 예상 소요시간
- 키워드 및 태그

---

## 🔗 모듈 간 의존성

### 의존성 그래프

```
ai_reasoner.py
├── genai_client.py
└── services.json (config)

vector_search.py
├── oci_embedding.py
└── oracle_db.py

selenium_utils.py
└── workshop_parser.py

mongo_utils.py
└── oracle_db.py (간접적)
```

### 핵심 워크플로우

#### 1. AI 추론 워크플로우
```
사용자 쿼리 → ai_reasoner.py → genai_client.py → Oracle GenAI → 서비스 선택
```

#### 2. 벡터 검색 워크플로우
```
검색 쿼리 → vector_search.py → oci_embedding.py → Oracle GenAI → oracle_db.py → 검색 결과
```

#### 3. 데이터 수집 워크플로우
```
웹사이트 → selenium_utils.py → workshop_parser.py → mongo_utils.py → MongoDB
```

---

## 💡 사용 예시

### AI 기반 워크샵 추천

```python
from utils.ai_reasoner import AIReasoner
from utils.vector_search import VectorSearchEngine
import json

# 1. 서비스 설정 로드
with open('config/services.json', 'r') as f:
    services_config = json.load(f)

# 2. AI 추론 엔진 초기화
reasoner = AIReasoner(services_config)

# 3. 사용자 쿼리 분석
user_query = "Python 초보자를 위한 데이터베이스 워크샵을 찾아줘"
analysis = reasoner.reason_about_query(user_query)

# 4. 벡터 검색 실행
if analysis['service'] == 'livelabs-semantic-search':
    search_engine = VectorSearchEngine()
    results = search_engine.search(
        query=user_query,
        top_k=5,
        difficulty_filter="BEGINNER"
    )
```

### 워크샵 데이터 수집 및 저장

```python
from utils.selenium_utils import SeleniumDriver
from utils.workshop_parser import WorkshopParser
from utils.mongo_utils import MongoManager
from utils.oracle_db import DatabaseManager

# 1. 웹 스크래핑
driver = SeleniumDriver()
driver.setup_driver()
html_content = driver.get_page_content("https://livelabs.oracle.com")

# 2. 데이터 파싱
parser = WorkshopParser()
workshops = parser.extract_workshops_beautifulsoup(html_content)

# 3. MongoDB 저장
mongo_manager = MongoManager()
mongo_manager.connect()
mongo_manager.insert_workshops(workshops)

# 4. Oracle Database 동기화
db_manager = DatabaseManager()
with db_manager.get_connection() as conn:
    # JSON Duality View를 통한 데이터 동기화
    pass
```

### 벡터 임베딩 생성 및 검색

```python
from utils.oci_embedding import init_client, get_embeddings
from utils.oracle_db import DatabaseManager
import oci

# 1. OCI 클라이언트 초기화
config = oci.config.from_file()
client = init_client(config)

# 2. 텍스트 임베딩 생성
texts = ["Oracle Database tutorial", "Python programming guide"]
embeddings = get_embeddings(client, config['tenancy'], texts)

# 3. Oracle Database에 저장
db_manager = DatabaseManager()
with db_manager.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE livelabs_workshops2 
        SET cohere4_embedding = :embedding 
        WHERE id = :workshop_id
    """, embedding=embeddings[0], workshop_id="123")
```

---

## 🔧 설정 및 환경 변수

### 필수 환경 변수

```bash
# Oracle Database
DB_USER=admin
DB_PASSWORD=your_password
DB_DSN=discovery_day_demo_high
TNS_ADMIN=/path/to/wallet
WALLET_LOCATION=/path/to/wallet

# MongoDB
MONGO_USER=your_username
MONGO_PASSWORD=your_password
MONGO_HOST=cluster.mongodb.net
MONGO_PORT=27017

# OCI 설정
OCI_CONFIG_FILE=~/.oci/config
OCI_PROFILE=DEFAULT
```

### 의존성 패키지

```bash
# 핵심 패키지
pip install oracledb pymongo oci selenium beautifulsoup4

# 추가 패키지
pip install python-dotenv webdriver-manager numpy
```

---

## 🚀 성능 최적화

### 연결 풀 관리
- **Oracle Database**: 2-5개 연결 풀 유지
- **MongoDB**: 연결 재사용 및 타임아웃 관리

### 캐싱 전략
- **임베딩 캐시**: 동일한 텍스트에 대한 벡터 재사용
- **검색 결과 캐시**: 자주 사용되는 쿼리 결과 캐싱

### 배치 처리
- **임베딩 생성**: 최대 100개 텍스트 배치 처리
- **데이터베이스 삽입**: 트랜잭션 단위 배치 처리

---

## 🔍 모니터링 및 로깅

### 로그 레벨
- **INFO**: 정상 작업 흐름
- **WARNING**: 복구 가능한 오류
- **ERROR**: 심각한 오류 및 예외

### 주요 메트릭
- **응답 시간**: API 호출 및 데이터베이스 쿼리 시간
- **성공률**: 작업 성공/실패 비율
- **리소스 사용량**: 메모리 및 CPU 사용률

---

## 📚 관련 문서

- [서비스 설정 문서](../config/README.md)
- [테스트 문서](../test/README.md)
- [Discovery Day 데모 설정](../DISCOVERY_DAY_DEMO_SETUP.md)
- [데이터베이스 스키마](../LIVELABS_DATABASE_SCHEMA.md)

---

**마지막 업데이트**: 2025-08-22  
**Python 버전**: 3.8+  
**주요 의존성**: Oracle Database 23ai, MongoDB, OCI GenAI
