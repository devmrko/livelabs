"""
AI Reasoning Engine for LiveLabs MCP Service Selection
Handles dynamic multi-step workflow reasoning using Oracle GenAI
"""

import json
import logging
from typing import Dict, Any, List, Optional
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
        decision_prompt = self._create_decision_prompt(user_query, thinking_result, previous_results)
        ai_analysis = self._ai_make_decision(decision_prompt, user_query, reasoning_model)
        
        # 결과 결합 및 모델 정보 추가
        ai_analysis["thinking_process"] = thinking_result
        ai_analysis["models_used"] = {
            "reasoning_model": reasoning_model,
            "summarization_model": "meta.llama-4-scout-17b-16e-instruct"
        }
        
        # LLM이 완전히 실패한 경우에만 최소한의 폴백 제공
        if ai_analysis.get("error") and not ai_analysis.get("service"):
            log_step("AIReasoner", "LLM 완전 실패, 오류 반환")
            ai_analysis = {
                "service": None,
                "tool": None,
                "parameters": {},
                "reasoning": "AI가 쿼리를 분석할 수 없습니다. 다시 시도해 주세요.",
                "confidence": 0.0,
                "workflow_complete": True,
                "error": "AI 분석 실패"
            }
        
        log_step("AIReasoner", f"AI 사고 과정: {thinking_result.get('thought_process', '사고 과정 없음')}")
        log_step("AIReasoner", f"AI 선택 서비스: {ai_analysis.get('service')}, 도구: {ai_analysis.get('tool')}")
        log_step("AIReasoner", f"워크플로우 완료 상태: {ai_analysis.get('workflow_complete')}")
        
        return ai_analysis
        
        # # 완료 상태 동적 감지 (이미 설정되지 않은 경우에만)
        # if "workflow_complete" not in ai_analysis:
        #     ai_analysis["workflow_complete"] = self._assess_completion_status(
        #         user_query, ai_analysis, previous_results
        #     )
        
        # # LLM이 완전히 실패한 경우에만 최소한의 폴백 제공
        # if ai_analysis.get("error") and not ai_analysis.get("service"):
        #     log_step("AIReasoner", "LLM 완전 실패, 오류 반환")
        #     ai_analysis = {
        #         "service": None,
        #         "tool": None,
        #         "parameters": {},
        #         "reasoning": "AI가 쿼리를 분석할 수 없습니다. 다시 시도해 주세요.",
        #         "confidence": 0.0,
        #         "workflow_complete": True,
        #         "error": "AI 분석 실패"
        #     }
        #     ai_analysis["thinking_process"] = thinking_result
        
        # log_step("AIReasoner", f"AI 사고 과정: {thinking_result.get('thought_process', '사고 과정 없음')}")
        # log_step("AIReasoner", f"AI 선택 서비스: {ai_analysis.get('service')}, 도구: {ai_analysis.get('tool')}")
        # log_step("AIReasoner", f"워크플로우 완료 상태: {ai_analysis.get('workflow_complete')}")
        
        # return ai_analysis
    
    # def _assess_completion_status(self, user_query: str, current_analysis: Dict, previous_results: List[Dict] = None) -> bool:
    #     """현재 단계 결과를 바탕으로 워크플로우 완료 여부 동적 판단"""
    #     if not previous_results:
    #         # 첫 번째 단계 - 개인화된 쿼리인지 확인 (한국어 포함)
    #         query_lower = user_query.lower()
    #         is_personalized = any(word in query_lower for word in [
    #             "고정민", "내", "나의", "저의", "my", "i am", "what should i", "who is", "추천", "recommend"
    #         ])
            
    #         # 개인화된 쿼리면 더 많은 단계가 필요할 가능성이 높음
    #         return not is_personalized
        
    #     # 이전 결과가 있는 경우
    #     step_count = len(previous_results)
    #     last_step = previous_results[-1] if previous_results else None
        
    #     # 이전 단계가 사용자 프로필 쿼리이고, 아직 semantic search를 하지 않은 경우
    #     if last_step and last_step.get("service") == "livelabs-nl-query":
    #         # 사용자 프로필 쿼리 다음에는 반드시 semantic search가 와야 함
    #         return False
            
    #     # semantic search 이후거나, 2단계 이상 실행했으면 완료
    #     if step_count >= 2 or (last_step and last_step.get("service") == "livelabs-semantic-search"):
    #         return True
            
    #     return False
    
    # def _extract_json_from_text(self, text: str) -> Dict[str, Any] | None:
    #     """임의의 텍스트에서 코드 펜스나 중괄호 균형을 사용하여 첫 번째 유효한 JSON 객체 추출"""
    #     import re
    #     # 1) JSON 코드 블록 시도
    #     fence = re.search(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    #     if fence:
    #         candidate = fence.group(1).strip()
    #         try:
    #             return json.loads(candidate)
    #         except Exception:
    #             pass
    #     # 2) 모든 코드 블록 시도
    #     fence_any = re.search(r"```\s*([\s\S]*?)\s*```", text)
    #     if fence_any:
    #         candidate = fence_any.group(1).strip()
    #         try:
    #             return json.loads(candidate)
    #         except Exception:
    #             pass
    #     # 3) 첫 번째 객체에 대한 중괄호 균형 맞추기
    #     start = text.find('{')
    #     if start != -1:
    #         brace_count = 0
    #         in_string = False
    #         esc = False
    #         for i in range(start, len(text)):
    #             ch = text[i]
    #             if in_string:
    #                 if esc:
    #                     esc = False
    #                 elif ch == '\\':
    #                     esc = True
    #                 elif ch == '"':
    #                     in_string = False
    #             else:
    #                 if ch == '"':
    #                     in_string = True
    #                 elif ch == '{':
    #                     brace_count += 1
    #                 elif ch == '}':
    #                     brace_count -= 1
    #                     if brace_count == 0:
    #                         candidate = text[start:i+1]
    #                         try:
    #                             return json.loads(candidate)
    #                         except Exception:
    #                             break
    #     # 4) 모든 시도 실패
    #     return None
    
    def _create_reasoning_prompt(self, user_query: str, previous_results: List[Dict] = None) -> str:
        """LLM이 해야 할 일에 대해 생각하도록 하는 프롬프트 생성"""
        schema = (
            '{"query_type":"personal_recommendation|general_search|update_request|profile_lookup","user_mentioned":"string|null","needs_user_context":true|false,'
            '"thought_process":"string","recommended_approach":"string"}'
        )
        context_info = ""
        if previous_results:
            context_info = f"\n\nPrevious Steps Completed:\n"
            for i, result in enumerate(previous_results, 1):
                context_info += f"Step {i}: {result.get('service', 'unknown')}.{result.get('action', 'unknown')} - "
                context_info += f"{'Success' if result.get('result', {}).get('success') else 'Failed'}\n"
        
        return f"""You are an AI assistant analyzing a user's query to understand what information you need to give the best possible answer.

User Query: "{user_query}"{context_info}

Think deeply about this query and what you need to do:

1. What is the user asking for?
2. What information would help give a better answer? (e.g., user's name, user's skills, workshop search results)
3. What's your reasoning strategy? (e.g., look up user's profile first, then search workshops based on skills)

OUTPUT RULES (MANDATORY):
- Return ONLY a single JSON object on one line. No markdown, no prose, no code fences.
- Use only double quotes for all keys and strings.

JSON Schema: {schema}

Analyze and respond with JSON:"""

#         """
#         Create a fully prompt-driven reasoning system for AI Workshop Planner.
#         All decisions are made by the LLM through prompts, not hardcoded logic.
#         """
#         # Build available services and tools dynamically from MCP discovery
#         services_desc = []
#         for service_key, service_config in self.services.items():
#             service_desc = f"- {service_key}: {service_config.get('description', 'No description')}"
            
#             # Add discovered tools with parameter details if available
#             if service_config.get('tools_cache'):
#                 tools_info = []
#                 for tool in service_config['tools_cache'].get('tools', []):
#                     tool_name = tool.get('name', 'unknown')
#                     tool_desc = tool.get('description', 'No description')
                    
#                     # Add parameter information if available
#                     tool_line = f"  * {tool_name}: {tool_desc}"
                    
#                     # Try to get parameter info from inputSchema if available
#                     if hasattr(tool, 'inputSchema') and tool.inputSchema:
#                         properties = tool.inputSchema.get('properties', {})
#                         if properties:
#                             param_names = list(properties.keys())
#                             tool_line += f" (parameters: {', '.join(param_names)})"
                    
#                     tools_info.append(tool_line)
                
#                 if tools_info:
#                     service_desc += "\n" + "\n".join(tools_info)
            
#             services_desc.append(service_desc)
        
#         services_text = "\n\n".join(services_desc)
        
#         # Build context from previous results
#         context_info = ""
#         if previous_results:
#             context_info = f"\n\nPREVIOUS WORKFLOW CONTEXT:\n"
#             for i, result in enumerate(previous_results, 1):
#                 service = result.get('service', 'unknown')
#                 action = result.get('action', 'unknown')
#                 success = result.get('result', {}).get('success', False)
#                 context_info += f"Step {i}: {service}.{action} - {'Success' if success else 'Failed'}\n"
                
#                 if success and result.get('result'):
#                     # Add key information from successful results
#                     res_data = result['result']
#                     if isinstance(res_data, dict):
#                         important_keys = [k for k in res_data.keys() if k not in ['success', 'message']]
#                         if important_keys:
#                             context_info += f"  → Available data: {', '.join(important_keys)}\n"
        
#         return f"""You are an AI Workshop Planner that makes ALL decisions through reasoning, not hardcoded rules.

# AVAILABLE MCP SERVICES AND TOOLS:
# {services_text}

# USER QUERY: "{user_query}"{context_info}

# CRITICAL - TOOL NAME REQUIREMENTS:
# - You MUST use the exact tool names shown in the service descriptions above
# - DO NOT use service names as tool names (e.g., don't use "livelabs-user-progression" as a tool name)
# - Look at the tool list under each service and use those exact names
# - Example: For livelabs-user-progression service, use tools like "get_user", "add_user", etc.

# YOUR TASK:
# Analyze the user query and current context to determine:
# 1. What MCP service to use
# 2. What specific TOOL from that service to call (use EXACT tool names from above)
# 3. What parameters to use (including modified/enhanced queries when needed)
# 4. Whether this completes the workflow or more steps are needed

# MUST:
# because it is AI workshops planner, you must figure out the user's current situation(skill, workshop taken) if the inquiry needs
# then you can plan the next step by using the user's current situation

# QUERY MODIFICATION FOR TOOL CALLS:
# - For search_workshops: Enhance the query parameter with context from previous steps
# - For query_database_nl: Modify natural_language_query to be more specific based on context
# - For user tools: Use specific user identifiers from previous results
# - Always consider how to make the tool call more effective with available context


# DECISION PROCESS:
# - Consider the user's intent and what they're asking for
# - Look at previous workflow context if available
# - Modify queries/parameters to include relevant context from previous steps
# - Use the CORRECT tool names from the service descriptions above
# - Choose the most appropriate service and tool
# - Decide if workflow should continue (workflow_complete: false) or end (workflow_complete: true)

# WORKFLOW CONTINUATION LOGIC:
# - Set workflow_complete: false if you expect to need another step after this one
# - Set workflow_complete: true if this step should complete the user's request AND you have enough information to provide a comprehensive summary
# - Base this decision on the user's original query and what you're accomplishing

# PARAMETER ADAPTATION:
# - Adapt parameters to match the selected tool's requirements exactly
# - Use context from previous results to enhance parameter values
# - Ensure parameter names and types match the tool specification

# COMPLETION AND SUMMARY:
# - When setting workflow_complete: true, include a "summary" field with a comprehensive answer to the user's original question
# - The summary should synthesize all information gathered from previous workflow steps
# - Provide actionable recommendations based on the collected data

# RESPONSE FORMAT (JSON only, no explanations):
# {{"service": "service-name", "tool": "actual-tool-name-from-list", "parameters": {{"key": "value"}}, "reasoning": "your decision process", "workflow_complete": true/false, "query_modification": "explanation of how you modified the query/parameters", "summary": "comprehensive answer when workflow_complete is true"}}

# Make your decision based on reasoning about the user's needs, using the CORRECT tool names from the MCP discovery results above."""




    def _create_decision_prompt(self, user_query: str, thinking_result: Dict[str, Any], previous_results: Optional[List[Dict]] = None) -> str:
        """
        AI의 사고 과정을 바탕으로 실제 툴 호출을 결정하는 프롬프트 생성
        """
        services_desc = []
        for service_key, service_config in self.services.items():
            service_desc = f"- {service_config.get('name', service_key)} ({service_key}): {service_config.get('description', 'No description')}"
            
            if service_config.get('tools_cache'):
                tools_info = []
                for tool in service_config['tools_cache'].get('tools', []):
                    tool_name = tool.get('name', 'unknown')
                    tool_desc = tool.get('description', 'No description')
                    
                    tool_line = f"  * {tool_name}: {tool_desc}"
                    
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        properties = tool.inputSchema.get('properties', {})
                        if properties:
                            param_names = list(properties.keys())
                            tool_line += f" (parameters: {', '.join(param_names)})"
                    
                    tools_info.append(tool_line)
                
                if tools_info:
                    service_desc += "\n" + "\n".join(tools_info)
            
            services_desc.append(service_desc)
        
        services_text = "\n\n".join(services_desc)
        
        context_info = ""
        if previous_results:
            context_info = f"\n\nPREVIOUS WORKFLOW CONTEXT:\n"
            for i, result in enumerate(previous_results, 1):
                service = result.get('service', 'unknown')
                action = result.get('action', 'unknown')
                success = result.get('result', {}).get('success', False)
                context_info += f"Step {i}: {service}.{action} - {'Success' if success else 'Failed'}\n"
                
                if success and result.get('result'):
                    res_data = result['result']
                    if isinstance(res_data, dict):
                        important_keys = [k for k in res_data.keys() if k not in ['success', 'message', 'error']]
                        if important_keys:
                            context_info += f"  → Available data from this step: {', '.join(important_keys)}\n"
        
        thinking_text = thinking_result.get("thought_process", "사고 과정 없음")
        
        return f"""You are an AI Workshop Planner that makes ALL decisions through reasoning.
Your goal is to choose the most appropriate MCP tool to execute for the current step.

AVAILABLE MCP SERVICES AND TOOLS:
{services_text}

USER QUERY: "{user_query}"
AI THINKING PROCESS: {thinking_text}
{context_info}

CRITICAL - TOOL NAME REQUIREMENTS:
- You MUST use the exact tool names shown in the service descriptions above
- DO NOT use service names as tool names (e.g., don't use "livelabs-user-profiles" as a tool name)
- Look at the tool list under each service and use those exact names

YOUR TASK:
Analyze the user query, AI thinking process, and current context to determine:
1. What MCP service to use.
2. What specific TOOL from that service to call (use EXACT tool names from above).
3. What parameters to use.
4. Whether this single step completes the entire workflow or more steps are needed.

DECISION PROCESS:
- Use the provided AI THINKING PROCESS to guide your decision.
- If a user lookup is needed first (e.g., for personalized recommendations), choose a user-related tool.
- If the user is asking to add or update data, choose the corresponding update tool.
- If a search is needed, choose a search tool.
- Use the CORRECT tool names from the service descriptions.

WORKFLOW CONTINUATION LOGIC:
- Set "workflow_complete": false if this is an intermediate step (e.g., getting user profile before searching workshops).
- Set "workflow_complete": true if this step should provide the final answer.

RESPONSE FORMAT (JSON only, no explanations):
{{"service": "service-name", "tool": "actual-tool-name-from-list", "parameters": {{"key": "value"}}, "reasoning": "your decision process", "workflow_complete": true/false}}"""

    def _ai_think_about_query(self, prompt: str, user_query: str, model_name: str) -> Dict[str, Any]:
        """LLM을 사용하여 쿼리에 대해 생각하도록 함"""
        log_step("AIThinkQuery", f"LLM 사고 과정 호출: '{user_query}'")
        
        response = self.genai_client.chat_json( 
            prompt=prompt,
            model_name=model_name,
            max_tokens=300,
            retry_on_invalid_json=True
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







    def _ai_analyze_query(self, prompt: str, user_query: str, model_name: str) -> Dict[str, Any]:
        """LLM을 사용하여 쿼리 분석 및 서비스 선택"""
        log_step("AIAnalyzeQuery", f"LLM 호출하여 분석: '{user_query}'")
        
        response = self.genai_client.chat_json(
            prompt=prompt,
            model_name=model_name,
            max_tokens=200,
            retry_on_invalid_json=True
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

    def _ai_make_decision(self, prompt: str, user_query: str, model_name: str) -> Dict[str, Any]:
        """LLM을 사용하여 쿼리 분석 및 서비스 선택"""
        log_step("AIMakeDecision", f"LLM 호출하여 분석: '{user_query}'")
        
        response = self.genai_client.chat_json(
            prompt=prompt,
            model_name=model_name,
            max_tokens=200,
            retry_on_invalid_json=True
        )
        
        if response["success"]:
            log_step("AIMakeDecision", f"JSON 응답 성공적으로 받음: {response['json']}")
            return response["json"]
        else:
            log_step("AIMakeDecision", f"GenAI 호출 실패: {response.get('error', '알 수 없는 오류')}")
            return {"error": response.get("error", "genai_failed"), "raw": response.get("raw_text", "")}

    def _ai_think_about_query(self, prompt: str, user_query: str, model_name: str) -> Dict[str, Any]:
        """LLM을 사용하여 쿼리에 대해 생각하도록 함"""
        log_step("AIThinkQuery", f"LLM 사고 과정 호출: '{user_query}'")
        
        response = self.genai_client.chat_json( 
            prompt=prompt,
            model_name=model_name,
            max_tokens=300,
            retry_on_invalid_json=True
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
