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
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.genai_client import OracleGenAIClient
from utils.ai_reasoner import AIReasoner

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

def load_services_config() -> Dict[str, Any]:
    """서비스 설정을 JSON 파일에서 로드"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'services.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # Extract mcpServers from the new format
        services = config.get('mcpServers', {})
        logger.info(f"서비스 설정 로드 완료: {len(services)}개 서비스")
        return services
    except FileNotFoundError:
        logger.error(f"서비스 설정 파일을 찾을 수 없음: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"서비스 설정 파일 JSON 파싱 오류: {e}")
        raise
    except Exception as e:
        logger.error(f"서비스 설정 로드 오류: {e}")
        raise

# 서비스 설정 로드
SERVICES = load_services_config()

class MCPToolDiscovery:
    """MCP 서비스 도구 동적 발견 및 캐싱 관리"""
    
    def __init__(self, services_config: Dict[str, Any]):
        self.services = services_config
        self.tools_cache = {}
        
    async def discover_tools(self, service_key: str) -> Dict[str, Any]:
        """특정 서비스의 도구를 발견하고 캐시"""
        if service_key not in self.services:
            raise ValueError(f"Unknown service: {service_key}")
            
        service = self.services[service_key]
        
        # 캐시된 도구가 있고 최근 발견한 경우 반환
        if (service.get('tools_cache') and 
            service.get('last_discovery') and 
            self._is_cache_valid(service['last_discovery'])):
            return service['tools_cache']
            
        # REST API를 통해 도구 발견
        try:
            tools_url = f"{service['baseUrl']}{service['endpoints']['tools']}"
            response = requests.get(tools_url, timeout=10)
            response.raise_for_status()
            
            tools_data = response.json()
            
            # 캐시 업데이트
            service['tools_cache'] = tools_data
            service['last_discovery'] = datetime.now().isoformat()
            
            logger.info(f"도구 발견 완료 - {service_key}: {len(tools_data.get('tools', []))}개 도구")
            return tools_data
            
        except requests.RequestException as e:
            logger.error(f"도구 발견 실패 - {service_key}: {e}")
            # 캐시된 도구가 있으면 반환, 없으면 빈 결과
            return service.get('tools_cache', {'tools': []})
            
    def _is_cache_valid(self, last_discovery: str, max_age_minutes: int = 30) -> bool:
        """캐시 유효성 검사"""
        try:
            last_time = datetime.fromisoformat(last_discovery)
            age = datetime.now() - last_time
            return age.total_seconds() < (max_age_minutes * 60)
        except:
            return False
            
    def enable_service(self, service_key: str) -> bool:
        """서비스 활성화 및 도구 발견"""
        if service_key not in self.services:
            return False
            
        self.services[service_key]['enabled'] = True
        # 비동기 도구 발견은 별도로 호출
        return True
        
    def disable_service(self, service_key: str) -> bool:
        """서비스 비활성화"""
        if service_key not in self.services:
            return False
            
        self.services[service_key]['enabled'] = False
        return True
        
    def get_enabled_services(self) -> List[str]:
        """활성화된 서비스 목록 반환"""
        return [key for key, service in self.services.items() 
                if service.get('enabled', False)]
                
    def get_available_tools(self, service_key: str) -> List[Dict[str, Any]]:
        """서비스의 사용 가능한 도구 목록 반환"""
        if service_key not in self.services:
            return []
            
        service = self.services[service_key]
        # Ensure tools_cache is not None before accessing it
        tools_cache = service.get('tools_cache')
        if not tools_cache:
            return []
        return tools_cache.get('tools', [])


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
    """REST API 서비스 관리 클래스 - 서비스 상태 테스트 및 건강 상태 확인"""
    
    def __init__(self, services_config: Dict[str, Any]):
        self.services = services_config
        
    def test_service(self, service_key: str) -> Dict[str, Any]:
        """개별 서비스 건강 상태 테스트"""
        if service_key not in self.services:
            return {
                "success": False,
                "status": "error",
                "message": f"Unknown service: {service_key}",
                "response_time": 0
            }
            
        service = self.services[service_key]
        health_url = f"{service['baseUrl']}{service['endpoints']['health']}"
        
        try:
            start_time = time.time()
            response = requests.get(health_url, timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status": "healthy",
                    "message": f"Service {service['name']} is running",
                    "response_time": round(response_time * 1000, 2),  # ms
                    "details": response.json() if response.content else {}
                }
            else:
                return {
                    "success": False,
                    "status": "unhealthy", 
                    "message": f"Service returned status {response.status_code}",
                    "response_time": round(response_time * 1000, 2)
                }
                
        except requests.RequestException as e:
            return {
                "success": False,
                "status": "error",
                "message": f"Connection failed: {str(e)}",
                "response_time": 0
            }
            
    def test_all_services(self) -> Dict[str, Dict[str, Any]]:
        """모든 서비스 건강 상태 테스트"""
        results = {}
        for service_key in self.services.keys():
            results[service_key] = self.test_service(service_key)
        return results
        
    async def discover_service_tools(self, service_key: str) -> Dict[str, Any]:
        """서비스의 도구 발견"""
        return await mcp_discovery.discover_tools(service_key)


def generate_chatbot_response_with_data(user_query: str) -> tuple[str, Dict[str, Any], Dict[str, Any]]:
    """Generate chatbot response and return the raw data for LLM formatting"""
    log_step("ChatbotResponse", f"Processing user query: '{user_query}'")
    
    # Initialize AI reasoner
    if "ai_reasoner" not in st.session_state:
        st.session_state.ai_reasoner = AIReasoner(st.session_state.services_config)
    
    # Step 1: AI Analysis
    ai_analysis = st.session_state.ai_reasoner.reason_about_query(user_query)
    
    # Step 2: Validate and make API call
    service_key = ai_analysis.get("service")
    action = ai_analysis.get("tool") or ai_analysis.get("action")
    parameters = ai_analysis.get("parameters", {})
    
    if not service_key or not action:
        error_msg = "AI reasoner failed to identify a valid service and action from the user query."
        log_step("ChatbotResponse", f"❌ {error_msg}")
        # Create a final result that shows the initial failure
        final_result = {
            "success": False,
            "error": error_msg,
            "workflow_type": "failed_initialization",
            "total_steps": 0,
            "steps": [{
                "step": 1,
                "service": "AI-Reasoner",
                "action": "Initial-Analysis",
                "parameters": {"user_query": user_query},
                "result": {"success": False, "error": error_msg},
                "reasoning": ai_analysis.get('thinking_process', 'N/A')
            }]
        }
        return error_msg, final_result, ai_analysis
    
    if service_key not in SERVICES:
        error_msg = f"Unknown service: {service_key}"
        log_step("ChatbotResponse", f"❌ {error_msg}")
        return error_msg, {"success": False, "error": error_msg}, ai_analysis
    
    # Execute dynamic multi-step workflow
    all_results = []
    step_count = 0
    max_steps = 5
    
    # Start with initial AI analysis
    current_step = ai_analysis
    
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
        
        # Check if workflow should continue based on dynamic reasoning
        if step_result.get("success"):
            # Check if current step indicates completion
            if current_step.get("workflow_complete", False):
                log_step("ChatbotResponse", f"Workflow marked complete after step {step_count}")
                break
                
            # If not complete, use AI reasoner to determine next step
            log_step("ChatbotResponse", f"Step {step_count} successful, checking for next step...")
            
            # Re-analyze with context of previous results to determine next action
            next_analysis = st.session_state.ai_reasoner.reason_about_query(user_query, all_results)
            
            # If reasoner says we're done, stop
            if next_analysis.get("workflow_complete", False):
                log_step("ChatbotResponse", f"AI reasoner determined workflow complete after {step_count} steps")
                break
                
            # If reasoner suggests a different service than what we just did, continue
            if (next_analysis.get("service") != step_service or 
                next_analysis.get("tool") != step_action):
                
                # Enhance semantic search queries with context from previous steps
                if next_analysis.get("service") == "livelabs-semantic-search":
                    context_parts = [f"Original user inquiry: {user_query}"]
                    
                    # Add information from all previous steps
                    for prev_step in all_results:
                        step_result_data = prev_step.get("result", {})
                        if not step_result_data.get("success"):
                            continue
                            
                        # Process all keys in the result data
                        for key, value in step_result_data.items():
                            # Skip special keys and empty values
                            if key in ["success", "explanation"] or not value:
                                continue
                                
                            # Handle list of objects (like users, workshops, etc.)
                            if isinstance(value, list) and value and isinstance(value[0], dict):
                                for item in value:
                                    if not isinstance(item, dict):
                                        continue
                                    # Add all fields from each item
                                    for field, field_value in item.items():
                                        if not field_value:
                                            continue
                                        if isinstance(field_value, list):
                                            if field == "skills" and len(field_value) > 5:
                                                field_value = field_value[:5]  # Limit skills to top 5
                                            context_parts.append(f"{key}.{field}: {', '.join(map(str, field_value))}")
                                        else:
                                            context_parts.append(f"{key}.{field}: {field_value}")
                            # Handle simple key-value pairs
                            elif not isinstance(value, (dict, list)):
                                context_parts.append(f"{key}: {value}")
                            # Handle nested dictionaries
                            elif isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    if sub_value:
                                        context_parts.append(f"{key}.{sub_key}: {sub_value}")
                        
                        # Add explanation if it exists
                        if step_result_data.get("explanation"):
                            context_parts.append(f"{prev_step['service']} context: {step_result_data['explanation']}")
                    
                    # Enhance query with context
                    original_query = next_analysis.get("parameters", {}).get("query", user_query)
                    comprehensive_query = f"{original_query}. Context: {' | '.join(context_parts)}"
                    next_analysis["parameters"]["query"] = comprehensive_query
                    log_step("ChatbotResponse", f"Enhanced query with context: {comprehensive_query[:200]}...")
                
                current_step = next_analysis
                log_step("ChatbotResponse", f"Continuing to next step: {current_step.get('service')}.{current_step.get('tool')}")
            else:
                log_step("ChatbotResponse", f"No new action suggested - workflow complete")
                break
        else:
            log_step("ChatbotResponse", f"Step {step_count} failed - stopping workflow")
            break
    
    # Combine results
    success = all(step["result"].get("success", False) for step in all_results) if all_results else False
    final_result = {
        "success": success,
        "workflow_type": "multi_step" if len(all_results) > 1 else "single_step", 
        "total_steps": len(all_results),
        "steps": all_results
    }
    
    # Generate response with LLM formatting
    if final_result.get("success"):
        response = format_response_with_llm(user_query, final_result, ai_analysis)
    else:
        # Even on failure, provide a helpful error message and the steps that were attempted
        failed_step = next((s for s in all_results if not s["result"].get("success")), None)
        if failed_step:
            error_details = failed_step['result'].get('error', 'Unknown error')
            response = f"I encountered an error during the process. Step {failed_step['step']} ({failed_step['action']}) failed with the following error: {error_details}"
        else:
            response = f"I'm sorry, I was unable to complete your request for '{user_query}'. An unexpected error occurred."

    log_step("ChatbotResponse", f"Workflow completed: {len(all_results)} steps")
    return response, final_result, ai_analysis


def format_response_with_llm(user_query: str, api_result: Dict[str, Any], ai_analysis: Dict[str, Any]) -> str:
    """Use LLM to format the API response into a natural language response"""
    log_step("LLMFormatting", f"Formatting response for query: '{user_query}'")
    
    # Prepare data for LLM formatting
    workflow_type = api_result.get("workflow_type", "single_step")
    total_steps = api_result.get("total_steps", 1)
    steps = api_result.get("steps", [])
    
    # Extract information from all steps dynamically
    all_step_data = {}
    
    for step in steps:
        step_result = step.get("result", {})
        if not step_result.get("success"):
            continue
            
        service_name = step.get("service", "unknown")
        if service_name not in all_step_data:
            all_step_data[service_name] = []
            
        # Process all keys in the result
        step_data = {}
        for key, value in step_result.items():
            # Skip special keys and empty values
            if key in ["success", "explanation"] or not value:
                continue
                
            # Handle different value types
            if isinstance(value, list):
                # For lists, take first 5 items if it's a list of objects
                if value and isinstance(value[0], dict):
                    step_data[key] = value[:5]
                else:
                    step_data[key] = value
            else:
                step_data[key] = value
                
        # Add explanation if it exists
        if step_result.get("explanation"):
            step_data["explanation"] = step_result["explanation"]
            
        all_step_data[service_name].append(step_data)
    
    # Backward compatibility
    user_info = all_step_data.get("livelabs-nl-query", [{}])[0].get("users", [{}])[0] if all_step_data.get("livelabs-nl-query") else {}
    workshop_results = all_step_data.get("livelabs-semantic-search", [{}])[0].get("results", [])
    
    # Create context for LLM using the dynamic all_step_data structure
    context_parts = [f"사용자 질문: {user_query}"]
    workshops = []
    
    # Process all services and their data
    for service_name, service_steps in all_step_data.items():
        if not service_steps:
            continue
            
        context_parts.append(f"\n{service_name.upper()} 결과:")
        
        for step_idx, step_data in enumerate(service_steps, 1):
            for key, value in step_data.items():
                if key == 'explanation':
                    context_parts.append(f"- 설명: {value}")
                elif key == 'results' and isinstance(value, list):
                    # Add raw workshop results to context
                    for item in value[:5]:  # Limit to top 5 workshops
                        if isinstance(item, dict):
                            context_parts.append(f"- WORKSHOP_RAW: {item}")
                elif isinstance(value, list):
                    if value and isinstance(value[0], dict):
                        for item in value[:3]:  # Limit to top 3 items
                            if 'name' in item:
                                context_parts.append(f"- {key}: {item.get('name')}")
                    elif value:
                        context_parts.append(f"- {key}: {', '.join(map(str, value[:5]))}")
                elif value and not isinstance(value, (dict, list)):
                    context_parts.append(f"- {key}: {value}")
    
    context = "\n".join(context_parts)
    
    # Use LLM to format response
    formatting_prompt = """You are a helpful AI assistant for Oracle LiveLabs workshop recommendations.

CONTEXT:
{context}

TASK: Create a natural, conversational response in Korean that:
1. Acknowledges the user's query
2. If user profile information is available, mention relevant skills/experience
3. For each WORKSHOP_RAW entry:
   - Extract and present the workshop details in this format:
     ### [title]
     - **난이도**: [difficulty]
     - **소요 시간**: [duration]
     - **카테고리**: [category]
     - **유사도 점수**: [similarity]%
     - [바로가기](url)
4. Order workshops by highest similarity score first
5. Keep the tone warm, professional, and encouraging
6. Include all URLs exactly as provided in the raw data
7. Format the response in clean Markdown

IMPORTANT:
- The raw workshop data is in JSON format after 'WORKSHOP_RAW:'
- Use the exact field names from the raw data
- Don't modify or interpret the values, just present them as-is
- If a field is missing, skip that line
- Make sure all URLs are clickable Markdown links
- Use only the information provided in the context
- Keep the response concise but informative
- Use Korean throughout the response

Example of raw data format:
- WORKSHOP_RAW: {{'title': '...', 'url': '...', 'difficulty': '...', ...}}

Example output format for each workshop:
### [Workshop Title]
- **난이도**: [Difficulty]
- **소요 시간**: [Duration]
- **카테고리**: [Category]
- **유사도 점수**: [Similarity]%
- [바로가기](URL)
"""
    
    try:
        genai_client = OracleGenAIClient()
        llm_response = genai_client.chat(
            prompt=formatting_prompt.format(context=context),
            model_name="meta.llama-4-scout-17b-16e-instruct",
            temperature=0.3,
            max_tokens=500
        )
        
        if llm_response.get("success"):
            formatted_response = llm_response["text"]
            log_step("LLMFormatting", "✅ LLM formatting successful")
            return formatted_response
        else:
            log_step("LLMFormatting", f"❌ LLM formatting failed: {llm_response.get('error')}")
    except Exception as e:
        log_step("LLMFormatting", f"❌ LLM formatting error: {str(e)}")
    
    # Fallback to simple formatting
    fallback_response = f"Based on your query '{user_query}', "
    
    if user_info:
        fallback_response += f"I found your profile information. "
    
    if workshop_results:
        fallback_response += f"I found {len(workshop_results)} relevant workshops:\n\n"
        for i, workshop in enumerate(workshop_results[:3], 1):
            title = workshop.get("title", "Untitled Workshop")
            url = workshop.get("url", "#")
            score = workshop.get("score", 0)
            fallback_response += f"{i}. **[{title}]({url})** (Relevance: {score:.1f}/10)\n"
    else:
        fallback_response += "I couldn't find specific workshops matching your criteria."
    
    return fallback_response


# ===== REST API TESTING FUNCTIONS =====

def call_rest_api(service_key: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """서비스에 REST API 호출 수행"""
    service = st.session_state.services_config[service_key]

    try:
        # 서비스별 매개변수 이름 매핑 처리
        if service_key == "livelabs-nl-query" and "query" in params:
            log_step("CallRESTAPI", "매개변수 이름 매핑: 'query' -> 'natural_language_query'")
            params["natural_language_query"] = params.pop("query")

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
            url = f"{service['baseUrl']}{service['endpoints'][endpoint_name]}"
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



def main():
    """Main Streamlit application"""
    log_step("MainApp", "Starting main application")

    # Initialize session state
    if "services_config" not in st.session_state:
        st.session_state.services_config = load_services_config()
    if "mcp_discovery" not in st.session_state:
        st.session_state.mcp_discovery = MCPToolDiscovery(st.session_state.services_config)
    if "rest_service_manager" not in st.session_state:
        st.session_state.rest_service_manager = RESTServiceManager(st.session_state.services_config)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = []
    if "service_states" not in st.session_state:
        st.session_state.service_states = {key: service.get('enabled', False) for key, service in st.session_state.services_config.items()}

    st.title("🔬 LiveLabs AI Assistant")
    st.markdown("*Powered by REST APIs and OCI Generative AI*")

    with st.sidebar:
        st.header("🔧 Service Management")

        st.subheader("Service Activation")
        for service_key, service in st.session_state.services_config.items():
            current_state = st.session_state.service_states.get(service_key, False)
            new_state = st.toggle(
                f"{service['name']}",
                value=current_state,
                key=f"toggle_{service_key}",
                help=f"Enable/disable {service['description']}"
            )
            if new_state != current_state:
                st.session_state.service_states[service_key] = new_state
                log_step("ServiceToggle", f"{service['name']} {'enabled' if new_state else 'disabled'}")

                if new_state:  # If service is enabled, discover tools
                    with st.spinner(f"Discovering tools for {service['name']}..."):
                        try:
                            import asyncio
                            tools_data = asyncio.run(st.session_state.mcp_discovery.discover_tools(service_key))
                            st.success(f"✅ Found {len(tools_data.get('tools', []))} tools for {service['name']}")
                        except Exception as e:
                            st.error(f"❌ Tool discovery failed for {service['name']}: {str(e)}")
                else: # If service is disabled, clear the cache
                    if 'tools_cache' in st.session_state.services_config[service_key]:
                        del st.session_state.services_config[service_key]['tools_cache']
                        log_step("Cache", f"Cleared tools cache for {service['name']}")

                st.rerun()

        st.subheader("📊 Service Status")
        if st.button("🩺 Check All Services", key="check_services"):
            with st.spinner("Checking service health..."):
                st.session_state.health_check_results = st.session_state.rest_service_manager.test_all_services()
                st.rerun()

        if "health_check_results" in st.session_state:
            for service_key, result in st.session_state.health_check_results.items():
                if st.session_state.service_states.get(service_key):
                    status = result['status']
                    if status == 'healthy':
                        st.success(f"✅ {st.session_state.services_config[service_key]['name']}: Healthy ({result['response_time']}ms)")
                    else:
                        st.warning(f"⚠️ {st.session_state.services_config[service_key]['name']}: {result['message']}")

        with st.expander("⚙️ Service Configuration & Tools"):
            st.subheader("Loaded `SERVICES` Configuration")
            st.json(st.session_state.services_config)
            st.subheader("Discovered Tools Cache")
            cached_tools_services = [s for s, d in st.session_state.services_config.items() if d.get("tools_cache")]
            if cached_tools_services:
                for service_key in cached_tools_services:
                    with st.expander(f"🛠️ Tools for {st.session_state.services_config[service_key]['name']}"):
                        st.json(st.session_state.services_config[service_key]["tools_cache"])
            else:
                st.info("No tools cached. Use 'Discover Tools' first.")

        st.subheader("⚡ Quick Actions")
        enabled_services_for_action = [k for k, v in st.session_state.service_states.items() if v]
        if not enabled_services_for_action:
            st.info("Enable a service to see its actions.")
        else:
            selected_service_for_action = st.selectbox(
                "Select a service",
                options=enabled_services_for_action,
                format_func=lambda x: st.session_state.services_config[x]['name'],
                key="quick_action_service"
            )

            if selected_service_for_action:
                available_tools = st.session_state.mcp_discovery.get_available_tools(selected_service_for_action)
                tool_names = [tool['name'] for tool in available_tools]

                if not tool_names:
                    st.warning("No tools discovered for this service. Use 'Discover Tools' first.")
                else:
                    selected_action = st.selectbox(
                        "Select an action",
                        options=tool_names,
                        key="quick_action_action"
                    )

                    if selected_action:
                        selected_tool = next((t for t in available_tools if t['name'] == selected_action), None)
                        params = {}

                        if selected_tool and 'parameters' in selected_tool:
                            st.markdown("**Parameters**")
                            for param in selected_tool['parameters']:
                                if isinstance(param, dict):
                                    param_name = param.get('name')
                                    param_type = param.get('type', 'string')
                                else:
                                    param_name = param
                                    param_type = 'string'

                                if param_name:
                                    params[param_name] = st.text_input(
                                        f"Parameter: `{param_name}` ({param_type})",
                                        key=f"param_{selected_service_for_action}_{selected_action}_{param_name}"
                                    )

                        if st.button("🚀 Run Action", key="run_quick_action"):
                            with st.spinner(f"Running {selected_action}..."):
                                final_params = {k: v for k, v in params.items() if v}
                                result = call_rest_api(selected_service_for_action, selected_action, final_params)
                                st.session_state.last_action_result = result

        if "last_action_result" in st.session_state:
            with st.expander("Last Action Result", expanded=True):
                st.json(st.session_state.last_action_result)

        st.subheader("📝 Activity Log")
        if st.button("Clear Log", key="clear_log"):
            st.session_state.log_messages = []
            st.rerun()

        log_container = st.container()
        with log_container:
            for msg in reversed(st.session_state.get("log_messages", [])):
                st.text(msg)

    # Main chat interface
    st.header("💬 Chat with LiveLabs AI")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "api_response" in message and message["api_response"]:
                with st.expander("View Full API Response"):
                    st.json(message["api_response"])
            if "ai_analysis" in message and message["ai_analysis"]:
                with st.expander("View AI Reasoning Analysis"):
                    st.json(message["ai_analysis"])

            # Display workflow steps if available
            if "api_response" in message and message["api_response"] and "steps" in message["api_response"]:
                with st.expander("View Workflow Steps"):
                    for step in message["api_response"]["steps"]:
                        st.markdown(f"**Step {step['step']}: {step['service']} -> {step['action']}**")
                        if step['result'].get('success'):
                            st.success("Status: Success")
                        else:
                            st.error("Status: Failed")
                        
                        with st.container():
                            st.markdown("**Parameters:**")
                            st.json(step['parameters'])
                            
                            st.markdown("**Reasoning:**")
                            st.info(step.get('reasoning', 'No reasoning provided.'))

                            st.markdown("**Result:**")
                            st.json(step['result'])

    if prompt := st.chat_input("Ask me about LiveLabs workshops..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("AI is thinking..."):
                assistant_response, api_response, ai_analysis = generate_chatbot_response_with_data(prompt)
                
                # First, save the complete response to session state
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": assistant_response,
                    "api_response": api_response,
                    "ai_analysis": ai_analysis
                })
                
                # Then, update the UI and force a rerun to show the new message and its details
                message_placeholder.markdown(assistant_response)
                st.rerun()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        logger.error(f"Unhandled exception in main: {e}", exc_info=True)
