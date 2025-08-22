# 🤖 LiveLabs AI Assistant - Oracle 워크샵 개인화 학습 플랫폼

Oracle LiveLabs 워크샵을 위한 종합적인 AI 기반 학습 관리 시스템입니다. 자연어 처리, 시맨틱 검색, 사용자 스킬 추적을 통해 개인화된 워크샵 추천과 학습 경로를 제공합니다.

## 🎯 주요 기능

### 🔍 **AI Workshop Planner**
- **개인화된 워크샵 추천**: 사용자의 스킬 레벨과 관심사를 기반으로 한 맞춤형 학습 콘텐츠 제안
- **자연어 쿼리**: "Python 관련 워크샵 찾아주세요", "내 스킬에 맞는 추천해주세요" 등 자연스러운 대화
- **다단계 AI 워크플로우**: NL-to-SQL → 시맨틱 검색 → 스킬 업데이트 → AI 응답 생성
- **한국어 지원**: 완전한 한국어 인터페이스와 응답

### 📊 **스킬 및 진도 관리**
- **사용자 프로필 관리**: 개인 정보, 스킬, 학습 이력 통합 관리
- **스킬 레벨 추적**: BEGINNER, INTERMEDIATE, ADVANCED 단계별 역량 관리
- **워크샵 완료 추적**: 진행 상황, 완료일, 평점(1-5) 기록
- **학습 분석**: 개인별 학습 패턴과 성과 분석

### 🔎 **고급 검색 시스템**
- **시맨틱 검색**: 벡터 임베딩을 활용한 의미 기반 워크샵 검색
- **자연어 데이터베이스 쿼리**: Oracle SELECT AI를 통한 직관적인 데이터 조회
- **실시간 검색**: 4,000+ 워크샵에서 즉시 검색 결과 제공

## 🏗️ 시스템 아키텍처

### **마이크로서비스 구조**
```
LiveLabs AI Assistant
├── 🌐 Streamlit 웹 인터페이스 (메인 앱)
├── 🔍 시맨틱 검색 서비스 (포트 8001)
├── 💬 자연어 쿼리 서비스 (포트 8002)
├── 📈 사용자 진도 관리 서비스 (포트 8003)
└── 🛠️ MCP 프로토콜 지원
```

### **기술 스택**
- **백엔드**: Python 3.13, FastAPI, Oracle Database, MongoDB
- **프론트엔드**: Streamlit, 커스텀 CSS, 실시간 업데이트
- **AI/ML**: Oracle GenAI, Cohere 임베딩, 벡터 검색
- **프로토콜**: MCP (Model Context Protocol), REST API
- **인프라**: 프로세스 관리, 로깅, 헬스 체크

## 🚀 빠른 시작

### 1. **환경 설정**
```bash
# 저장소 클론
git clone <repository-url>
cd livelabs

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. **환경 변수 설정**
```bash
# .env 파일 생성 (.env.example 참고)
cp .env.example .env

# 필수 설정값 입력
# - Oracle Database 연결 정보
# - MongoDB 연결 문자열
# - API 키 및 인증 정보
```

### 3. **서비스 시작**
```bash
# 모든 마이크로서비스 시작
./start_services.sh

# 개별 서비스 확인
curl http://localhost:8001/health  # 시맨틱 검색
curl http://localhost:8002/health  # 자연어 쿼리
curl http://localhost:8003/health  # 사용자 진도 관리
```

### 4. **웹 애플리케이션 실행**
```bash
# Streamlit 앱 시작
streamlit run streamlit_livelabs_rest_app.py

# 브라우저에서 http://localhost:8501 접속
```

## 💡 사용 방법

### **AI Workshop Planner와 대화하기**
```
사용자: "Python 초보자를 위한 워크샵 추천해주세요"
AI: 🎓 맞춤형 학습 경로 추천
    
    안녕하세요! 여러분의 AI Workshop Planner입니다.
    Python 초보자를 위한 워크샵을 찾았습니다!
    
    ### Getting Started with Python and Oracle Database
    - 난이도: BEGINNER
    - 카테고리: Database
    - 유사도: 92.5%
    - [학습 시작하기](https://livelabs.oracle.com/...)
```

### **주요 명령어 예시**
- `"내 스킬에 맞는 워크샵 추천해주세요"`
- `"사용자를 추가해주세요"`
- `"Machine Learning 관련 워크샵을 찾아주세요"`
- `"워크샵 완료를 기록해주세요"`
- `"Python 스킬을 INTERMEDIATE로 업데이트해주세요"`

## 📁 프로젝트 구조

```
livelabs/
├── MCP/                              # 마이크로서비스
│   ├── rest_livelabs_semantic_search.py      # 시맨틱 검색 API
│   ├── rest_livelabs_nl_query.py             # 자연어 쿼리 API
│   ├── rest_livelabs_user_skills_progression.py  # 스킬 관리 API
│   └── mcp_config.json                       # MCP 설정
├── utils/                            # 유틸리티 모듈
│   ├── genai_client.py              # Oracle GenAI 클라이언트
│   ├── mongo_utils.py               # MongoDB 유틸리티
│   ├── oracle_db.py                 # Oracle DB 매니저
│   └── vector_search.py             # 벡터 검색 엔진
├── config/
│   └── services.json                # 서비스 설정
├── test/                            # 테스트 스크립트
├── logs/                            # 서비스 로그
├── pids/                            # 프로세스 ID 파일
├── streamlit_livelabs_rest_app.py   # 메인 웹 애플리케이션
├── start_services.sh                # 서비스 시작 스크립트
├── stop_services.sh                 # 서비스 종료 스크립트
└── requirements.txt                 # 의존성 목록
```

## 🗄️ 데이터베이스 스키마

### **Oracle Database 테이블**
- **`LIVELABS_WORKSHOPS2`**: 워크샵 메타데이터, 벡터 임베딩
- **`LIVELABS_USERS`**: 사용자 프로필 정보
- **`USER_PROGRESS`**: 워크샵 완료 기록
- **`LIVELABS_USERS_SKILL`**: 사용자 스킬 레벨

### **JSON Duality Views**
- MongoDB 호환 인터페이스 제공
- 실시간 데이터 동기화
- RESTful API 지원

## 🔧 서비스 관리

### **서비스 시작/종료**
```bash
# 모든 서비스 시작
./start_services.sh

# 모든 서비스 종료
./stop_services.sh

# 개별 서비스 상태 확인
ps aux | grep "rest_livelabs"
```

### **로그 모니터링**
```bash
# 실시간 로그 확인
tail -f logs/semantic_search_*.log
tail -f logs/nl_query_*.log
tail -f logs/user_progression_*.log
```

### **헬스 체크**
```bash
# 모든 서비스 상태 확인
curl http://localhost:8001/health
curl http://localhost:8002/health  
curl http://localhost:8003/health
```

## 🧪 테스트

### **개별 서비스 테스트**
```bash
# 시맨틱 검색 테스트
python test/test_semantic_search.py

# 자연어 쿼리 테스트
python test/test_nl_query.py

# MCP 직접 테스트
python test/test_direct_mcp.py
```

### **통합 테스트**
```bash
# 전체 워크플로우 테스트
python test/test_ai_workshop_planner.py
```

## 🔍 문제 해결

### **일반적인 문제**
1. **포트 충돌**: `lsof -i :8001` 등으로 포트 사용 확인
2. **데이터베이스 연결**: 환경 변수와 네트워크 접근 확인
3. **임포트 오류**: Python 경로와 모듈 위치 확인
4. **서비스 시작 실패**: `logs/` 디렉토리의 로그 파일 확인

### **로그 분석**
- 타임스탬프가 포함된 서비스별 로그
- 구조화된 로깅 레벨 (INFO, ERROR, DEBUG)
- API 요청/응답 로깅
- 디버깅을 위한 오류 스택 트레이스

## 🚀 향후 개선 계획

### **예정된 기능**
- 향상된 오류 처리 및 재시도 로직
- 성능 모니터링 및 메트릭
- 자동화된 테스트 및 CI/CD
- Docker 컨테이너화
- 로드 밸런싱 및 스케일링

### **아키텍처 개선**
- 서비스 디스커버리 메커니즘
- 설정 관리 시스템
- 중앙화된 로깅 및 모니터링
- API 버전 관리 및 문서화
- 보안 강화 및 인증

## 📞 지원 및 기여

### **기술 지원**
- Oracle Cloud 관련 문제: Oracle Cloud Support
- Azure 관련 문제: Azure Help + Support
- 프로젝트 관련 문제: GitHub Issues

### **기여 방법**
1. Fork 저장소
2. Feature 브랜치 생성
3. 변경사항 커밋
4. Pull Request 제출

## 📄 라이선스

이 프로젝트는 Oracle LiveLabs 교육 목적으로 개발되었습니다.

---

**🤖 AI Workshop Planner와 함께 Oracle LiveLabs에서 효율적인 학습 여정을 시작하세요!**