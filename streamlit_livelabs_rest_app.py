#!/usr/bin/env python3
"""
LiveLabs Streamlit Application with REST API Integration
Uses FastAPI REST services instead of MCP protocol

LiveLabs AI 어시스턴트 - Streamlit 웹 애플리케이션
REST API 서비스들과 통합하여 워크샵 검색, 자연어 쿼리, 사용자 스킬 관리 기능 제공
"""

import streamlit as st
import requests
import json
import subprocess
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.genai_client import OracleGenAIClient

# 로깅 설정 - 애플리케이션 실행 과정 추적용
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Streamlit 페이지 설정 - 제목, 아이콘, 레이아웃 구성
st.set_page_config(
    page_title="LiveLabs AI Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS - 텍스트 가독성 향상을 위한 스타일링
st.markdown("""
<style>
    .stMarkdown {
        color: #262730 !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #262730 !important;
    }
    .stMarkdown p {
        color: #262730 !important;
    }
    .element-container .stMarkdown {
        background-color: rgba(255, 255, 255, 0.8);
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# REST API 서비스 설정 - 각 서비스별 엔드포인트, 도구, 사용 시나리오 정의
# SERVICES = {
#     "semantic_search": {
#         "name": "LiveLabs Semantic Search",
#         "description": "Find workshops by topic, technology, or content keywords. Use for: 'list workshops', 'find AI courses', 'show machine learning labs'. Does NOT consider user profiles.",
#         # ... rest of config
#     },
#     "nl_query": {
#         "name": "LiveLabs NL Query to Database", 
#         "description": "Get personalized recommendations based on user profiles and skills. Use when query mentions a specific person ('I am...', 'for Michael Chen') or asks about user skills/experience. Perfect for 'what should I learn?' questions.",
#         # ... rest of config
#     },
#     "user_skills_progression": {
#         "name": "LiveLabs User Skills Progression",
#         "description": "Update user skills or mark workshop completion. Use for: 'I completed workshop X', 'add Python skill', 'update my progress'. Only for data updates, not queries.",
SERVICES = {
    "semantic_search": {  # 시맨틱 검색 서비스 - 벡터 임베딩 기반 워크샵 검색
        "name": "LiveLabs Semantic Search",
        "description": "Search LiveLabs workshops using semantic similarity and vector embeddings",
        "mcp_service": "livelabs-semantic-search-service",
        "base_url": "http://localhost:8001",  # 포트 8001에서 실행
        "use_when": ["workshop search", "find courses", "semantic search", "similar content"],
        "endpoints": {
            "search": "/search",
            "statistics": "/statistics",
            "health": "/health"
        },
        "tools": {
            "search_livelabs_workshops": {
                "description": "Search for LiveLabs workshops using semantic similarity based on query text",
                "parameters": {
                    "query": {"type": "string", "required": True, "description": "Search query text"},
                    "top_k": {"type": "integer", "required": False, "description": "Number of results to return (default: 10)"}
                },
                "use_when": "User wants to find workshops or courses related to specific topics",
                "examples": ["find machine learning workshops", "search for database courses", "show me cloud computing labs"]
            }
        }
    },
    "nl_to_sql": {  # 자연어-SQL 변환 서비스 - Oracle SELECT AI 활용
        "name": "Natural Language to SQL Query",
        "description": "Query database using natural language with Oracle SELECT AI",
        "mcp_service": "livelabs-nl-query-service",
        "base_url": "http://localhost:8002",  # 포트 8002에서 실행
        "use_when": ["natural language query", "database questions", "user data lookup", "skills inquiry"],
        "endpoints": {
            "query": "/users/search/nl",
            "health": "/health"
        },
        "tools": {
            "query_database_nl": {
                "description": "Query the database using natural language with Oracle SELECT AI",
                "parameters": {
                    "natural_language_query": {"type": "string", "required": True, "description": "Natural language query about users, skills, or workshops"}
                },
                "use_when": "User asks questions about data in natural language",
                "examples": ["Who are the Python developers?", "Show me users with cloud skills", "What workshops has John completed?"]
            }
        }
    },
    "skill_progression": {  # 스킬 진행도 관리 서비스 - 사용자 스킬 업데이트 및 워크샵 완료 추적
        "name": "User Skills and Workshop Progression",
        "description": "Update and manage user skills and workshop completion tracking",
        "mcp_service": "livelabs-user-progression-service", 
        "base_url": "http://localhost:8003",  # 포트 8003에서 실행
        "use_when": ["update skills", "track progress", "complete workshop", "skill management"],
        "endpoints": {
            "update_skills": "/skills/update",
            "complete_workshop": "/progression/update",
            "get_progress": "/progression/get",
            "add_skill": "/skills/update",
            "health": "/health"
        },
        "tools": {
            "update_user_skills": {
                "description": "Update a user's skills or add new skills to their profile",
                "parameters": {
                    "user_id": {"type": "string", "required": True, "description": "User ID to update"},
                    "skills": {"type": "array", "required": True, "description": "List of skills to add or update"},
                    "skill_level": {"type": "string", "required": False, "default": "beginner", "description": "Skill level: beginner, intermediate, advanced"}
                },
                "use_when": "User wants to add or update their skills",
                "examples": ["add Python to my skills", "I learned machine learning", "update my Java level to advanced"]
            },
            "mark_workshop_complete": {
                "description": "Mark a workshop as completed for a user",
                "parameters": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "workshop_id": {"type": "string", "required": True, "description": "Workshop ID or name"},
                    "completion_date": {"type": "string", "required": False, "description": "Completion date (ISO format)"}
                },
                "use_when": "User reports completing a workshop or course",
                "examples": ["I completed the Docker workshop", "finished AI fundamentals course", "mark Oracle DB course as done"]
            }
        }
    }
}

def log_step(step_name: str, message: str):
    """실행 단계 로깅 - 타임스탬프와 함께 Streamlit 사이드바에 표시"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_message = f"🔍 {step_name}: {message}"
    logger.info(f"[{timestamp}] {log_message}")
    
    # Streamlit 사이드바에 로그 메시지 표시
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = []
    
    st.session_state.log_messages.append(f"[{timestamp}] {log_message}")
    
    # 최근 50개 메시지만 유지 (메모리 관리)
    if len(st.session_state.log_messages) > 50:
        st.session_state.log_messages = st.session_state.log_messages[-50:]

class RESTServiceManager:
    """REST API 서비스 관리자 - 서비스 시작/중지/상태 확인 담당"""
    
    def __init__(self):
        self.services = SERVICES  # 서비스 설정 정보
        self.processes = {}  # 실행 중인 프로세스 추적
        log_step("RESTServiceManager", "REST 서비스 매니저 초기화")
    
    def start_service(self, service_key: str) -> bool:
        """REST API 서비스 시작"""
        service = self.services[service_key]
        
        try:
            log_step("StartService", f"{service['name']} MCP 서비스 시작: {service['mcp_service']}")
            
            # 이미 실행 중인지 확인
            if service_key in self.processes and self.processes[service_key].poll() is None:
                log_step("StartService", f"{service['name']} 이미 실행 중")
                return True
            
            # 서비스 프로세스 시작
            process = subprocess.Popen(
                ["python", service["script"]],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.processes[service_key] = process
            
            # 시작 대기 시간 (서비스 초기화)
            time.sleep(2)
            
            # 서비스 상태 확인
            if self.check_health(service_key):
                log_step("StartService", f"✅ {service['name']} started successfully")
                return True
            else:
                log_step("StartService", f"❌ {service['name']} failed to start properly")
                return False
                
        except Exception as e:
            log_step("StartService", f"❌ Error starting {service['name']}: {e}")
            return False
    
    def stop_service(self, service_key: str) -> bool:
        """REST API 서비스 중지"""
        service = self.services[service_key]
        
        try:
            if service_key not in self.processes:
                log_step("StopService", f"{service['name']} 실행 중이지 않음")
                return True
            
            process = self.processes[service_key]
            
            if process.poll() is not None:
                log_step("StopService", f"{service['name']} 이미 중지됨")
                del self.processes[service_key]
                return True
            
            log_step("StopService", f"{service['name']} 중지 중")
            
            # 프로세스 종료 (정상 종료 시도)
            process.terminate()
            
            # 정상 종료 대기 (5초)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 필요시 강제 종료
                process.kill()
                process.wait()
            
            del self.processes[service_key]
            log_step("StopService", f"✅ {service['name']} 중지 완료")
            return True
            
        except Exception as e:
            log_step("StopService", f"❌ {service['name']} 중지 오류: {e}")
            return False
    
    def check_health(self, service_key: str) -> bool:
        """서비스 상태 확인 (헬스체크)"""
        service = self.services[service_key]
        
        try:
            response = requests.get(f"{service['base_url']}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_service_status(self, service_key: str) -> str:
        """서비스 상태 조회 (실행중/시작중/중지됨)"""
        if service_key in self.processes and self.processes[service_key].poll() is None:
            if self.check_health(service_key):
                return "running"  # 실행중
            else:
                return "starting"  # 시작중
        else:
            return "stopped"  # 중지됨

class AIReasoner:
    """AI 추론 엔진 - OCI GenAI를 사용한 도구 선택 및 쿼리 분석"""
    
    def __init__(self):
        log_step("AIReasoner", "AI 추론 엔진 초기화")
        self.genai_client = OracleGenAIClient()  # Oracle GenAI 클라이언트
    
    def reason_about_query(self, user_query: str) -> Dict[str, Any]:
        """사용자 쿼리 분석 및 적절한 서비스/액션 결정"""
        log_step("AIReasoner", f"쿼리 분석 중: '{user_query}'")
        
        # 각 단계별 사용할 모델 정의
        reasoning_model = "cohere.command-r-plus-08-2024"
        
        # 1단계: LLM에게 해야 할 일에 대해 생각하도록 요청
        thinking_prompt = self._create_thinking_prompt(user_query)
        thinking_result = self._ai_think_about_query(thinking_prompt, user_query, reasoning_model)
        
        # 2단계: 개선된 프롬프트로 서비스 결정
        decision_prompt = self._create_reasoning_prompt(user_query)
        ai_analysis = self._ai_analyze_query(decision_prompt, user_query, reasoning_model)
        
        # 결과 결합 및 모델 정보 추가
        ai_analysis["thinking_process"] = thinking_result
        ai_analysis["models_used"] = {
            "reasoning_model": reasoning_model,
            "summarization_model": "meta.llama-3.1-405b-instruct"
        }
        
        # LLM이 완전히 실패한 경우 기본 폴백 제공
        if ai_analysis.get("error") and not ai_analysis.get("service"):
            log_step("AIReasoner", "LLM 완전 실패, 기본 폴백 사용")
            query_lower = user_query.lower()
            if any(word in query_lower for word in ["i am", "my name", "what should i"]):
                ai_analysis = {
                    "service": "livelabs-user-skills-progression-service",
                    "tool": "query_user_skills_progression", 
                    "parameters": {"query": user_query},
                    "reasoning": "폴백: 개인 쿼리 감지됨",
                    "confidence": 0.5
                }
            else:
                ai_analysis = {
                    "service": "livelabs-semantic-search-service",
                    "tool": "search_livelabs_workshops",
                    "parameters": {"query": user_query}, 
                    "reasoning": "폴백: 일반 검색",
                    "confidence": 0.5
                }
            ai_analysis["thinking_process"] = thinking_result
        
        log_step("AIReasoner", f"AI 사고 과정: {thinking_result.get('thought_process', '사고 과정 없음')}")
        log_step("AIReasoner", f"AI 선택 서비스: {ai_analysis.get('service')}, 도구: {ai_analysis.get('tool')}")
        
        return ai_analysis
    
    def _apply_fallback_logic(self, user_query: str) -> Dict[str, Any]:
        """LLM이 서비스 선택에 실패했을 때 규칙 기반 폴백 로직 적용"""
        query_lower = user_query.lower()
        
        # 사용자가 자신의 이름을 언급하거나 개인적인 조언을 요청하는지 확인
        personal_indicators = ["i am", "my name is", "what should i", "recommend for me", "help me"]
        has_personal_context = any(indicator in query_lower for indicator in personal_indicators)
        
        # 워크샵/학습 관련 키워드 확인
        workshop_keywords = ["workshop", "learn", "course", "training", "skill", "big data", "ai", "machine learning", "python", "java"]
        is_workshop_related = any(keyword in query_lower for keyword in workshop_keywords)
        
        # 결정 로직
        if has_personal_context and is_workshop_related:
            # 개인 추천 - 먼저 nl_query를 사용하여 사용자 컨텍스트 가져오기
            return {
                "service": "nl_query",
                "action": "search_nl", 
                "reasoning": "폴백 로직: 사용자가 개인 추천을 요청함, nl_query로 사용자 프로필과 스킬 찾기",
                "confidence": 0.7,
                "parameters": {"natural_language_query": user_query},
                "requires_user_context": True
            }
        elif is_workshop_related:
            # 일반 워크샵 검색 - 시맨틱 검색 사용
            return {
                "service": "semantic_search",
                "action": "search",
                "reasoning": "Fallback logic: General workshop search query, using semantic search",
                "confidence": 0.7,
                "parameters": {"query": user_query},
                "requires_user_context": False
            }
        else:
            # 기타 모든 쿼리에 대해 기본적으로 시맨틱 검색 사용
            return {
                "service": "semantic_search", 
                "action": "search",
                "reasoning": "폴백 로직: 일반 쿼리에 대해 기본적으로 시맨틱 검색 사용",
                "confidence": 0.6,
                "parameters": {"query": user_query},
                "requires_user_context": False
            }
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any] | None:
        """임의의 텍스트에서 코드 펜스나 중괄호 균형을 사용하여 첫 번째 유효한 JSON 객체 추출"""
        import re
        # 1) JSON 코드 블록 시도
        fence = re.search(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fence:
            candidate = fence.group(1).strip()
            try:
                return json.loads(candidate)
            except Exception:
                pass
        # 2) 모든 코드 블록 시도
        fence_any = re.search(r"```\s*([\s\S]*?)\s*```", text)
        if fence_any:
            candidate = fence_any.group(1).strip()
            try:
                return json.loads(candidate)
            except Exception:
                pass
        # 3) 첫 번째 객체에 대한 중괄호 균형 맞추기
        start = text.find('{')
        if start != -1:
            brace_count = 0
            in_string = False
            esc = False
            for i in range(start, len(text)):
                ch = text[i]
                if in_string:
                    if esc:
                        esc = False
                    elif ch == '\\':
                        esc = True
                    elif ch == '"':
                        in_string = False
                else:
                    if ch == '"':
                        in_string = True
                    elif ch == '{':
                        brace_count += 1
                    elif ch == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            candidate = text[start:i+1]
                            try:
                                return json.loads(candidate)
                            except Exception:
                                break
        # 4) 모든 시도 실패
        return None
    
    def _create_reasoning_prompt(self, user_query: str) -> str:
        """SERVICES 설정을 사용하여 추론 프롬프트 생성"""
        services_desc = []
        for service_key, service_config in SERVICES.items():
            service_use_when = service_config.get("use_when", [])
            tool_list = []
            for tool_name, tool_info in service_config.get("tools", {}).items():
                tool_use_when = tool_info.get("use_when", "")
                tool_list.append(f"   - {tool_name}: {tool_info['description']} (Use when: {tool_use_when})")
            
            use_when_text = f" (Use when: {', '.join(service_use_when)})" if service_use_when else ""
            services_desc.append(f"{service_key}{use_when_text}:\n" + "\n".join(tool_list))
        
        services_text = "\n\n".join(services_desc)
        
        return f"""You are a service selector for LiveLabs workshop recommendations. 

AVAILABLE MCP SERVICES AND TOOLS:
{services_text}

USER QUERY: "{user_query}"

CRITICAL: For queries like "I am [Name], what should I learn for [topic]", you MUST include next_step.

DECISION RULES:
- Personalized queries with name → ALWAYS 2 steps: nl_to_sql first, then semantic_search
- General queries → single step with semantic_search
- Update/progression queries → use skill_progression service

REQUIRED OUTPUT FORMAT (include next_step for personalized queries):
{{"service": "nl_to_sql", "tool": "query_database_nl", "parameters": {{"natural_language_query": "Get all data for user [Name] including skills, experience levels, and workshop completion history"}}, "reasoning": "Get complete user profile first - filter by user, then let AI analyze", "next_step": {{"service": "semantic_search", "tool": "search_livelabs_workshops", "parameters": {{"query": "[topic] workshops"}}, "reasoning": "Find workshops matching topic - AI will match difficulty to user's actual skill level from step 1"}}}}

For general queries (no next_step):
{{"service": "semantic_search", "tool": "search_livelabs_workshops", "parameters": {{"query": "search term"}}, "reasoning": "Direct search"}}

RESPOND WITH VALID JSON FOR: "{user_query}"
"""
    
    

    def _ai_analyze_query(self, prompt: str, user_query: str, model_name: str) -> Dict[str, Any]:
        """LLM을 사용하여 쿼리 분석 및 서비스 선택"""
        log_step("AIAnalyzeQuery", f"LLM 호출하여 분석: '{user_query}'")
        
        response = self.genai_client.chat_json(
            prompt=prompt,
            model_name=model_name,
            temperature=0.0,
            max_tokens=300
        )
        
        if response["success"]:
            log_step("AIAnalyzeQuery", f"JSON 응답 성공적으로 받음: {response['json']}")
            return response["json"]
        else:
            log_step("AIAnalyzeQuery", f"GenAI 호출 실패: {response.get('error', '알 수 없는 오류')}")
            return {"error": response.get("error", "genai_failed"), "raw": response.get("raw_text", "")}

    def _create_thinking_prompt(self, user_query: str) -> str:
        """LLM이 해야 할 일에 대해 생각하도록 하는 프롬프트 생성"""
        schema = (
            '{"query_type":"personal_recommendation|general_search|update_request","user_mentioned":"string|null","needs_user_context":true,'
            '"thought_process":"string","recommended_approach":"string"}'
        )
        return f"""
You are an AI assistant analyzing a user's query to understand what information you need to give the best possible answer.

User Query: "{user_query}"

Think deeply about this query and what you need to do:

1. What is the user asking for?
2. What information would help give a better answer?
3. What's your reasoning strategy?

OUTPUT RULES (MANDATORY):
- Return ONLY a single JSON object on one line. No markdown, no prose, no code fences.
- Use only double quotes for all keys and strings.
- Escape any internal double quotes as \".
- Keep fields short to avoid long texts.

Respond EXACTLY with this JSON schema (no extra fields):
{schema}
"""

    def _create_decision_prompt(self, user_query: str, thinking_result: Dict) -> str:
        """Create service selection prompt based on thinking analysis"""
        
        # Build service descriptions from SERVICES configuration
        services_info = []
        for service_key, service_config in SERVICES.items():
            endpoints_list = []
            for action, endpoint in service_config.get("endpoints", {}).items():
                endpoints_list.append(f"   - {action}: {endpoint}")
            
            service_info = f"""**{service_key}** ({service_config['name']}):
   Description: {service_config['description']}
   Port: {service_config['port']}
   Available actions:
{chr(10).join(endpoints_list)}"""
            services_info.append(service_info)
        
        services_description = "\n\n".join(services_info)
        decision_schema = (
            '{"service":"service_key","action":"endpoint_key","reasoning":"string","confidence":0.85,'
            '"parameters":{"key":"value"}}'
        )
        return f"""
Based on your thinking analysis, now select the appropriate service and action.

**User Query:** "{user_query}"

**Your Previous Thinking:** {thinking_result}

**Available Services:**

{services_description}

**Now decide:** Based on your thinking above, which service should you call first?

**Response Format:**
{decision_schema}
"""

    def _ai_think_about_query(self, prompt: str, user_query: str, model_name: str) -> Dict[str, Any]:
        """LLM이 먼저 해야 할 일에 대해 생각하도록 함"""
        log_step("AIThink", f"사고 분석 진행 중: '{user_query}'")
        
        response = self.genai_client.chat_json(
            prompt=prompt,
            model_name=model_name, 
            temperature=0.0,
            max_tokens=300
        )
        
        if response["success"]:
            log_step("AIThink", f"사고 JSON 성공적으로 받음: {response['json']}")
            return response["json"]
        else:
            log_step("AIThink", f"사고 GenAI 호출 실패: {response.get('error', '알 수 없는 오류')}")
            return {"error": response.get("error", "thinking_genai_failed"), "raw": response.get("raw_text", "")}

def call_rest_api(service_key: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """서비스에 REST API 호출 수행"""
    service = SERVICES[service_key]
    
    try:
        log_step("CallRESTAPI", f"{service['name']}.{action} 호출, 매개변수: {params}")
        
        # 도구 이름을 엔드포인트 이름으로 매핑
        tool_to_endpoint_map = {
            "search_livelabs_workshops": "search",
            "query_database_nl": "query", 
            "update_user_skills": "update_skills",
            "mark_workshop_complete": "complete_workshop",
            "get_user_progress": "get_progress"
        }
        
        # 실제 엔드포인트 이름 가져오기
        endpoint_name = tool_to_endpoint_map.get(action, action)
        
        # 서비스 엔드포인트에서 URL 구성
        if endpoint_name in service.get("endpoints", {}):
            url = f"{service['base_url']}{service['endpoints'][endpoint_name]}"
        else:
            log_step("CallRESTAPI", f"❌ 알 수 없는 액션: {action} ({endpoint_name}으로 매핑됨)")
            return {"success": False, "error": f"알 수 없는 액션: {action} for service {service['name']}"}
        
        log_step("CallRESTAPI", f"🌐 요청 URL: {url}")
        
        # 요청 수행
        response = None
        if params:
            log_step("CallRESTAPI", f"📤 JSON 페이로드와 함께 POST 요청")
            try:
                response = requests.post(url, json=params, timeout=30)
                log_step("CallRESTAPI", f"📥 POST 응답: HTTP {response.status_code}")
            except Exception as post_error:
                log_step("CallRESTAPI", f"⚠️ POST 실패, GET 시도: {post_error}")
                try:
                    response = requests.get(url, params=params, timeout=30)
                    log_step("CallRESTAPI", f"📥 GET 응답: HTTP {response.status_code}")
                except Exception as get_error:
                    log_step("CallRESTAPI", f"❌ POST와 GET 모두 실패: {get_error}")
                    return {"success": False, "error": f"요청 실패: POST({post_error}), GET({get_error})"}
        else:
            log_step("CallRESTAPI", f"📤 GET 요청 (매개변수 없음)")
            response = requests.get(url, timeout=30)
            log_step("CallRESTAPI", f"📥 GET 응답: HTTP {response.status_code}")
        
        # 응답 처리
        if response.status_code == 200:
            try:
                result = response.json()
                log_step("CallRESTAPI", f"✅ {service['name']}.{action} 성공적으로 완료")
                log_step("CallRESTAPI", f"📊 응답 데이터 키: {list(result.keys()) if isinstance(result, dict) else '딕셔너리 아님'}")
                
                # 응답에 대한 주요 정보 로그
                if isinstance(result, dict):
                    if "success" in result:
                        log_step("CallRESTAPI", f"🎯 API 성공: {result.get('success')}")
                    if "results" in result:
                        log_step("CallRESTAPI", f"📋 결과 개수: {len(result.get('results', []))}")
                    if "total_found" in result:
                        log_step("CallRESTAPI", f"🔍 총 발견: {result.get('total_found')}")
                    if "error" in result and result.get("error"):
                        log_step("CallRESTAPI", f"⚠️ API 오류 반환: {result.get('error')}")
                
                # 명시적인 성공 필드가 없으면 성공으로 표시
                if "success" not in result:
                    result["success"] = True
                    log_step("CallRESTAPI", f"🔧 응답에 success=True 추가")
                
                return result
            except json.JSONDecodeError as e:
                error_msg = f"잘못된 JSON 응답: {e}"
                log_step("CallRESTAPI", f"❌ JSON 디코드 오류: {error_msg}")
                log_step("CallRESTAPI", f"📄 원시 응답: {response.text[:500]}...")
                return {"success": False, "error": error_msg}
        else:
            error_msg = f"HTTP {response.status_code}: {response.text[:200]}..."
            log_step("CallRESTAPI", f"❌ {service['name']}.{action} 실패: {error_msg}")
            return {"success": False, "error": error_msg}
        
    except Exception as e:
        error_msg = f"요청 실패: {str(e)}"
        log_step("CallRESTAPI", f"❌ {service['name']}.{action} 오류: {error_msg}")
        return {"success": False, "error": error_msg}

def generate_chatbot_response(user_query: str) -> str:
    """AI 추론과 REST API 호출을 사용하여 챗봇 응답 생성"""
    log_step("ChatbotResponse", f"사용자 쿼리 처리 중: '{user_query}'")
    
    # Create reasoning display container
    reasoning_container = st.container()
    
    with reasoning_container:
        st.markdown("### 🧠 AI Reasoning Process")
        
        # Step 1: Query Analysis
        with st.expander("Step 1: Query Analysis", expanded=True):
            st.markdown(f"**User Query:** `{user_query}`")
            st.markdown("**Analysis:** Sending query to LLM for intent analysis...")
    
    # Initialize AI reasoner
    if "ai_reasoner" not in st.session_state:
        st.session_state.ai_reasoner = AIReasoner()
    
    # Step 2: AI Analysis
    with reasoning_container:
        with st.expander("Step 2: AI Service Selection", expanded=True):
            st.markdown("**LLM Analysis:** Oracle GenAI analyzing query...")
            
            # Show the reasoning process
            with st.spinner("🤖 AI is analyzing your query..."):
                ai_analysis = st.session_state.ai_reasoner.reason_about_query(user_query)
            
            # Update with actual model info after getting results
            if ai_analysis.get('models_used'):
                reasoning_model = ai_analysis['models_used'].get('reasoning_model', 'Unknown')
                st.markdown(f"**Model Used:** `{reasoning_model}`")
            
            # Display detailed AI reasoning
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Confidence", f"{ai_analysis.get('confidence', 0.0):.2f}")
                st.markdown(f"**Selected Service:** `{ai_analysis.get('service')}`")
                st.markdown(f"**Selected Action:** `{ai_analysis.get('tool') or ai_analysis.get('action')}`")
            
            with col2:
                if ai_analysis.get('parameters'):
                    st.markdown("**Extracted Parameters:**")
                    st.json(ai_analysis.get('parameters', {}))
            
            st.markdown("**AI Reasoning:**")
            st.info(ai_analysis.get('reasoning', 'No reasoning provided'))
    
    # Step 3: Multi-Step Workflow Execution
    with reasoning_container:
        with st.expander("Step 3: Multi-Step Workflow Execution", expanded=True):
            st.markdown("**Executing multi-step workflow...**")
            
            # Execute the multi-step workflow and get all results
            response, final_result, ai_analysis = generate_chatbot_response_with_data(user_query)
            
            # Display each step
            if final_result.get("steps"):
                for step_info in final_result["steps"]:
                    step_num = step_info["step"]
                    service = step_info["service"]
                    action = step_info["action"]
                    result = step_info["result"]
                    
                    st.markdown(f"### Step {step_num}: {service}.{action}")
                    st.markdown(f"**Parameters:** `{step_info['parameters']}`")
                    
                    if result.get("success"):
                        st.success(f"✅ Step {step_num} successful!")
                        if "results" in result:
                            st.markdown(f"**Results found:** {len(result.get('results', []))}")
                        if "total_found" in result:
                            st.markdown(f"**Total found:** {result.get('total_found')}")
                    else:
                        st.error(f"❌ Step {step_num} failed: {result.get('error', 'Unknown error')}")
                    
                    st.divider()
            
            # Show workflow summary
            st.markdown(f"**Workflow Type:** {final_result.get('workflow_type', 'unknown')}")
            st.markdown(f"**Total Steps:** {final_result.get('total_steps', 0)}")
            st.markdown(f"**Overall Success:** {'✅' if final_result.get('success') else '❌'}")
            
            return response
    
    # Step 4: Response Formatting
    with reasoning_container:
        with st.expander("Step 4: Response Formatting", expanded=True):
            st.markdown("**LLM will format the response based on the API results...**")
            
            # Let LLM format the response
            st.markdown(f"**API Response Status:** {'✅ Success' if result.get('success') else '❌ Error'}")
            st.markdown(f"**Raw API Response Keys:** `{list(result.keys()) if isinstance(result, dict) else 'Not a dict'}`")
            
            # Simple response - let the LLM in the final results handle formatting
            if result.get("success"):
                response = f"Query: {user_query}\n\nAPI Results:\n{json.dumps(result, indent=2)}"
            else:
                response = f"Error processing query: {user_query}\nError: {result.get('error', 'Unknown error')}"
    
    log_step("ChatbotResponse", "Response generated successfully")
    return response

def generate_chatbot_response_with_data(user_query: str) -> tuple[str, Dict[str, Any], Dict[str, Any]]:
    """Generate chatbot response and return the raw data for LLM formatting"""
    log_step("ChatbotResponse", f"Processing user query: '{user_query}'")
    
    # Create reasoning display container
    reasoning_container = st.container()
    
    with reasoning_container:
        st.markdown("### 🧠 AI Reasoning Process")
        
        # Step 1: Query Analysis
        with st.expander("Step 1: Query Analysis", expanded=True):
            st.markdown(f"**User Query:** `{user_query}`")
            st.markdown("**Analysis:** Sending query to LLM for intent analysis...")
    
    # Initialize AI reasoner
    if "ai_reasoner" not in st.session_state:
        st.session_state.ai_reasoner = AIReasoner()
    
    # Step 2: AI Analysis
    with reasoning_container:
        with st.expander("Step 2: AI Service Selection", expanded=True):
            st.markdown("**LLM Analysis:** Two-step reasoning with Oracle GenAI...")
            
            # Show the reasoning process
            with st.spinner("🤖 AI is doing detailed reasoning analysis..."):
                ai_analysis = st.session_state.ai_reasoner.reason_about_query(user_query)
            
            # Show model information dynamically
            if ai_analysis.get('models_used'):
                reasoning_model = ai_analysis['models_used'].get('reasoning_model', 'Unknown')
                summarization_model = ai_analysis['models_used'].get('summarization_model', 'Unknown')
                st.markdown(f"**Models Used:** Reasoning: `{reasoning_model}` | Summarization: `{summarization_model}`")
            
            # Debug: Show raw AI analysis
            st.markdown("**🔍 Debug: Raw AI Analysis Result**")
            st.json(ai_analysis)
            
            # Display thinking process first
            if ai_analysis.get('thinking_process'):
                st.markdown("**🧠 Step 2a: LLM's Thinking Process**")
                thinking = ai_analysis['thinking_process']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Query Type", thinking.get('query_type', 'Unknown'))
                with col2:
                    st.metric("User Mentioned", thinking.get('user_mentioned', 'None') or 'None')
                with col3:
                    st.metric("Needs Context", "Yes" if thinking.get('needs_user_context') else "No")
                
                st.markdown("**LLM's Step-by-Step Thinking:**")
                st.info(thinking.get('thought_process', 'No thinking provided'))
                
                st.markdown("**LLM's Recommended Approach:**")
                st.success(thinking.get('recommended_approach', 'No approach specified'))
                
                st.divider()
            
            # Display final service selection
            st.markdown("**🎯 Step 2b: Final Service Selection**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Confidence", f"{ai_analysis.get('confidence', 0.0):.2f}")
                st.markdown(f"**Selected Service:** `{ai_analysis.get('service')}`")
                st.markdown(f"**Selected Action:** `{ai_analysis.get('tool') or ai_analysis.get('action')}`")
            
            with col2:
                if ai_analysis.get('parameters'):
                    st.markdown("**Extracted Parameters:**")
                    st.json(ai_analysis.get('parameters', {}))
            
            st.markdown("**Service Selection Reasoning:**")
            st.info(ai_analysis.get('reasoning', 'No reasoning provided'))
    
    # Step 3: API Call Execution
    with reasoning_container:
        with st.expander("Step 3: API Call Execution", expanded=True):
            service_key = ai_analysis.get("service")
            action = ai_analysis.get("tool") or ai_analysis.get("action")
            parameters = ai_analysis.get("parameters", {})
            
            # Validate that AI reasoner provided valid service and action
            if not service_key or not action:
                st.error("❌ AI reasoner failed to identify a valid service and action for your query.")
                st.markdown("**Debug Info:**")
                st.markdown(f"- Service: `{service_key}`")
                st.markdown(f"- Action: `{action}`")
                st.markdown("**Suggestion:** Try rephrasing your question to be more specific about what you want to do.")
                return "I couldn't determine which service to use for your request. Please try rephrasing your question.", {}, ai_analysis
            
            # Validate service exists
            if service_key not in SERVICES:
                st.error(f"❌ Unknown service: `{service_key}`")
                st.markdown(f"**Available services:** {list(SERVICES.keys())}")
                return f"Unknown service: {service_key}", {}, ai_analysis
            
            st.markdown(f"**Making API Call:** `{service_key}.{action}`")
            st.markdown(f"**Parameters:** `{parameters}`")
            
    
    # Step 3: Validate and make API call
    if not service_key or not action:
        error_msg = "AI reasoner failed to identify a valid service and action"
        log_step("ChatbotResponse", f"❌ {error_msg}")
        return error_msg, {"success": False, "error": error_msg}, ai_analysis
    
    if service_key not in SERVICES:
        error_msg = f"Unknown service: {service_key}"
        log_step("ChatbotResponse", f"❌ {error_msg}")
        return error_msg, {"success": False, "error": error_msg}, ai_analysis
    
    # Execute multi-step workflow
    all_results = []
    current_step = ai_analysis
    step_count = 0
    max_steps = 3
    
    while current_step and step_count < max_steps:
        step_count += 1
        step_service = current_step.get("service")
        step_action = current_step.get("tool") or current_step.get("action")
        step_params = current_step.get("parameters", {})
        
        log_step("ChatbotResponse", f"Executing step {step_count}: {step_service}.{step_action}")
        
        # Make API call for this step
        step_result = call_rest_api(step_service, step_action, step_params)
        
        all_results.append({
            "step": step_count,
            "service": step_service,
            "action": step_action,
            "parameters": step_params,
            "result": step_result,
            "reasoning": current_step.get("reasoning", "")
        })
        
        # Debug: Show what AI actually returned
        log_step("ChatbotResponse", f"AI analysis keys: {list(current_step.keys())}")
        if "next_step" in current_step:
            log_step("ChatbotResponse", f"Next step found: {current_step['next_step']}")
        else:
            log_step("ChatbotResponse", f"No 'next_step' key in AI response")
        
        # Check for next step and enhance it with previous step results
        if step_result.get("success") and current_step.get("next_step"):
            next_step = current_step.get("next_step").copy()
            
            # If next step is semantic search, enhance query with comprehensive context
            if next_step.get("service") == "semantic_search":
                
                # Build comprehensive context from original user query + all previous step results
                context_parts = [f"Original user inquiry: {user_query}"]
                
                # Add information from all previous steps
                for prev_step in all_results:
                    step_result_data = prev_step["result"]
                    if step_result_data.get("success"):
                        # Add user profile information from NL-to-SQL steps
                        if prev_step["service"] == "nl_to_sql":
                            if step_result_data.get("explanation"):
                                context_parts.append(f"User profile: {step_result_data['explanation']}")
                            if step_result_data.get("users"):
                                for user in step_result_data["users"]:
                                    if user.get("skills"):
                                        context_parts.append(f"User skills: {', '.join(user['skills'][:5])}")
                                    if user.get("experience_level"):
                                        context_parts.append(f"Experience level: {user['experience_level']}")
                                    if user.get("completed_workshops"):
                                        context_parts.append(f"Completed workshops: {len(user['completed_workshops'])} workshops")
                        
                        # Add any other relevant step results
                        elif prev_step["service"] == "semantic_search" and step_result_data.get("results"):
                            context_parts.append(f"Previous search found {len(step_result_data['results'])} workshops")
                
                # Combine original query with comprehensive context
                original_query = next_step.get("parameters", {}).get("query", "")
                comprehensive_query = f"{original_query}. Context: {' | '.join(context_parts)}"
                
                next_step["parameters"]["query"] = comprehensive_query
                log_step("ChatbotResponse", f"Enhanced query with full context: {comprehensive_query[:200]}...")
            
            current_step = next_step
            log_step("ChatbotResponse", f"Executing next step: {current_step.get('service')}.{current_step.get('tool')}")
        else:
            if current_step.get("next_step"):
                log_step("ChatbotResponse", f"Step {step_count} failed, skipping next step")
            else:
                log_step("ChatbotResponse", f"No next step specified - workflow complete")
            break
    
    # Combine results
    final_result = {
        "success": all(step["result"].get("success", False) for step in all_results),
        "workflow_type": "multi_step" if len(all_results) > 1 else "single_step", 
        "total_steps": len(all_results),
        "steps": all_results
    }
    
    # Generate response with LLM formatting
    if final_result.get("success"):
        response = format_response_with_llm(user_query, final_result, ai_analysis)
    else:
        response = f"Error processing query: {user_query}\nSome steps failed"
    
    log_step("ChatbotResponse", f"Workflow completed: {len(all_results)} steps")
    return response, final_result, ai_analysis


def format_response_with_llm(user_query: str, api_result: Dict[str, Any], ai_analysis: Dict[str, Any]) -> str:
    """Use LLM to format the final response using comprehensive data from all workflow steps"""
    try:
        genai_client = OracleGenAIClient()

        # Build comprehensive context from all steps
        comprehensive_context = {
            "user_query": user_query,
            "ai_analysis": ai_analysis,
            "workflow_type": api_result.get("workflow_type", "unknown"),
            "total_steps": api_result.get("total_steps", 0),
            "all_step_data": [],
            "final_result": api_result
        }
        
        # Collect data from each step
        if api_result.get("steps"):
            for step_info in api_result["steps"]:
                step_data = {
                    "step_number": step_info.get("step"),
                    "service": step_info.get("service"),
                    "action": step_info.get("action"),
                    "parameters": step_info.get("parameters"),
                    "result": step_info.get("result"),
                    "success": step_info.get("result", {}).get("success", False)
                }
                comprehensive_context["all_step_data"].append(step_data)

        # Create formatting prompt with comprehensive context
        formatting_prompt = f"""
You are an AI assistant helping users with LiveLabs workshop recommendations and database queries.

**User's Original Query:** "{user_query}"

**AI Analysis & Reasoning:** {ai_analysis.get('reasoning', 'No reasoning provided')}

**Workflow Summary:**
- Type: {comprehensive_context['workflow_type']}
- Total Steps: {comprehensive_context['total_steps']}
- Overall Success: {api_result.get('success', False)}

**Complete Step-by-Step Data:**
{json.dumps(comprehensive_context['all_step_data'], indent=2)}

**Final Aggregated Results:**
{json.dumps(api_result, indent=2)}

**Your Task:**
Analyze ALL step data and create a comprehensive, personalized response. Use information from EVERY step:

**Step 1 Analysis (User Profile):**
- Extract user's current skills, experience levels, and completed workshops
- Identify knowledge gaps and learning progression

**Step 2 Analysis (Workshop Search):**
- Review all found workshops and their difficulty levels
- Match workshops to user's skill level from Step 1

**Integration Requirements:**
1. **SYNTHESIZE ALL STEPS** - Combine user profile data with workshop search results
2. **PERSONALIZED MATCHING** - Explain why each workshop fits the user's current level
3. **LEARNING PATH** - Show progression from user's current state to recommended workshops
4. **COMPREHENSIVE REASONING** - Use both user data AND workshop data to justify recommendations

**Response Format:**
1. **User Profile Summary** (from Step 1 data)
2. **Recommended Learning Path** (synthesized from both steps)
3. **Specific Workshop Recommendations** with personalized reasoning
4. **Next Steps** for the user's learning journey

**CRITICAL RULES:**
- **USE ALL STEP DATA**: Don't ignore any step's information
- **CONNECT THE DOTS**: Show how user profile leads to specific workshop recommendations
- **PERSONALIZED REASONING**: Explain why each recommendation fits this specific user
- **INCLUDE URLs**: Format as [Workshop Title](URL) when available
- **NO HALLUCINATION**: Only use actual data from the steps

**LANGUAGE REQUIREMENT:**
Respond in Korean (한국어). Use natural, professional Korean language throughout the entire response.

Create a comprehensive response that uses ALL available step information:
"""

        response = genai_client.chat(
            prompt=formatting_prompt,
            model_name="meta.llama-4-scout-17b-16e-instruct",
            temperature=0.3,
            max_tokens=1000
        )
        
        if response["success"]:
            log_step("FormatResponse", f"LLM formatted response successfully")
            return response["text"]
        else:
            log_step("FormatResponse", f"LLM formatting failed: {response.get('error', 'Unknown error')}")
            # Fallback to simple formatting
            return f"**Results for:** {user_query}\n\n```json\n{json.dumps(api_result, indent=2)}\n```"

    except Exception as e:
        log_step("FormatResponse", f"LLM formatting failed: {str(e)}")
        # Fallback to simple formatting
        return f"**Results for:** {user_query}\n\n```json\n{json.dumps(api_result, indent=2)}\n```"

def main():
    """Main Streamlit application"""
    log_step("MainApp", "Starting main application")
    
    # Initialize session state
    if "rest_service_manager" not in st.session_state:
        st.session_state.rest_service_manager = RESTServiceManager()
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Main title
    st.title("🔬 LiveLabs AI Assistant")
    st.markdown("*Powered by REST APIs and OCI Generative AI*")
    
    # Sidebar for service management
    with st.sidebar:
        st.header("🔧 REST API Services")
        
        for service_key, service in SERVICES.items():
            st.subheader(f"🔌 {service['name']}")
            st.markdown(f"*{service['description']}*")
            st.markdown(f"**MCP Service:** {service['mcp_service']}")
            
            # Service status
            status = st.session_state.rest_service_manager.get_service_status(service_key)
            if status == "running":
                st.success("✅ Running")
            elif status == "starting":
                st.warning("🔄 Starting...")
            else:
                st.error("❌ Stopped")
            
            # Control buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("▶️ Start", key=f"start_{service_key}"):
                    with st.spinner(f"Starting {service['name']}..."):
                        success = st.session_state.rest_service_manager.start_service(service_key)
                        if success:
                            st.success("Started!")
                        else:
                            st.error("Failed to start")
                        st.rerun()
            
            with col2:
                if st.button("⏹️ Stop", key=f"stop_{service_key}"):
                    with st.spinner(f"Stopping {service['name']}..."):
                        success = st.session_state.rest_service_manager.stop_service(service_key)
                        if success:
                            st.success("Stopped!")
                        else:
                            st.error("Failed to stop")
                        st.rerun()
            
            with col3:
                if st.button("🔍 Test", key=f"test_{service_key}"):
                    with st.spinner(f"Testing {service['name']}..."):
                        healthy = st.session_state.rest_service_manager.check_health(service_key)
                        if healthy:
                            st.success("Healthy!")
                        else:
                            st.error("Not responding")
            
            st.divider()
        
        # Quick actions
        st.header("⚡ Quick Actions")
        
        if st.button("🚀 Start All Services"):
            log_step("UserAction", "User clicked start all services")
            with st.spinner("Starting all services..."):
                for service_key in SERVICES.keys():
                    st.session_state.rest_service_manager.start_service(service_key)
                st.success("All services started!")
                st.rerun()
        
        if st.button("🛑 Stop All Services"):
            log_step("UserAction", "User clicked stop all services")
            with st.spinner("Stopping all services..."):
                for service_key in SERVICES.keys():
                    st.session_state.rest_service_manager.stop_service(service_key)
                st.success("All services stopped!")
                st.rerun()
        
        # Logs section
        st.header("📋 Activity Logs")
        if "log_messages" in st.session_state and st.session_state.log_messages:
            log_container = st.container()
            with log_container:
                for log_msg in st.session_state.log_messages[-10:]:  # Show last 10
                    st.text(log_msg)
        else:
            st.text("No activity yet...")
    
    # Main chat interface
    st.header("💬 AI Chat Assistant")
    
    # Chat input
    user_input = st.chat_input("Ask me about LiveLabs workshops, users, or skills...")
    
    if user_input:
        log_step("UserInput", f"User asked: '{user_input}'")
        
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Show detailed reasoning process
        st.markdown("---")
        st.markdown("## 🧠 AI Reasoning & Processing")
        
        # Execute multi-step workflow and show results
        response, api_result, ai_analysis = generate_chatbot_response_with_data(user_input)
        
        # Show multi-step workflow execution details
        if api_result and api_result.get("steps"):
            st.markdown("### 🔄 Multi-Step Workflow Execution")
            
            for step_info in api_result["steps"]:
                step_num = step_info["step"]
                service = step_info["service"]
                action = step_info["action"]
                result = step_info["result"]
                
                with st.expander(f"Step {step_num}: {service}.{action}", expanded=True):
                    st.markdown(f"**Service:** {service}")
                    st.markdown(f"**Action:** {action}")
                    st.markdown(f"**Parameters:** `{step_info['parameters']}`")
                    
                    if result.get("success"):
                        st.success(f"✅ Step {step_num} completed successfully!")
                        
                        # Show specific results for each service type
                        if service == "nl_to_sql" and "users" in result:
                            st.markdown(f"**Users found:** {result.get('total_found', 0)}")
                            if result.get("sql_query"):
                                st.code(result["sql_query"], language="sql")
                        
                        elif service == "semantic_search" and "results" in result:
                            st.markdown(f"**Workshops found:** {len(result.get('results', []))}")
                            
                            # Show first few workshop results
                            workshops = result.get("results", [])[:3]  # Show first 3
                            for i, workshop in enumerate(workshops, 1):
                                st.markdown(f"**{i}. {workshop.get('title', 'Unknown Workshop')}**")
                                if workshop.get('url'):
                                    st.markdown(f"🔗 [View Workshop]({workshop['url']})")
                                if workshop.get('description'):
                                    st.markdown(f"📝 {workshop['description'][:100]}...")
                                st.markdown("---")
                    else:
                        st.error(f"❌ Step {step_num} failed: {result.get('error', 'Unknown error')}")
            
            # Workflow summary
            st.markdown("### 📊 Workflow Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Steps", api_result.get("total_steps", 0))
            with col2:
                st.metric("Workflow Type", api_result.get("workflow_type", "unknown"))
            with col3:
                success_status = "✅ Success" if api_result.get("success") else "❌ Failed"
                st.metric("Status", success_status)
        
        # Final Results Display
        st.markdown("## 📋 Final Results")
        with st.container():
            # Let LLM format the final response
            if api_result and api_result.get("success"):
                with st.spinner("🤖 LLM is formatting the final response..."):
                    formatted_response = format_response_with_llm(user_input, api_result, ai_analysis)
                st.markdown(formatted_response)
                # Use the formatted response for chat history
                final_response = formatted_response
            else:
                error_msg = f"❌ Error: {api_result.get('error', 'Unknown error') if api_result else 'No results'}"
                st.error(error_msg)
                final_response = error_msg
        
        st.markdown("---")
        
        # Add the formatted assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": final_response})
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(message["content"])
    
    # REST API Testing Section
    st.header("🧪 REST API Testing")
    
    with st.expander("Test REST APIs Directly"):
        test_service = st.selectbox("Select Service", list(SERVICES.keys()))
        
        if test_service == "semantic_search":
            st.subheader("Semantic Search")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Search Workshops**")
                search_query = st.text_input("Search Query", "big data workshops")
                top_k = st.number_input("Top K Results", 1, 20, 5)
                
                if st.button("🔍 Search"):
                    result = call_rest_api("semantic_search", "search", {"query": search_query, "top_k": top_k})
                    st.json(result)
            
            with col2:
                st.write("**Get Statistics**")
                
                if st.button("📊 Get Stats"):
                    result = call_rest_api("semantic_search", "statistics", {})
                    st.json(result)
        
        elif test_service == "nl_to_sql":
            st.subheader("Natural Language Query to Database")
            
            st.write("**Ask questions in natural language about users, skills, and profiles:**")
            
            # Example queries
            example_queries = [
                "Who are the Python developers?",
                "Find users with advanced Oracle skills",
                "Show me data scientists",
                "Who has machine learning experience?",
                "List all users with their skills",
                "Find John Smith's profile",
                "Who are the most experienced developers?",
                "Show users with cloud computing skills"
            ]
            
            col1, col2 = st.columns([2, 1])
            
            # Initialize session state for the query
            if 'current_nl_query' not in st.session_state:
                st.session_state.current_nl_query = "Who are the Python developers?"
            
            with col1:
                nl_query = st.text_area("Natural Language Query", 
                                       value=st.session_state.current_nl_query,
                                       height=100,
                                       key="nl_query_textarea")
                
                if st.button("🤖 Execute NL Query"):
                    result = call_rest_api("nl_to_sql", "query_database_nl", {"natural_language_query": nl_query})
                    if result:
                        st.success("✅ Query executed successfully!")
                        if result.get("explanation"):
                            st.markdown(result["explanation"])
                        else:
                            st.info("Query executed but returned no results (empty response)")
                        
                        st.write("**Technical Details:**")
                        st.code(result.get("sql_query", "No SQL query shown"))
                    else:
                        st.error("❌ Query failed")
            
            with col2:
                st.write("**Example Queries:**")
                for i, example in enumerate(example_queries, 1):
                    # Show first few words of the query in the button
                    button_text = example if len(example) <= 35 else example[:32] + "..."
                    if st.button(f"📝 {button_text}", key=f"example_{i}"):
                        st.session_state.current_nl_query = example
                        st.rerun()
        
        elif test_service == "skill_progression":
            st.subheader("User Skills Progression")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Update User Skills**")
                user_id = st.text_input("User ID", "USR001")
                skill_name = st.text_input("Skill Name", "Python")
                experience_level = st.selectbox("Experience Level", ["BEGINNER", "INTERMEDIATE", "ADVANCED"])
                
                if st.button("📝 Update Skills"):
                    params = {
                        "userId": user_id,
                        "skills": [{
                            "skillName": skill_name,
                            "experienceLevel": experience_level
                        }]
                    }
                    result = call_rest_api("skill_progression", "update_user_skills", params)
                    st.json(result)
            
            with col2:
                st.write("**Update Workshop Progression**")
                workshop_user_id = st.text_input("User ID for Workshop", "USR001", key="workshop_user")
                workshop_id = st.number_input("Workshop ID", 1, 2000, 979)
                status = st.selectbox("Status", ["STARTED", "COMPLETED"])
                rating = st.number_input("Rating (1-5)", 1, 5, 5) if status == "COMPLETED" else None
                
                if st.button("📈 Update Progression"):
                    progression = {
                        "userId": workshop_user_id,
                        "workshopId": workshop_id,
                        "status": status
                    }
                    if rating is not None:
                        progression["rating"] = rating
                    
                    params = {
                        "progressions": [progression]
                    }
                    result = call_rest_api("skill_progression", "mark_workshop_complete", params)
                    st.json(result)

if __name__ == "__main__":
    main()
