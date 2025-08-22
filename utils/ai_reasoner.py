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
        refinement_model = "cohere.command-r-plus-08-2024" # 파라미터 개선을 위한 모델
        
        # 1단계: LLM에게 해야 할 일에 대해 생각하도록 요청
        thinking_prompt = self._create_reasoning_prompt(user_query, previous_results)
        thinking_result = self._ai_think_about_query(thinking_prompt, user_query, reasoning_model)
        
        # 2단계: 개선된 프롬프트로 서비스 결정
        decision_prompt = self._create_decision_prompt(user_query, thinking_result, previous_results)
        ai_analysis = self._ai_make_decision(decision_prompt, user_query, reasoning_model)

        # 3단계: LLM으로부터 추출된 파라미터를 다시 한번 검증하고 개선 (신규 로직)
        if ai_analysis.get("service") and ai_analysis.get("tool"):
            log_step("AIReasoner", f"결정된 도구({ai_analysis.get('tool')})의 파라미터 개선 시작")
            ai_analysis = self.refine_parameters(user_query, ai_analysis, previous_results, refinement_model)
        
        # 결과 결합 및 모델 정보 추가
        ai_analysis["thinking_process"] = thinking_result
        if "models_used" not in ai_analysis:
            ai_analysis["models_used"] = {}
        ai_analysis["models_used"]["reasoning_model"] = reasoning_model
        ai_analysis["models_used"]["summarization_model"] = "meta.llama-4-scout-17b-16e-instruct"
        
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
        log_step("AIReasoner", f"최종 파라미터: {ai_analysis.get('parameters')}")
        log_step("AIReasoner", f"워크플로우 완료 상태: {ai_analysis.get('workflow_complete')}")
        
        return ai_analysis
        
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
                        # 성공, 메시지, 오류 같은 메타데이터를 제외하고 실제 데이터 키만 추출
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
5. for workshop search it should be use skills or user inquiry rather use user's name or email.

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

    # =================================================================
    # 신규 추가된 파라미터 개선 로직
    # =================================================================
    def refine_parameters(self, user_query: str, current_analysis: Dict[str, Any], previous_results: Optional[List[Dict]], model_name: str) -> Dict[str, Any]:
        """기존에 선택된 도구와 파라미터를 LLM을 통해 한번 더 검증하고 개선합니다."""
        log_step("ParameterRefiner", f"Refining parameters for tool: {current_analysis.get('tool')}")

        prompt = self._create_refinement_prompt(user_query, current_analysis, previous_results)
        
        response = self.genai_client.chat_json(
            prompt=prompt,
            model_name=model_name,
            max_tokens=300,
            retry_on_invalid_json=True
        )

        if response["success"] and response["json"]:
            log_step("ParameterRefiner", f"Parameter refinement successful: {response['json']}")
            # 원래 분석 결과에 개선된 파라미터와 추론 과정을 추가
            current_analysis["parameters"] = response["json"].get("refined_parameters", current_analysis["parameters"])
            current_analysis["refinement_reasoning"] = response["json"].get("reasoning", "No reasoning provided.")
            
            if "models_used" not in current_analysis:
                current_analysis["models_used"] = {}
            current_analysis["models_used"]["refinement_model"] = model_name
        else:
            log_step("ParameterRefiner", f"Parameter refinement failed: {response.get('error')}. Using initial parameters.")
            # 실패 시, 원래 분석 결과를 그대로 반환하고 실패 사실을 기록
            current_analysis["refinement_reasoning"] = f"Parameter refinement failed: {response.get('error')}"

        return current_analysis

    def _create_refinement_prompt(self, user_query: str, current_analysis: Dict[str, Any], previous_results: Optional[List[Dict]]) -> str:
        """파라미터 개선을 위한 프롬프트 생성"""
        service_name = current_analysis.get("service")
        tool_name = current_analysis.get("tool")
        initial_params = current_analysis.get("parameters", {})

        # 해당 서비스와 도구의 정보 찾기
        tool_info = "Unknown"
        tool_schema = {}
        service_config = self.services.get(service_name, {})
        if service_config.get('tools_cache'):
            for tool in service_config['tools_cache'].get('tools', []):
                if tool.get('name') == tool_name:
                    tool_desc = tool.get('description', 'No description')
                    param_info = ""
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        tool_schema = tool.inputSchema
                        properties = tool_schema.get('properties', {})
                        if properties:
                            param_names = list(properties.keys())
                            param_info = f" (Parameters: {', '.join(param_names)})"
                    tool_info = f"{tool_desc}{param_info}"
                    break

        context_info = ""
        if previous_results:
            context_info = f"\n\nPREVIOUS WORKFLOW CONTEXT:\n"
            context_data = []
            for i, result in enumerate(previous_results, 1):
                service = result.get('service', 'unknown')
                action = result.get('action', 'unknown')
                success = result.get('result', {}).get('success', False)
                
                step_summary = f"Step {i}: {service}.{action} - {'Success' if success else 'Failed'}"
                
                if success and result.get('result'):
                    res_data = result['result']
                    if isinstance(res_data, dict):
                        # 실제 결과 데이터만 JSON 문자열로 요약
                        data_payload = {k: v for k, v in res_data.items() if k not in ['success', 'message', 'error']}
                        if data_payload:
                           step_summary += f"\n  → Result data: {json.dumps(data_payload)}"
                context_data.append(step_summary)
            context_info = "\n".join(context_data)


        return f"""You are an AI assistant that refines and validates tool parameters based on the full context.

USER QUERY: "{user_query}"
{context_info}

---
AI's CURRENT PLAN:
- Selected Tool: {service_name}.{tool_name}
- Tool Description: {tool_info}
- Tool Parameter Schema: {json.dumps(tool_schema)}
- Initial Parameters decided by AI: {json.dumps(initial_params)}
---

YOUR TASK: 
Review the "Initial Parameters" and refine them for maximum accuracy and effectiveness.
1.  **Analyze Context**: Use the user query AND the data from "PREVIOUS WORKFLOW CONTEXT" to extract the most relevant values. For example, if the context has user skills, use those skills for a workshop search query instead of the user's name.
2.  **Validate & Correct**: Ensure the parameters fit the "Tool Parameter Schema". Correct any mistakes.
3.  **Enhance**: Make parameter values more specific if possible. For example, change a generic search for "database" to "OCI 23c new features" if the context suggests it.
4.  **No Change**: If the initial parameters are already optimal, return them as is.

CRITICAL: Extract values from the PREVIOUS WORKFLOW CONTEXT if they are available and relevant. For instance, if a user's profile was fetched in a previous step, use the 'skills' from that result for a subsequent search.

RESPONSE FORMAT (JSON only, no prose, no markdown):
{{"refined_parameters": {{...}}, "reasoning": "Explain concisely why you made the changes, or why no changes were needed. Mention if you used data from the previous context."}}
"""


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