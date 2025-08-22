# 🔧 LiveLabs AI Assistant 서비스 설정 문서

이 문서는 `services.json` 파일의 목적과 사용법을 설명합니다.

## 📋 목차
1. [개요](#개요)
2. [현재 사용 상태](#현재-사용-상태)
3. [설정 구조](#설정-구조)
4. [서비스별 상세 설정](#서비스별-상세-설정)
5. [사용하는 컴포넌트](#사용하는-컴포넌트)
6. [설정 관리](#설정-관리)

---

## 🎯 개요

`services.json`은 LiveLabs AI Assistant 시스템에서 **MCP (Model Context Protocol) 서비스들의 설정을 중앙 집중식으로 관리**하는 설정 파일입니다.

**주요 목적**:
- MCP 서비스들의 연결 정보 및 메타데이터 관리
- AI 추론 엔진(`AIReasoner`)이 적절한 서비스를 선택할 수 있도록 지원
- 서비스별 엔드포인트, 타임아웃, 사용 조건 등을 정의

---

## ✅ 현재 사용 상태

**활발히 사용 중** - 다음 컴포넌트들에서 참조됩니다:

### 사용하는 파일들:
1. **`streamlit_livelabs_rest_app.py`** - 메인 Streamlit 애플리케이션
2. **`utils/ai_reasoner.py`** - AI 추론 엔진
3. **`test/test_ai_workshop_planner.py`** - AI 워크샵 플래너 테스트
4. **`test/test_enhanced_workflow.py`** - 향상된 워크플로우 테스트

### 핵심 역할:
- **AI 추론 엔진**이 사용자 쿼리를 분석하여 적절한 MCP 서비스를 선택
- **서비스 디스커버리** 및 **동적 도구 로딩**
- **다단계 워크플로우** 실행 시 서비스 간 연계 지원

---

## 🏗️ 설정 구조

```json
{
  "mcpServers": {
    "서비스-키": {
      "transport": "http",
      "baseUrl": "서비스 URL",
      "headers": { "헤더 설정" },
      "timeout": 30000,
      "name": "서비스 표시명",
      "description": "서비스 설명",
      "use_when": ["사용 조건 배열"],
      "endpoints": { "엔드포인트 매핑" },
      "enabled": false,
      "tools_cache": null,
      "last_discovery": null
    }
  }
}
```

### 주요 필드 설명:

| 필드 | 타입 | 설명 |
|------|------|------|
| `transport` | string | 통신 프로토콜 (현재 "http") |
| `baseUrl` | string | 서비스의 기본 URL |
| `timeout` | number | 요청 타임아웃 (밀리초) |
| `name` | string | 서비스의 사람이 읽기 쉬운 이름 |
| `description` | string | 서비스 기능 설명 |
| `use_when` | array | AI가 이 서비스를 선택할 조건들 |
| `endpoints` | object | API 엔드포인트 매핑 |
| `enabled` | boolean | 서비스 활성화 상태 |
| `tools_cache` | object | 도구 캐시 (런타임에 설정) |
| `last_discovery` | string | 마지막 디스커버리 시간 |

---

## 🔗 서비스별 상세 설정

### 1. 시맨틱 검색 서비스 (`livelabs-semantic-search`)

**포트**: 8001  
**목적**: 벡터 임베딩을 사용한 워크샵 시맨틱 검색

```json
{
  "name": "LiveLabs Semantic Search",
  "description": "Search LiveLabs workshops using semantic similarity and vector embeddings",
  "use_when": [
    "workshop search", 
    "find courses", 
    "semantic search", 
    "similar content"
  ],
  "endpoints": {
    "search": "/search",
    "statistics": "/statistics", 
    "health": "/health",
    "tools": "/mcp/tools"
  }
}
```

**AI 선택 조건**:
- 워크샵 검색 요청
- 유사한 콘텐츠 찾기
- 시맨틱 검색이 필요한 경우

### 2. 자연어 쿼리 서비스 (`livelabs-nl-query`)

**포트**: 8002  
**목적**: Oracle SELECT AI를 사용한 자연어 데이터베이스 쿼리

```json
{
  "name": "Natural Language to SQL Query",
  "description": "Query database using natural language with Oracle SELECT AI",
  "use_when": [
    "natural language query", 
    "ask about users", 
    "database questions", 
    "user skills"
  ],
  "endpoints": {
    "query": "/users/search/nl",
    "health": "/health",
    "tools": "/mcp/tools"
  }
}
```

**AI 선택 조건**:
- 자연어로 데이터베이스 질문
- 사용자 정보 조회
- 스킬 관련 질문

### 3. 사용자 진도 관리 서비스 (`livelabs-user-progression`)

**포트**: 8003  
**목적**: 사용자 스킬 및 워크샵 완료 진도 관리

```json
{
  "name": "User Skills and Workshop Progression",
  "description": "Update and manage user skills and workshop completion tracking",
  "use_when": [
    "update skills", 
    "complete workshop", 
    "track progress", 
    "skill management"
  ],
  "endpoints": {
    "update_skills": "/skills/update",
    "complete_workshop": "/progression/update",
    "get_progress": "/progression/get",
    "add_skill": "/skills/update",
    "health": "/health",
    "tools": "/mcp/tools"
  }
}
```

**AI 선택 조건**:
- 스킬 업데이트
- 워크샵 완료 처리
- 학습 진도 추적

---

## 🤖 사용하는 컴포넌트

### 1. AI 추론 엔진 (`utils/ai_reasoner.py`)

**역할**: 사용자 쿼리를 분석하여 적절한 서비스 선택

```python
class AIReasoner:
    def __init__(self, services_config: Dict[str, Any]):
        self.services = services_config
    
    def reason_about_query(self, user_query: str) -> Dict[str, Any]:
        # services.json의 use_when 조건을 참조하여
        # 가장 적합한 서비스를 AI가 선택
```

**선택 로직**:
1. 사용자 쿼리 분석
2. `use_when` 조건과 매칭
3. 서비스 우선순위 결정
4. 다단계 워크플로우 계획

### 2. Streamlit 애플리케이션 (`streamlit_livelabs_rest_app.py`)

**역할**: 설정 로딩 및 서비스 초기화

```python
def load_services_config() -> Dict[str, Any]:
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'services.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# AI 추론 엔진 초기화
st.session_state.ai_reasoner = AIReasoner(st.session_state.services_config)
```

### 3. 테스트 파일들

**테스트에서의 활용**:
- AI 추론 로직 검증
- 서비스 선택 시나리오 테스트
- 다단계 워크플로우 테스트

---

## ⚙️ 설정 관리

### 서비스 활성화/비활성화

```json
{
  "enabled": false  // 현재 모든 서비스가 비활성화 상태
}
```

**활성화 방법**:
1. 해당 MCP 서비스 시작
2. `enabled: true`로 변경
3. 애플리케이션 재시작

### 동적 도구 디스커버리

```json
{
  "tools_cache": null,        // 런타임에 도구 정보 캐시
  "last_discovery": null      // 마지막 디스커버리 시간
}
```

**디스커버리 과정**:
1. 서비스 시작 시 `/mcp/tools` 엔드포인트 호출
2. 사용 가능한 도구 목록 캐시
3. AI 추론 시 캐시된 도구 정보 활용

### 타임아웃 설정

```json
{
  "timeout": 30000  // 30초 타임아웃
}
```

**권장 설정**:
- **시맨틱 검색**: 30초 (벡터 검색 시간 고려)
- **자연어 쿼리**: 30초 (AI 처리 시간 고려)
- **사용자 진도**: 15초 (단순 CRUD 작업)

---

## 🔄 워크플로우 예시

### 사용자 쿼리: "고정민의 스킬을 바탕으로 추천 워크샵을 찾아줘"

1. **AI 추론 엔진**이 쿼리 분석
2. **1단계**: `livelabs-nl-query` 선택 (사용자 스킬 조회)
3. **2단계**: `livelabs-semantic-search` 선택 (관련 워크샵 검색)
4. **결과 통합** 및 사용자에게 응답

### 설정 기반 서비스 선택

```python
# AI가 다음 조건들을 참조하여 서비스 선택:
"livelabs-nl-query": {
    "use_when": ["ask about users", "user skills"]  # 매칭!
}

"livelabs-semantic-search": {
    "use_when": ["workshop search", "find courses"]  # 매칭!
}
```

---

## 🚀 개발 및 운영 가이드

### 새로운 서비스 추가

1. **서비스 개발** 및 MCP 프로토콜 구현
2. **`services.json`에 설정 추가**:
   ```json
   "new-service": {
     "transport": "http",
     "baseUrl": "http://localhost:8004",
     "name": "New Service",
     "description": "Service description",
     "use_when": ["condition1", "condition2"],
     "endpoints": {
       "main": "/api/endpoint"
     },
     "enabled": true
   }
   ```
3. **AI 추론 로직** 업데이트 (필요시)
4. **테스트 케이스** 추가

### 설정 검증

```bash
# JSON 문법 검증
python -m json.tool config/services.json

# 서비스 연결 테스트
python test/test_mcp_connection.py
```

### 모니터링

```python
# 서비스 상태 확인
for service in services_config["mcpServers"]:
    health_url = f"{service['baseUrl']}/health"
    # 헬스 체크 수행
```

---

## 📚 관련 문서

- [Discovery Day 데모 설정](../DISCOVERY_DAY_DEMO_SETUP.md)
- [테스트 문서](../test/README.md)
- [MCP 설정 가이드](../doc/MCP_SETUP_GUIDE.md)
- [아키텍처 문서](../아키텍처_문서.md)

---

**마지막 업데이트**: 2025-08-22  
**설정 버전**: MCP Protocol 2024-11-05 호환
