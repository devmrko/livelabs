#!/usr/bin/env python3
"""
LiveLabs Streamlit Application with MCP Integration
Uses FastMCP client to communicate with MCP services

LiveLabs AI 어시스턴트 - Streamlit 웹 애플리케이션
MCP 서비스들과 통합하여 워크샵 검색, 자연어 쿼리, 사용자 스킬 관리 기능 제공
"""

import streamlit as st
import asyncio
import json
import time
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastmcp import Client
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
            
        # MCP Client를 통해 도구 발견
        try:
            service_url = service['baseUrl']
            async with Client(service_url) as client:
                tools = await client.list_tools()
                tools_data = {'tools': [{'name': tool.name, 'description': tool.description} for tool in tools]}
                
                # 캐시 업데이트
                service['tools_cache'] = tools_data
                service['last_discovery'] = datetime.now().isoformat()
                
                logger.info(f"도구 발견 완료 - {service_key}: {len(tools_data.get('tools', []))}개 도구")
                return tools_data
                
        except Exception as e:
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

class MCPServiceManager:
    """MCP 서비스 관리 클래스 - 서비스 상태 테스트 및 건강 상태 확인"""
    
    def __init__(self, services_config: Dict[str, Any]):
        self.services = services_config
        
    async def test_service(self, service_key: str) -> Dict[str, Any]:
        """개별 서비스 건강 상태 테스트"""
        if service_key not in self.services:
            return {
                "success": False,
                "status": "error",
                "message": f"Unknown service: {service_key}",
                "response_time": 0
            }
            
        service = self.services[service_key]
        service_url = service['baseUrl']
        
        try:
            start_time = time.time()
            async with Client(service_url) as client:
                # Test connection by listing tools
                await client.list_tools()
                response_time = time.time() - start_time
                
                return {
                    "success": True,
                    "status": "healthy",
                    "message": f"Service {service['name']} is running",
                    "response_time": round(response_time * 1000, 2),  # ms
                    "details": {"connection": "successful"}
                }
                
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": f"Connection failed: {str(e)}",
                "response_time": 0
            }
            
    async def test_all_services(self) -> Dict[str, Dict[str, Any]]:
        """모든 서비스 건강 상태 테스트"""
        results = {}
        for service_key in self.services.keys():
            results[service_key] = await self.test_service(service_key)
        return results
        
    async def discover_service_tools(self, service_key: str) -> Dict[str, Any]:
        """서비스의 도구 발견"""
        return await st.session_state.mcp_discovery.discover_tools(service_key)


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
        error_msg = "죄송합니다. 질문을 이해할 수 없습니다. 다른 방식으로 질문해 주세요."
        log_step("ChatbotResponse", f"❌ AI reasoner failed to identify service/action")
        # Create a final result that shows the initial failure
        final_result = {
            "success": False,
            "error": "AI reasoner failed to identify a valid service and action",
            "workflow_type": "failed_initialization",
            "total_steps": 0,
            "steps": [{
                "step": 1,
                "service": "AI-Reasoner",
                "action": "Initial-Analysis",
                "parameters": {"user_query": user_query},
                "result": {"success": False, "error": "Could not parse user intent"},
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
            # Check if we actually got meaningful data
            has_meaningful_data = False
            if step_result.get("users") and len(step_result["users"]) > 0:
                has_meaningful_data = True
            elif step_result.get("results") and len(step_result["results"]) > 0:
                has_meaningful_data = True
            elif step_result.get("total_found", 0) > 0:
                has_meaningful_data = True
                
            # If no meaningful data and this is a user query, don't continue workflow
            if not has_meaningful_data and step_service == "livelabs-nl-query":
                log_step("ChatbotResponse", f"No user data found, stopping workflow after step {step_count}")
                break
                
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
                
            # If reasoner suggests no action or same action, stop workflow
            next_service = next_analysis.get("service")
            next_tool = next_analysis.get("tool") or next_analysis.get("action")
            
            if not next_service or not next_tool:
                log_step("ChatbotResponse", f"No new action suggested - workflow complete")
                break
                
            # If reasoner suggests a different service/tool than what we just did, continue
            if (next_service != step_service or next_tool != step_action):
                current_step = next_analysis
                log_step("ChatbotResponse", f"Continuing to next step: {next_service}.{next_tool}")
            else:
                log_step("ChatbotResponse", f"Same action suggested - workflow complete")
                break
                
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
                    for item in value[len(value)-1]:  # Limit to top 5 workshops
                        if isinstance(item, dict):
                            context_parts.append(f"- WORKSHOP_RAW: {item}")
                elif isinstance(value, list):
                    if value and isinstance(value[0], dict):
                        for item in value[len(value)-1]:  # Limit to top 3 items
                            if 'name' in item:
                                context_parts.append(f"- {key}: {item.get('name')}")
                    elif value:
                        context_parts.append(f"- {key}: {', '.join(map(str, value[:5]))}")
                elif value and not isinstance(value, (dict, list)):
                    context_parts.append(f"- {key}: {value}")
    
    context = "\n".join(context_parts)
    
    # Check if context contains any WORKSHOP_RAW entries
    has_workshop_raw = "WORKSHOP_RAW:" in context
    has_empty_results = any(phrase in context for phrase in ["검색 결과 없음", "데이터 없음", "total_found: 0"])
    
    # If no workshop data or empty results, return AI Workshop Planner response
    if not has_workshop_raw or has_empty_results:
        return "🤖 **AI Workshop Planner**\n\n죄송합니다! 요청하신 조건에 맞는 워크샵을 찾을 수 없었어요. \n\n💡 **다른 방법을 시도해 보세요:**\n- 다른 키워드로 검색 (예: 'Python', 'Machine Learning', 'Database')\n- 더 일반적인 주제로 검색\n- 사용자 정보를 먼저 등록하고 맞춤형 추천 요청\n\n언제든지 도와드릴게요! 🚀"
    
    # Use LLM to format response ONLY when actual data exists
    formatting_prompt = """You are an AI Workshop Planner assistant helping users with their Oracle LiveLabs learning journey.

CONTEXT:
{context}

역할: AI Workshop Planner
- 사용자의 학습 목표와 현재 스킬을 고려한 맞춤형 추천
- 격려적이고 친근한 톤으로 대화
- 학습 경로 설계 및 진도 관리
- 실용적인 학습 조언 제공

응답 규칙:
1. WORKSHOP_RAW 데이터만 사용하여 워크샵 정보 제공
2. 각 워크샵을 다음 형식으로 제시:
   ### [title]
   - **난이도**: [difficulty] 
   - **카테고리**: [category]
   - **유사도**: [similarity]%
   - [학습 시작하기](url)
3. 유사도 높은 순으로 정렬
4. AI Workshop Planner로서 개인화된 조언 추가
5. 학습 단계와 다음 스텝 제안

예시 응답:
🎓 **맞춤형 학습 경로 추천**

안녕하세요! 여러분의 AI Workshop Planner입니다. 요청하신 조건에 맞는 워크샵을 찾았습니다!

### Getting Started with Python and Oracle Database
- **난이도**: BEGINNER
- **카테고리**: Database  
- **유사도**: 85.2%
- [학습 시작하기](https://livelabs.oracle.com/...)

💡 **학습 팁**: 이 워크샵은 Python 기초부터 시작하여 데이터베이스 연동까지 단계별로 학습할 수 있어요!
"""
    
    try:
        genai_client = OracleGenAIClient()
        llm_response = genai_client.chat(
            prompt=formatting_prompt.format(context=context),
            model_name="meta.llama-4-scout-17b-16e-instruct",
            temperature=0.3,
            max_tokens=4000
        )
        
        if llm_response.get("success"):
            formatted_response = llm_response["text"]
            log_step("LLMFormatting", "✅ LLM formatting successful")
            return formatted_response
        else:
            log_step("LLMFormatting", f"❌ LLM formatting failed: {llm_response.get('error')}")
    except Exception as e:
        log_step("LLMFormatting", f"❌ LLM formatting error: {str(e)}")
    
    # Fallback AI Workshop Planner response
    return "🤖 **AI Workshop Planner**\n\n죄송합니다. 요청하신 정보를 처리하는 도중 문제가 발생했어요. \n\n다시 시도해 주시거나 다른 방식으로 질문해 주세요. 🚀"


# ===== MCP API TESTING FUNCTIONS =====

async def call_mcp_api(service_key: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """서비스에 MCP API 호출 수행"""
    service = st.session_state.services_config[service_key]

    try:
        # 서비스별 매개변수 이름 매핑 처리
        if service_key == "livelabs-nl-query" and "query" in params:
            log_step("CallMCPAPI", "매개변수 이름 매핑: 'query' -> 'natural_language_query'")
            params["natural_language_query"] = params.pop("query")

        log_step("CallMCPAPI", f"{service['name']}.{action} 호출, 매개변수: {params}")
        
        service_url = service['baseUrl']
        log_step("CallMCPAPI", f"🌐 MCP 서비스 URL: {service_url}")
        
        # MCP 클라이언트를 통해 도구 호출
        async with Client(service_url) as client:
            log_step("CallMCPAPI", f"📤 MCP 도구 호출: {action}")
            result = await client.call_tool(action, params)
            
            log_step("CallMCPAPI", f"✅ {service['name']}.{action} 성공적으로 완료")
            
            # 결과 데이터 추출
            if hasattr(result, 'data') and result.data:
                response_data = result.data
            elif hasattr(result, 'structured_content') and result.structured_content:
                response_data = result.structured_content
            else:
                response_data = {"success": True, "raw_result": str(result)}
            
            log_step("CallMCPAPI", f"📊 응답 데이터 키: {list(response_data.keys()) if isinstance(response_data, dict) else '딕셔너리 아님'}")
            
            # 응답에 대한 주요 정보 로그
            if isinstance(response_data, dict):
                if "success" in response_data:
                    log_step("CallMCPAPI", f"🎯 API 성공: {response_data.get('success')}")
                if "results" in response_data:
                    log_step("CallMCPAPI", f"📋 결과 개수: {len(response_data.get('results', []))}")
                if "total_found" in response_data:
                    log_step("CallMCPAPI", f"🔍 총 발견: {response_data.get('total_found')}")
                if "error" in response_data and response_data.get("error"):
                    log_step("CallMCPAPI", f"⚠️ API 오류 반환: {response_data.get('error')}")
            
            # 명시적인 성공 필드가 없으면 성공으로 표시
            if isinstance(response_data, dict) and "success" not in response_data:
                response_data["success"] = True
                log_step("CallMCPAPI", f"🔧 응답에 success=True 추가")
            
            return response_data
        
    except Exception as e:
        error_msg = f"MCP 요청 실패: {str(e)}"
        log_step("CallMCPAPI", f"❌ {service['name']}.{action} 오류: {error_msg}")
        return {"success": False, "error": error_msg}


def call_rest_api(service_key: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP API 호출을 위한 동기 래퍼"""
    return asyncio.run(call_mcp_api(service_key, action, params))



def main():
    """Main Streamlit application"""
    log_step("MainApp", "Starting main application")

    # Initialize session state
    if "services_config" not in st.session_state:
        st.session_state.services_config = load_services_config()
    if "mcp_discovery" not in st.session_state:
        st.session_state.mcp_discovery = MCPToolDiscovery(st.session_state.services_config)
    if "mcp_service_manager" not in st.session_state:
        st.session_state.mcp_service_manager = MCPServiceManager(st.session_state.services_config)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = []
    if "service_states" not in st.session_state:
        st.session_state.service_states = {key: service.get('enabled', False) for key, service in st.session_state.services_config.items()}

    st.title("🤖 AI Workshop Planner - Oracle LiveLabs")
    st.markdown("*Your personal learning assistant for Oracle LiveLabs workshops*")
    
    # Add AI Workshop Planner introduction
    with st.expander("🎯 What can AI Workshop Planner do?", expanded=False):
        st.markdown("""
        **🤖 AI Workshop Planner helps you:**
        - 📚 Find workshops based on your skills and interests
        - 👤 Manage user profiles and skill tracking
        - 🎯 Get personalized learning path recommendations
        - 📈 Track workshop completion progress
        - 💡 Receive learning tips and guidance
        
        **💬 Try asking:**
        - "내 스킬에 맞는 워크샵 추천해주세요"
        - "사용자를 추가해주세요"
        - "Python 관련 워크샵을 찾아주세요"
        - "워크샵 완료를 기록해주세요"
        """)

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
                st.session_state.health_check_results = asyncio.run(st.session_state.mcp_service_manager.test_all_services())
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

                        # Add parameter inputs based on tool requirements
                        st.markdown("**Parameters**")
                        
                        # Handle common tool parameters
                        if selected_action == "query_database_nl":
                            params["natural_language_query"] = st.text_input(
                                "Natural Language Query",
                                placeholder="e.g., Who are the Python developers?",
                                key=f"param_{selected_service_for_action}_{selected_action}_natural_language_query"
                            )
                            params["top_k"] = st.number_input(
                                "Top K Results",
                                min_value=1,
                                max_value=50,
                                value=10,
                                key=f"param_{selected_service_for_action}_{selected_action}_top_k"
                            )
                        elif selected_action == "search_workshops":
                            params["query"] = st.text_input(
                                "Search Query",
                                placeholder="e.g., machine learning python",
                                key=f"param_{selected_service_for_action}_{selected_action}_query"
                            )
                            params["top_k"] = st.number_input(
                                "Top K Results",
                                min_value=1,
                                max_value=50,
                                value=10,
                                key=f"param_{selected_service_for_action}_{selected_action}_top_k"
                            )
                        elif selected_action == "get_user":
                            params["name"] = st.text_input(
                                "User Name (optional)",
                                key=f"param_{selected_service_for_action}_{selected_action}_name"
                            )
                            params["email"] = st.text_input(
                                "User Email (optional)",
                                key=f"param_{selected_service_for_action}_{selected_action}_email"
                            )
                        elif selected_action == "add_user":
                            params["name"] = st.text_input(
                                "User Name",
                                key=f"param_{selected_service_for_action}_{selected_action}_name"
                            )
                            params["email"] = st.text_input(
                                "User Email",
                                key=f"param_{selected_service_for_action}_{selected_action}_email"
                            )
                        elif selected_action == "update_user_skills":
                            params["userId"] = st.text_input(
                                "User ID",
                                key=f"param_{selected_service_for_action}_{selected_action}_userId"
                            )
                            params["skillName"] = st.text_input(
                                "Skill Name",
                                key=f"param_{selected_service_for_action}_{selected_action}_skillName"
                            )
                            params["experienceLevel"] = st.selectbox(
                                "Experience Level",
                                options=["BEGINNER", "INTERMEDIATE", "ADVANCED"],
                                key=f"param_{selected_service_for_action}_{selected_action}_experienceLevel"
                            )
                        elif selected_action == "update_workshop_progress":
                            params["userId"] = st.text_input(
                                "User ID",
                                key=f"param_{selected_service_for_action}_{selected_action}_userId"
                            )
                            params["workshopId"] = st.text_input(
                                "Workshop ID",
                                key=f"param_{selected_service_for_action}_{selected_action}_workshopId"
                            )
                            params["status"] = st.selectbox(
                                "Status",
                                options=["IN_PROGRESS", "COMPLETED"],
                                key=f"param_{selected_service_for_action}_{selected_action}_status"
                            )
                            params["completionDate"] = st.text_input(
                                "Completion Date (ISO format)",
                                placeholder="2025-08-19T15:57:00",
                                key=f"param_{selected_service_for_action}_{selected_action}_completionDate"
                            )
                            params["rating"] = st.number_input(
                                "Rating (1-5)",
                                min_value=1,
                                max_value=5,
                                value=5,
                                key=f"param_{selected_service_for_action}_{selected_action}_rating"
                            )
                        else:
                            # Fallback for unknown tools
                            if selected_tool and 'parameters' in selected_tool:
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

    if prompt := st.chat_input("🤖 AI Workshop Planner에게 물어보세요! (예: '내 스킬에 맞는 워크샵 추천해주세요', '사용자 추가해주세요')"):
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
