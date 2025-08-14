#!/usr/bin/env python3
"""
Reasoning + Acting Example using Oracle GenAI
Demonstrates structured reasoning, action planning, and execution
"""

import logging
import json
import os
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your OCILLMProvider
import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference import models as genai_models

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OCILLMProvider:
    """Simplified OCI LLM provider for the reasoning + acting example"""
    
    def __init__(self, model_id: str = "xai.grok-4"):
        self.model_id = model_id
        self.compartment_id = os.getenv('OCI_COMPARTMENT_ID')
        self.endpoint = os.getenv('OCI_GENAI_ENDPOINT')
        self.config_file_path = os.path.expanduser(os.getenv('OCI_CONFIG_PATH', '~/.oci/config'))
        self.config_profile = os.getenv('OCI_CONFIG_PROFILE', 'DEFAULT')
        
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OCI Generative AI client"""
        try:
            oci_config = oci.config.from_file(
                file_location=self.config_file_path,
                profile_name=self.config_profile
            )
            
            if not self.compartment_id and oci_config.get("tenancy"):
                self.compartment_id = oci_config.get("tenancy")
                logger.info(f"Using tenancy ID {self.compartment_id} as compartment ID")
            
            client = GenerativeAiInferenceClient(
                config=oci_config,
                service_endpoint=self.endpoint,
                retry_strategy=oci.retry.NoneRetryStrategy(),
                timeout=(10, 240)
            )
            
            logger.info(f"OCI GenAI client initialized with model: {self.model_id}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize OCI client: {e}")
            return None
    
    def generate_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> Optional[str]:
        """Generate response from OCI GenAI"""
        if not self.client:
            logger.error("OCI client not initialized")
            return None
        
        try:
            content = genai_models.TextContent(text=prompt, type="TEXT")
            message = genai_models.Message(role="USER", content=[content])
            
            chat_request = genai_models.GenericChatRequest(
                api_format=genai_models.BaseChatRequest.API_FORMAT_GENERIC,
                messages=[message],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            chat_details = genai_models.ChatDetails(
                serving_mode=genai_models.OnDemandServingMode(model_id=self.model_id),
                chat_request=chat_request,
                compartment_id=self.compartment_id
            )
            
            response = self.client.chat(chat_details)
            return response.data.chat_response.choices[0].message.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None

class MockTools:
    """Mock tools that the AI can use"""
    
    def __init__(self):
        # Mock database data
        self.mock_db_data = {
            "workshops": [
                {
                    "id": "648",
                    "title": "Oracle Cloud Infrastructure Core Services 시작하기",
                    "description": "OCI의 기본 서비스 탐색: 네트워킹, 컴퓨팅, 스토리지 등",
                    "duration": "2시간 30분",
                    "views": 223466,
                    "last_updated": "2024-01-15",
                    "category": "OCI Basics"
                },
                {
                    "id": "1070",
                    "title": "Oracle Database 23c 새로운 기능",
                    "description": "Oracle Database 23c의 최신 기능들 소개",
                    "duration": "1시간 45분",
                    "views": 156789,
                    "last_updated": "2023-12-20",
                    "category": "Database"
                },
                {
                    "id": "892",
                    "title": "Oracle Cloud Security 모범 사례",
                    "description": "OCI에서 보안을 강화하는 방법과 모범 사례",
                    "duration": "3시간",
                    "views": 98765,
                    "last_updated": "2024-02-10",
                    "category": "Security"
                },
                {
                    "id": "445",
                    "title": "Oracle 12c Database 관리",
                    "description": "Oracle 12c 데이터베이스 관리 및 유지보수",
                    "duration": "2시간",
                    "views": 45678,
                    "last_updated": "2020-05-15",
                    "category": "Database"
                }
            ]
        }
        
        # Mock vector embeddings (simplified)
        self.mock_embeddings = {
            "cloud_computing": ["648", "892"],
            "database": ["1070", "445"],
            "security": ["892"],
            "oci": ["648", "892"],
            "oracle_12c": ["445"],
            "oracle_23c": ["1070"]
        }
    
    def search_database(self, query: str) -> dict:
        """Mock database search using SQL-like queries"""
        print(f"🔍 데이터베이스 검색 실행: {query}")
        
        results = []
        query_lower = query.lower()
        
        for workshop in self.mock_db_data["workshops"]:
            # Simple keyword matching
            if any(keyword in workshop["title"].lower() or keyword in workshop["description"].lower() 
                   for keyword in query_lower.split()):
                results.append(workshop)
        
        return {
            "query": query,
            "results": results,
            "count": len(results),
            "status": "SUCCESS"
        }
    
    def vector_search(self, query: str, top_k: int = 5) -> dict:
        """Mock vector search using semantic similarity"""
        print(f"🔍 벡터 검색 실행: {query} (상위 {top_k}개)")
        
        query_lower = query.lower()
        results = []
        
        # Simple semantic matching
        for topic, workshop_ids in self.mock_embeddings.items():
            if any(word in topic for word in query_lower.split()):
                for workshop_id in workshop_ids:
                    workshop = next((w for w in self.mock_db_data["workshops"] if w["id"] == workshop_id), None)
                    if workshop:
                        results.append({
                            **workshop,
                            "similarity_score": 0.85 + (len(results) * 0.05)  # Mock similarity score
                        })
        
        # Sort by similarity score and limit results
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        results = results[:top_k]
        
        return {
            "query": query,
            "results": results,
            "count": len(results),
            "top_k": top_k,
            "status": "SUCCESS"
        }

class ReasoningActor:
    """Reasoning + Acting agent using Oracle GenAI with tools"""
    
    def __init__(self):
        self.llm = OCILLMProvider()
        self.tools = MockTools()
        self.memory = []
    
    def _fix_json_string(self, json_str: str) -> str:
        """Fix common JSON parsing issues"""
        # Remove trailing commas before closing braces/brackets
        import re
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix unclosed quotes by finding the last complete object
        brace_count = 0
        bracket_count = 0
        in_string = False
        escape_next = False
        
        for i, char in enumerate(json_str):
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
                
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                elif char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                
                # If we have unbalanced braces/brackets, truncate
                if brace_count < 0 or bracket_count < 0:
                    json_str = json_str[:i]
                    break
        
        # Close any unclosed structures
        while bracket_count > 0:
            json_str += ']'
            bracket_count -= 1
        while brace_count > 0:
            json_str += '}'
            brace_count -= 1
            
        return json_str
    
    def _extract_partial_plan(self, response: str) -> Dict:
        """Extract partial plan information from failed JSON response"""
        try:
            # Try to extract reasoning
            reasoning_start = response.find('"reasoning":')
            if reasoning_start != -1:
                reasoning_start = response.find('"', reasoning_start + 11) + 1
                reasoning_end = response.find('"', reasoning_start)
                if reasoning_end != -1:
                    reasoning = response[reasoning_start:reasoning_end]
                else:
                    reasoning = "부분적 추론 추출됨"
            else:
                reasoning = "추론을 찾을 수 없음"
            
            # Try to extract plan steps
            plan_steps = []
            step_pattern = r'"step":\s*(\d+).*?"action":\s*"([^"]*)"'
            import re
            matches = re.findall(step_pattern, response, re.DOTALL)
            
            for i, (step_num, action) in enumerate(matches[:3]):  # Limit to 3 steps
                plan_steps.append({
                    "step": int(step_num),
                    "action": action.strip(),
                    "reason": f"부분적 응답에서 추출됨",
                    "expected_outcome": "결정 예정"
                })
            
            if not plan_steps:
                plan_steps = [{
                    "step": 1,
                    "action": "워크샵 데이터 분석",
                    "reason": "부분적 응답에서 추출됨",
                    "expected_outcome": "데이터 분석 결과"
                }]
            
            return {
                "reasoning": reasoning,
                "plan": plan_steps,
                "risks": ["부분적 응답 - 일부 정보가 누락될 수 있음"],
                "success_criteria": ["사용 가능한 데이터의 완전한 분석"]
            }
            
        except Exception as e:
            logger.error(f"Failed to extract partial plan: {e}")
            return None
    
    def _create_default_reflection(self) -> Dict:
        """Create a default reflection when parsing fails"""
        return {
            "success_rate": "알 수 없음",
            "key_insights": ["일부 단계가 성공적으로 완료됨", "JSON 파싱 문제 발생"],
            "improvements": ["오류 처리 개선", "응답 검증 추가"],
            "lessons_learned": ["Oracle GenAI 응답이 일관성이 없을 수 있음", "더 나은 대체 메커니즘 필요"],
            "recommendations": ["다른 프롬프트로 테스트", "재시도 로직 구현"]
        }
    
    def _create_default_execution_result(self, action: str, error_message: str, tools_used: list = None, tool_results: dict = None) -> Dict:
        """Create a default execution result when parsing fails"""
        result = {
            "action_executed": action,
            "result": f"작업 시도했지만 실패: {error_message}",
            "status": "FAILED",
            "data": {},
            "next_steps": ["다음 단계 계속", "수동 검증 필요"],
            "notes": f"다음 이유로 기본 결과 생성됨: {error_message}"
        }
        
        if tools_used:
            result["tools_used"] = tools_used
        if tool_results:
            result["tool_results"] = tool_results
            
        return result
    
    def _extract_partial_execution_result(self, response: str, action: str) -> Dict:
        """Extract partial execution result from failed JSON response"""
        try:
            # Try to extract action_executed
            action_executed = action
            
            # Try to extract result
            result_start = response.find('"result":')
            if result_start != -1:
                result_start = response.find('"', result_start + 9) + 1
                result_end = response.find('"', result_start)
                if result_end != -1:
                    result = response[result_start:result_end]
                else:
                    result = "부분적 실행 완료"
            else:
                result = "작업 시도했지만 응답 파싱 실패"
            
            # Try to extract status
            status = "PARTIAL"
            if '"status":' in response:
                status_match = response.find('"status":')
                if status_match != -1:
                    status_start = response.find('"', status_match + 9) + 1
                    status_end = response.find('"', status_start)
                    if status_end != -1:
                        status = response[status_start:status_end]
            
            # Try to extract notes
            notes_start = response.find('"notes":')
            if notes_start != -1:
                notes_start = response.find('"', notes_start + 8) + 1
                notes_end = response.find('"', notes_start)
                if notes_end != -1:
                    notes = response[notes_start:notes_end]
                else:
                    notes = "부분적 응답 추출됨"
            else:
                notes = "응답 파싱 실패했지만 작업은 시도됨"
            
            return {
                "action_executed": action_executed,
                "result": result,
                "status": status,
                "data": {},
                "next_steps": ["다음 단계 계속", "결과 수동 확인"],
                "notes": notes
            }
            
        except Exception as e:
            logger.error(f"Failed to extract partial execution result: {e}")
            return None
    
    def _extract_search_query(self, action: str) -> str:
        """Extract search query from action description"""
        # Simple keyword extraction
        keywords = ['Oracle', 'Database', 'Cloud', 'Security', 'OCI', '워크샵', '데이터베이스', '클라우드', '보안']
        
        for keyword in keywords:
            if keyword.lower() in action.lower():
                return keyword
        
        # Default fallback
        return "Oracle"
    
    def reason_and_plan(self, task: str, context: str = "") -> Dict:
        """Use LLM to reason about the task and create an action plan"""
        
        reasoning_prompt = f"""
당신은 지능적인 추론 에이전트입니다. 주어진 작업을 분석하고 구조화된 실행 계획을 수립하세요.

작업: {task}
맥락: {context}

중요: 간결하고 구조화된 JSON 응답을 제공하세요. 작업 설명은 간단하지만 명확하게 작성하세요.

다음 JSON 형식으로 응답해주세요:
{{
    "reasoning": "수행해야 할 작업에 대한 간단한 단계별 추론",
    "plan": [
        {{
            "step": 1,
            "action": "수행할 작업의 간단한 설명",
            "reason": "이 작업이 필요한 이유",
            "expected_outcome": "예상 결과"
        }}
    ],
    "risks": ["주요 잠재적 문제점들"],
    "success_criteria": ["성공을 측정하는 방법"]
}}

응답을 간결하게 유지하고 유효한 JSON 형식을 보장하세요.
"""
        
        response = self.llm.generate_response(reasoning_prompt, temperature=0.3)
        
        if response:
            try:
                # Try to extract JSON from response
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip()
                else:
                    # Look for JSON-like structure
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    json_str = response[start:end]
                
                # Try to fix common JSON issues
                json_str = self._fix_json_string(json_str)
                
                plan = json.loads(json_str)
                logger.info("Successfully generated reasoning and plan")
                return plan
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.info(f"Raw response: {response}")
                
                # Try to extract partial information from the response
                partial_plan = self._extract_partial_plan(response)
                if partial_plan:
                    return partial_plan
                
                return {
                    "reasoning": "Failed to parse structured response",
                    "plan": [{"step": 1, "action": "Manual intervention required", "reason": "LLM response parsing failed"}],
                    "risks": ["Response parsing error"],
                    "success_criteria": ["Manual verification needed"]
                }
        
        return None
    
    def execute_action(self, action: str, context: Dict = None) -> Dict:
        """Execute a specific action and return results"""
        
        # Check if action requires tool usage
        tools_used = []
        tool_results = {}
        
        # Simple tool detection based on action content
        action_lower = action.lower()
        
        if any(keyword in action_lower for keyword in ['database', 'db', '검색', '조회', '데이터']):
            # Use database search
            search_query = self._extract_search_query(action)
            if search_query:
                tools_used.append("search_database")
                tool_results["database_search"] = self.tools.search_database(search_query)
        
        if any(keyword in action_lower for keyword in ['vector', '벡터', '유사', '의미', 'semantic']):
            # Use vector search
            search_query = self._extract_search_query(action)
            if search_query:
                tools_used.append("vector_search")
                tool_results["vector_search"] = self.tools.vector_search(search_query, top_k=3)
        
        # If no specific tools detected, try both for general queries
        if not tools_used and any(keyword in action_lower for keyword in ['워크샵', 'workshop', '분석', '찾기']):
            search_query = self._extract_search_query(action) or "Oracle"
            tools_used.append("search_database")
            tool_results["database_search"] = self.tools.search_database(search_query)
        
        execution_prompt = f"""
당신은 작업 실행 에이전트입니다. 다음 작업을 실행하고 결과를 제공하세요.

작업: {action}
맥락: {json.dumps(context) if context else "추가 맥락 없음"}

사용 가능한 도구:
1. search_database(query): 데이터베이스에서 워크샵 정보 검색
2. vector_search(query, top_k): 의미적 유사성을 기반으로 워크샵 검색

도구 사용 예시:
- 데이터베이스 검색이 필요한 경우: "search_database('Oracle Database')"
- 의미적 검색이 필요한 경우: "vector_search('클라우드 보안', 3)"

중요: 간결한 JSON 응답을 제공하세요. 설명을 간단하게 유지하세요.

다음 JSON 형식으로 응답해주세요:
{{
    "action_executed": "수행한 작업의 간단한 설명",
    "result": "성취한 내용의 간단한 요약",
    "status": "SUCCESS|FAILED|PARTIAL",
    "data": {{}},
    "next_steps": ["다음 작업"],
    "notes": "주요 관찰사항",
    "tools_used": ["사용한 도구들"]
}}

응답을 간결하게 유지하고 유효한 JSON 형식을 보장하세요.
"""
        
        response = self.llm.generate_response(execution_prompt, temperature=0.5)
        
        if response and response.strip():
            try:
                # Extract JSON from response
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip()
                else:
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    json_str = response[start:end]
                
                # Check if we have valid JSON content
                if not json_str or json_str.strip() == "":
                    logger.warning("Empty JSON response received")
                    return self._create_default_execution_result(action, "Empty response from LLM", tools_used, tool_results)
                
                # Try to fix common JSON issues
                json_str = self._fix_json_string(json_str)
                
                result = json.loads(json_str)
                
                # Add tool usage information
                if tools_used:
                    result["tools_used"] = tools_used
                    result["tool_results"] = tool_results
                
                logger.info(f"Action executed: {result.get('action_executed', 'Unknown')}")
                if tools_used:
                    logger.info(f"Tools used: {', '.join(tools_used)}")
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse execution result: {e}")
                
                # Try to extract partial execution result
                partial_result = self._extract_partial_execution_result(response, action)
                if partial_result:
                    return partial_result
                
                return self._create_default_execution_result(action, f"JSON parsing error: {e}", tools_used, tool_results)
        else:
            logger.warning("No response received from LLM")
            return self._create_default_execution_result(action, "No response from LLM", tools_used, tool_results)
        
        return None
    
    def reflect_and_improve(self, task: str, plan: Dict, results: List[Dict]) -> Dict:
        """Reflect on the execution and suggest improvements"""
        
        reflection_prompt = f"""
당신은 성찰 및 개선 에이전트입니다. 작업 실행을 분석하고 통찰을 제공하세요.

원본 작업: {task}
원본 계획: {json.dumps(plan, indent=2)}
실행 결과: {json.dumps(results, indent=2)}

다음 JSON 형식으로 분석을 제공해주세요:
{{
    "success_rate": "성공한 작업의 비율",
    "key_insights": ["실행에 대한 중요한 관찰사항들"],
    "improvements": ["계획을 개선할 수 있는 방법들"],
    "lessons_learned": ["이번 실행에서 배운 것들"],
    "recommendations": ["향후 유사한 작업에 대한 구체적인 권장사항들"]
}}
"""
        
        response = self.llm.generate_response(reflection_prompt, temperature=0.4)
        
        if response and response.strip():
            try:
                # Extract JSON from response
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip()
                else:
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    json_str = response[start:end]
                
                # Check if we have valid JSON content
                if not json_str or json_str.strip() == "":
                    logger.warning("Empty reflection response received")
                    return self._create_default_reflection()
                
                # Try to fix common JSON issues
                json_str = self._fix_json_string(json_str)
                
                reflection = json.loads(json_str)
                logger.info("Reflection and improvement analysis completed")
                return reflection
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse reflection: {e}")
                return self._create_default_reflection()
        else:
            logger.warning("No reflection response received from LLM")
            return self._create_default_reflection()
    
    def run_reasoning_acting_cycle(self, task: str, context: str = "") -> Dict:
        """Complete reasoning + acting cycle"""
        
        logger.info(f"Starting reasoning + acting cycle for task: {task}")
        
        # Step 1: Reason and Plan
        logger.info("Step 1: Reasoning and Planning...")
        plan = self.reason_and_plan(task, context)
        
        if not plan:
            logger.error("Failed to generate plan")
            return {"status": "FAILED", "error": "Plan generation failed"}
        
        logger.info(f"Generated plan with {len(plan.get('plan', []))} steps")
        
        # Step 2: Execute Actions
        logger.info("Step 2: Executing Actions...")
        results = []
        
        for step in plan.get('plan', []):
            action = step.get('action', 'Unknown action')
            logger.info(f"Executing step {step.get('step', '?')}: {action}")
            
            result = self.execute_action(action, {
                "step": step,
                "overall_plan": plan,
                "previous_results": results
            })
            
            results.append(result)
            
            if result and result.get('status') == 'FAILED':
                logger.warning(f"Action failed: {action}")
                break
        
        # Step 3: Reflect and Improve
        logger.info("Step 3: Reflecting and Improving...")
        reflection = self.reflect_and_improve(task, plan, results)
        
        # Compile final report
        final_report = {
            "task": task,
            "context": context,
            "plan": plan,
            "execution_results": results,
            "reflection": reflection,
            "status": "COMPLETED" if results else "FAILED"
        }
        
        logger.info("Reasoning + acting cycle completed")
        return final_report

def main():
    """Example usage of the reasoning + acting agent"""
    
    # Initialize the reasoning actor
    actor = ReasoningActor()
    
    # Example task: Analyze workshop data and provide insights
    task = """
    LiveLabs 스크래핑 프로젝트의 워크샵 텍스트를 분석하고 다음을 제공하세요:
    1. 가장 일반적인 주제와 테마의 요약
    2. 오래되었거나 업데이트가 필요한 워크샵 식별
    3. 콘텐츠 개선을 위해 우선순위를 정해야 할 워크샵에 대한 권장사항
    4. 현재 트렌드를 기반으로 한 새로운 워크샵 주제 제안
    """
    
    context = """
    Oracle LiveLabs에서 워크샵 텍스트를 스크래핑하여 MongoDB에 저장했습니다.
    데이터에는 워크샵 제목, 설명, 콘텐츠 및 메타데이터가 포함되어 있습니다.
    워크샵 제공의 품질과 관련성을 개선하고 싶습니다.
    """
    
    # Run the reasoning + acting cycle
    print("🚀 Oracle GenAI를 사용한 추론 + 실행 예제 시작")
    print("=" * 60)
    
    try:
        result = actor.run_reasoning_acting_cycle(task, context)
        
        # Display results
        print("\n📋 최종 보고서")
        print("=" * 60)
        print(f"작업: {result['task']}")
        print(f"상태: {result['status']}")
        
        if result and result.get('plan'):
            print(f"\n📝 생성된 계획:")
            print(f"추론: {result['plan'].get('reasoning', 'N/A')}")
            print(f"단계: {len(result['plan'].get('plan', []))}")
        
        if result and result.get('execution_results'):
            print(f"\n⚡ 실행 결과:")
            for i, res in enumerate(result['execution_results'], 1):
                if res:  # Check if result is not None
                    status = res.get('status', '알 수 없음')
                    action = res.get('action_executed', '알 수 없음')
                    tools = res.get('tools_used', [])
                    
                    print(f"  단계 {i}: {action} - {status}")
                    if tools:
                        print(f"    사용된 도구: {', '.join(tools)}")
                        if 'tool_results' in res:
                            for tool_name, tool_result in res['tool_results'].items():
                                if tool_result.get('count', 0) > 0:
                                    print(f"    {tool_name}: {tool_result['count']}개 결과")
                else:
                    print(f"  단계 {i}: 결과 없음")
        
        if result and result.get('reflection'):
            print(f"\n🤔 성찰 및 개선사항:")
            reflection = result['reflection']
            if reflection:  # Check if reflection is not None
                print(f"  성공률: {reflection.get('success_rate', 'N/A')}")
                print(f"  주요 통찰: {', '.join(reflection.get('key_insights', []))}")
                print(f"  권장사항: {', '.join(reflection.get('recommendations', []))}")
            else:
                print("  성찰 데이터 없음")
        
        # Save detailed report
        with open('reasoning_acting_report.json', 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 상세 보고서가 저장됨: reasoning_acting_report.json")
        
    except Exception as e:
        logger.error(f"추론 + 실행 사이클에서 오류 발생: {e}")
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    main() 