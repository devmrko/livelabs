"""
AI Reasoning Engine for LiveLabs MCP Service Selection
Handles dynamic multi-step workflow reasoning using Oracle GenAI
"""

import json
import logging
from typing import Dict, Any, List
from .genai_client import OracleGenAIClient

logger = logging.getLogger(__name__)

def log_step(step_name: str, message: str):
    """Log step information"""
    logger.info(f"[{step_name}] {message}")

class AIReasoner:
    """AI 추론 엔진 - OCI GenAI를 사용한 도구 선택 및 쿼리 분석"""
    
    def __init__(self, services_config: Dict[str, Any]):
        log_step("AIReasoner", "AI 추론 엔진 초기화")
        self.genai_client = OracleGenAIClient()  # Oracle GenAI 클라이언트
        self.services = services_config
    
    def reason_about_query(self, user_query: str, previous_results: List[Dict] = None) -> Dict[str, Any]:
        """사용자 쿼리 분석 및 적절한 서비스/액션 결정 (동적 다단계 지원)"""
        log_step("AIReasoner", f"쿼리 분석 중: '{user_query}'")
        
        # 각 단계별 사용할 모델 정의
        reasoning_model = "cohere.command-r-plus-08-2024"
        
        # 1단계: LLM에게 해야 할 일에 대해 생각하도록 요청
        thinking_prompt = self._create_reasoning_prompt(user_query, previous_results)
        thinking_result = self._ai_think_about_query(thinking_prompt, user_query, reasoning_model)
        
        # 2단계: 개선된 프롬프트로 서비스 결정
        decision_prompt = self._create_reasoning_prompt(user_query, previous_results)
        ai_analysis = self._ai_analyze_query(decision_prompt, user_query, reasoning_model)
        
        # 결과 결합 및 모델 정보 추가
        ai_analysis["thinking_process"] = thinking_result
        ai_analysis["models_used"] = {
            "reasoning_model": reasoning_model,
            "summarization_model": "meta.llama-4-scout-17b-16e-instruct"
        }
        
        # 이전 단계가 사용자 프로필 쿼리이고, 현재 단계가 아직 설정되지 않은 경우
        if previous_results and previous_results[-1].get("service") == "livelabs-nl-query" and not ai_analysis.get("service"):
            # Clean up the query by removing SQL and context from previous steps
            clean_query = user_query.split('|')[0].strip()  # Take only the part before the first |
            clean_query = clean_query.replace('sql_query:', '').replace('livelabs-nl-query context:', '').strip()
            
            ai_analysis = {
                "service": "livelabs-semantic-search",
                "tool": "search_livelabs_workshops",
                "parameters": {"query": clean_query},
                "reasoning": "사용자 프로필 쿼리 후 워크샵 검색을 위한 시맨틱 검색 실행",
                "confidence": 0.8,
                "workflow_complete": True
            }
        
        # 완료 상태 동적 감지
        ai_analysis["workflow_complete"] = self._assess_completion_status(
            user_query, ai_analysis, previous_results
        )
        
        # LLM이 완전히 실패한 경우 기본 폴백 제공
        if ai_analysis.get("error") and not ai_analysis.get("service"):
            log_step("AIReasoner", "LLM 완전 실패, 기본 폴백 사용")
            query_lower = user_query.lower()
            if any(word in query_lower for word in ["i am", "my name", "what should i"]):
                ai_analysis = {
                    "service": "livelabs-nl-query",
                    "tool": "query_database_nl", 
                    "parameters": {"natural_language_query": user_query},
                    "reasoning": "폴백: 개인 쿼리 감지됨",
                    "confidence": 0.5,
                    "workflow_complete": False
                }
            else:
                # Clean up the query by removing SQL and context from previous steps
                clean_query = user_query.split('|')[0].strip()  # Take only the part before the first |
                clean_query = clean_query.replace('sql_query:', '').replace('livelabs-nl-query context:', '').strip()
                
                ai_analysis = {
                    "service": "livelabs-semantic-search",
                    "tool": "search_livelabs_workshops",
                    "parameters": {"query": clean_query}, 
                    "reasoning": "폴백: 일반 검색",
                    "confidence": 0.5,
                    "workflow_complete": True
                }
            ai_analysis["thinking_process"] = thinking_result
        
        log_step("AIReasoner", f"AI 사고 과정: {thinking_result.get('thought_process', '사고 과정 없음')}")
        log_step("AIReasoner", f"AI 선택 서비스: {ai_analysis.get('service')}, 도구: {ai_analysis.get('tool')}")
        log_step("AIReasoner", f"워크플로우 완료 상태: {ai_analysis.get('workflow_complete')}")
        
        return ai_analysis
    
    def _assess_completion_status(self, user_query: str, current_analysis: Dict, previous_results: List[Dict] = None) -> bool:
        """현재 단계 결과를 바탕으로 워크플로우 완료 여부 동적 판단"""
        if not previous_results:
            # 첫 번째 단계 - 개인화된 쿼리인지 확인
            query_lower = user_query.lower()
            is_personalized = any(word in query_lower for word in ["i am", "my name", "what should i", "who is"])
            
            # 개인화된 쿼리면 더 많은 단계가 필요할 가능성이 높음
            return not is_personalized
        
        # 이전 결과가 있는 경우
        step_count = len(previous_results)
        last_step = previous_results[-1] if previous_results else None
        
        # 이전 단계가 사용자 프로필 쿼리이고, 아직 semantic search를 하지 않은 경우
        if last_step and last_step.get("service") == "livelabs-nl-query":
            # 사용자 프로필 쿼리 다음에는 반드시 semantic search가 와야 함
            return False
            
        # semantic search 이후거나, 2단계 이상 실행했으면 완료
        if step_count >= 2 or (last_step and last_step.get("service") == "livelabs-semantic-search"):
            return True
            
        return False
    
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
    
    def _create_reasoning_prompt(self, user_query: str, previous_results: List[Dict] = None) -> str:
        """AI가 다음 행동을 결정하기 위한 상세한 프롬프트를 생성합니다.

        이 메서드는 AI가 다음에 사용할 서비스와 도구를 정보에 입각해 결정하는 데
        필요한 모든 컨텍스트를 제공하는 프롬프트를 구성합니다. 프롬프트에는 다음이 포함됩니다:
        1.  사용 가능한 서비스 및 해당 도구(엔드포인트)의 동적으로 생성된 목록과
            선택을 안내하는 "사용 시점" 힌트.
        2.  사용자의 원본 쿼리.
        3.  성공 또는 실패 여부를 포함하여 다단계 워크플로우에서 이전에 실행된 단계의 요약.
        4.  일반적인 시나리오(예: 개인화된 쿼리 대 일반 쿼리)에 대한 결정 규칙 집합.
        5.  AI의 응답을 안정적으로 파싱할 수 있도록 보장하는 필수 JSON 출력 형식의 엄격한 정의.

        Args:
            user_query (str): 사용자의 초기 쿼리.
            previous_results (List[Dict]): 워크플로우의 이전 단계를 나타내는 딕셔너리 리스트.

        Returns:
            str: AI 모델의 프롬프트로 사용될 형식화된 문자열.
        """
        # 1. 사용 가능한 서비스 및 도구 목록 생성
        services_desc = []
        for service_key, service_config in self.services.items():
            service_use_when = service_config.get("use_when", [])
            endpoint_list = []
            for endpoint_name in service_config.get("endpoints", {}).items():
                # 'health', 'tools' 같은 유틸리티 엔드포인트는 건너뜁니다.
                if endpoint_name not in ["health", "tools"]:
                    endpoint_list.append(f"   - {endpoint_name}: {service_config['description']}")
            
            use_when_text = f" (Use when: {', '.join(service_use_when)})" if service_use_when else ""
            services_desc.append(f"{service_key}{use_when_text}:\n" + "\n".join(endpoint_list))
        
        services_text = "\n\n".join(services_desc)
        
        # 2. 이전 단계 실행 결과가 있는 경우, 컨텍스트 정보 생성
        context_info = ""
        if previous_results:
            context_info = f"\n\nPREVIOUS STEPS COMPLETED:\n" # 이전 단계 완료
            for i, result in enumerate(previous_results, 1):
                service = result.get('service', 'unknown')
                action = result.get('action', 'unknown')
                success = result.get('result', {}).get('success', False)
                context_info += f"Step {i}: {service}.{action} - {'✅ Success' if success else '❌ Failed'}\n"
                
                # 컨텍스트를 위한 결과 요약 추가
                if success and result.get('result'):
                    res_data = result['result']
                    # 이전 단계 결과에서 'success'를 제외한 키를 요약에 추가
                    summary_keys = [k for k in res_data.keys() if k != 'success']
                    if summary_keys:
                        context_info += f"  → 이전 단계 결과: {', '.join(summary_keys)} 키를 포함한 데이터가 반환되었습니다.\n"
        
        # 3. 최종 프롬프트 조립
        return f"""You are a service selector for LiveLabs workshop recommendations. 

# 사용 가능한 MCP 서비스 및 도구:
{services_text}

# 사용자 쿼리: "{user_query}"{context_info}

# 결정 규칙:
- 이름이 포함된 개인화 쿼리 → 'livelabs-nl-query'로 시작한 후 'livelabs-semantic-search' 사용
- 일반 쿼리 → 'livelabs-semantic-search' 직접 사용
- 업데이트/진행 관련 쿼리 → 'livelabs-user-progression' 서비스 사용
- 이전 단계가 성공적으로 완료된 경우, 추가 단계가 필요한지 판단

# 도구별 매개변수 예시:
- livelabs-semantic-search.search: {{"query": "사용자 검색어"}}
- livelabs-nl-query.query: {{"natural_language_query": "사용자의 자연어 질문"}}
- livelabs-user-progression.update_skills: {{"user_id": "사용자 ID 또는 이름", "skills": ["스킬1", "스킬2"]}}
- livelabs-user-progression.complete_workshop: {{"user_id": "사용자 ID 또는 이름", "workshop_id": "워크숍 ID 또는 이름"}}
- livelabs-user-progression.get_progress: {{"user_id": "사용자 ID 또는 이름"}}

# 필수 출력 형식:
{{"service": "서비스-이름", "tool": "엔드포인트-이름", "parameters": {{"키": "값"}}, "reasoning": "설명", "workflow_complete": true/false}}

# 중요:
- "tool" 필드에는 서비스 이름이 아닌 엔드포인트 이름(예: "query", "search", "update_skills")을 사용하세요.
- 'workflow_complete'는 다음과 같이 설정하세요:
  - false: 개인화된 쿼리의 첫 단계일 경우 (사용자 데이터가 먼저 필요함)
  - true: 사용자의 요청을 완료하는 경우 (일반 검색 또는 다단계의 마지막 단계)

# 다음 쿼리에 대해 유효한 JSON으로 응답하세요: "{user_query}"
"""
    
    def _ai_analyze_query(self, prompt: str, user_query: str, model_name: str) -> Dict[str, Any]:
        """LLM을 사용하여 쿼리 분석 및 서비스 선택"""
        log_step("AIAnalyzeQuery", f"LLM 호출하여 분석: '{user_query}'")
        
        response = self.genai_client.chat_json(
            prompt=prompt,
            model_name=model_name,
            max_tokens=300
        )
        
        if response["success"]:
            log_step("AIAnalyzeQuery", f"JSON 응답 성공적으로 받음: {response['json']}")
            return response["json"]
        else:
            log_step("AIAnalyzeQuery", f"GenAI 호출 실패: {response.get('error', '알 수 없는 오류')}")
            return {"error": response.get("error", "genai_failed"), "raw": response.get("raw_text", "")}

    def _create_thinking_prompt(self, user_query: str, previous_results: List[Dict] = None) -> str:
        """LLM이 해야 할 일에 대해 생각하도록 하는 프롬프트 생성"""
        schema = (
            '{"query_type":"personal_recommendation|general_search|update_request","user_mentioned":"string|null","needs_user_context":true,'
            '"thought_process":"string","recommended_approach":"string"}'
        )
        context_info = ""
        if previous_results:
            context_info = f"\n\nPrevious Steps Completed:\n"
            for i, result in enumerate(previous_results, 1):
                context_info += f"Step {i}: {result.get('service', 'unknown')}.{result.get('action', 'unknown')} - "
                context_info += f"{'Success' if result.get('result', {}).get('success') else 'Failed'}\n"
        
        return f"""
You are an AI assistant analyzing a user's query to understand what information you need to give the best possible answer.

User Query: "{user_query}"{context_info}

Think deeply about this query and what you need to do:

1. What is the user asking for?
2. What information would help give a better answer?
3. What's your reasoning strategy?

OUTPUT RULES (MANDATORY):
- Return ONLY a single JSON object on one line. No markdown, no prose, no code fences.
- Use only double quotes for all keys and strings.

JSON Schema: {schema}

Analyze and respond with JSON:"""

    def _ai_think_about_query(self, prompt: str, user_query: str, model_name: str) -> Dict[str, Any]:
        """LLM을 사용하여 쿼리에 대해 생각하도록 함"""
        log_step("AIThinkQuery", f"LLM 사고 과정 호출: '{user_query}'")
        
        response = self.genai_client.chat_json(
            prompt=prompt,
            model_name=model_name,
            max_tokens=400
        )
        
        if response["success"]:
            log_step("AIThinkQuery", f"사고 과정 JSON 응답 성공: {response['json']}")
            return response["json"]
        else:
            log_step("AIThinkQuery", f"사고 과정 GenAI 호출 실패: {response.get('error', '알 수 없는 오류')}")
            return {
                "query_type": "unknown",
                "user_mentioned": None,
                "needs_user_context": False,
                "thought_process": f"사고 과정 생성 실패: {response.get('error', '알 수 없는 오류')}",
                "recommended_approach": "기본 검색 사용"
            }
