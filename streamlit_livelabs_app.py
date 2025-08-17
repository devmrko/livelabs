#!/usr/bin/env python3
"""
Streamlit Chatbot App for LiveLabs MCP Services
Provides a conversational interface that reasons about user queries and calls appropriate MCP tools
"""

import streamlit as st
import asyncio
import json
import time
import threading
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
import re
import subprocess
import os
import signal
import psutil
import logging
import sys
import traceback

# MCP client imports
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolRequest, CallToolResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_step(step_name: str, details: str = "", data: Any = None):
    """Log a step with timestamp and details"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_message = f"[{timestamp}] 🔍 {step_name}"
    if details:
        log_message += f": {details}"
    
    # Log to console
    logger.info(log_message)
    
    # Log to Streamlit
    if 'debug_logs' not in st.session_state:
        st.session_state.debug_logs = []
    
    log_entry = {
        'timestamp': timestamp,
        'step': step_name,
        'details': details,
        'data': data
    }
    st.session_state.debug_logs.append(log_entry)
    
    # Keep only last 50 logs
    if len(st.session_state.debug_logs) > 50:
        st.session_state.debug_logs = st.session_state.debug_logs[-50:]

def display_debug_logs():
    """Display debug logs in the sidebar"""
    if 'debug_logs' in st.session_state and st.session_state.debug_logs:
        with st.sidebar:
            st.header("🔍 Debug Logs")
            
            # Show recent logs
            for log in st.session_state.debug_logs[-10:]:  # Show last 10 logs
                st.markdown(f"""
                <div class="debug-log">
                    <strong>[{log['timestamp']}]</strong> {log['step']}<br>
                    {log['details'] if log['details'] else ''}
                </div>
                """, unsafe_allow_html=True)
            
            # Clear logs button
            if st.button("🗑️ Clear Logs"):
                st.session_state.debug_logs = []
                st.rerun()

# Configure page
st.set_page_config(
    page_title="LiveLabs AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling with softer, more readable colors
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c5282;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .service-card {
        background-color: #f7fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #4a5568;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-success {
        color: #22543d;
        font-weight: bold;
    }
    .status-error {
        color: #742a2a;
        font-weight: bold;
    }
    .status-warning {
        color: #744210;
        font-weight: bold;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .user-message {
        background-color: #ebf8ff;
        border-left: 4px solid #3182ce;
        color: #2c5282;
    }
    .assistant-message {
        background-color: #f0fff4;
        border-left: 4px solid #38a169;
        color: #22543d;
    }
    .reasoning-box {
        background-color: #fffbeb;
        border: 1px solid #d69e2e;
        border-radius: 0.5rem;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-style: italic;
        color: #744210;
    }
    .tool-call {
        background-color: #f7fafc;
        border: 1px solid #a0aec0;
        border-radius: 0.5rem;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-family: monospace;
        color: #4a5568;
    }
    .stTextInput > div > div > input {
        border-radius: 25px;
        padding: 10px 20px;
        border: 1px solid #e2e8f0;
    }
    .stButton > button {
        border-radius: 25px;
        padding: 10px 20px;
        background-color: #4a5568;
        color: white;
        border: none;
    }
    .stButton > button:hover {
        background-color: #2d3748;
    }
    /* Make debug logs more readable */
    .debug-log {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
        color: #4a5568;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)

class MCPServiceManager:
    """Manages MCP service connections and interactions"""
    
    def __init__(self):
        log_step("MCPServiceManager", "Initializing service manager")

        self.services = {
            "semantic_search": {
                "name": "LiveLabs Semantic Search",
                "file": "mcp_livelabs_semantic_search.py",
                "status": "disconnected",
                "description": "Find and list available LiveLabs workshops. Use for queries like 'list workshops', 'find big data workshops', 'search for AI courses', or discovering workshop content by topic.",
                "tools": ["search_livelabs_workshops", "get_livelabs_statistics", "find_similar_livelabs_workshops"],
                "process": None,
                "port": None
            },
            "user_profiles": {
                "name": "LiveLabs User Profiles", 
                "file": "mcp_livelabs_user_profiles.py",
                "status": "disconnected",
                "description": "Access specific user account information and demographics. Use when asking about individual users like 'get John's profile' or 'find users who know Python'.",
                "tools": ["get_user_profile", "get_all_user_profiles", "search_users_by_skill", "get_user_statistics"],
                "process": None,
                "port": None
            },
            "user_skills": {
                "name": "LiveLabs User Skills & Progression",
                "file": "mcp_livelabs_user_skills_progression.py", 
                "status": "disconnected",
                "description": "Track user learning history and completed workshops. Use for queries about what users have already learned or their progress, NOT for finding available workshops.",
                "tools": ["query_user_skills_progression", "set_user_skills_ai_profile", "run_user_skills_example_queries"],
                "process": None,
                "port": None
            }
        }        

        log_step("MCPServiceManager", "Service manager initialized", {"services": list(self.services.keys())})
    
    def get_service_status(self, service_key: str) -> str:
        """Get current status of a service"""
        status = self.services[service_key]["status"]
        log_step("GetServiceStatus", f"Service {service_key} status: {status}")
        return status
    
    def set_service_status(self, service_key: str, status: str):
        """Set service status"""
        log_step("SetServiceStatus", f"Setting {service_key} status to {status}")
        self.services[service_key]["status"] = status
    
    def get_service_info(self, service_key: str) -> Dict:
        """Get service information"""
        log_step("GetServiceInfo", f"Getting info for {service_key}")
        return self.services[service_key]

    def test_service_connection(self, service_key: str) -> Dict:
        """Test connection to an MCP service by listing its tools."""
        log_step("TestServiceConnection", f"Testing connection to {service_key}")
        try:
            # Run the async test in the current event loop
            result = asyncio.run(self._test_service_async(service_key))
            if result.get("success"):
                self.set_service_status(service_key, "connected")
                st.toast(f"✅ Connection to {self.services[service_key]['name']} successful!", icon="✅")
            else:
                self.set_service_status(service_key, "error")
                st.toast(f"❌ Connection to {self.services[service_key]['name']} failed.", icon="❌")
            return result
        except Exception as e:
            self.set_service_status(service_key, "error")
            log_step("TestServiceConnection", f"Error testing {service_key}: {e}")
            st.toast(f"❌ Error testing {self.services[service_key]['name']}: {e}", icon="❌")
            return {"success": False, "error": str(e)}

    async def _test_service_async(self, service_key: str) -> Dict:
        """Async helper to test a service connection."""
        service = self.get_service_info(service_key)
        service_file = service.get('file')

        if not os.path.exists(service_file):
            return {"success": False, "error": "Service file not found"}

        from mcp.client.stdio import StdioServerParameters, stdio_client
        from mcp.client.session import ClientSession

        stdio_params = StdioServerParameters(command=sys.executable, args=[service_file])
        try:
            async with stdio_client(stdio_params) as (read, write):
                async with ClientSession(read, write) as session:
                # Wait for proper MCP initialization by checking server capabilities first
                max_wait_time = 15.0  # Total timeout
                start_time = asyncio.get_event_loop().time()
                
                while True:
                    try:
                        # First try to initialize - this will block until server is ready
                        await session.initialize()
                        
                        # If initialize succeeds, try listing tools
                        tools_result = await session.list_tools()
                        available_tools = [t.name for t in tools_result.tools]
                        return {"success": True, "available_tools": available_tools}
                        
                    except Exception as e:
                        current_time = asyncio.get_event_loop().time()
                        if current_time - start_time > max_wait_time:
                            raise Exception(f"Service failed to initialize within {max_wait_time}s: {e}")
                        
                        # Wait a bit before retrying
                        await asyncio.sleep(0.5)
                        continue
        except Exception as e:
            return {"success": False, "error": str(e)}
    





class AIReasoner:
    """AI-powered reasoning to determine which MCP tools to call"""
    
    def __init__(self, mcp_manager: MCPServiceManager):
        log_step("AIReasoner", "Initializing AI reasoner")
        self.mcp_manager = mcp_manager
        
        # Define available tools and their descriptions for AI reasoning
        self.available_tools = {
            "semantic_search": {
                "service_name": "LiveLabs Semantic Search",
                "tools": {
                    "search_livelabs_workshops": {
                        "description": "Search LiveLabs workshops using semantic similarity with natural language query",
                        "use_cases": [
                            "finding workshops about specific topics",
                            "searching for tutorials on particular technologies",
                            "looking for labs related to certain subjects"
                        ]
                    },
                    "get_livelabs_statistics": {
                        "description": "Get statistics about LiveLabs workshops in the database",
                        "use_cases": [
                            "counting total workshops",
                            "getting workshop statistics",
                            "understanding workshop distribution"
                        ]
                    },
                    "find_similar_livelabs_workshops": {
                        "description": "Find LiveLabs workshops similar to a specific workshop by ID",
                        "use_cases": [
                            "finding similar workshops",
                            "recommending related content",
                            "discovering workshop alternatives"
                        ]
                    }
                }
            },
            "user_profiles": {
                "service_name": "LiveLabs User Profiles",
                "tools": {
                    "get_user_profile": {
                        "description": "Get detailed profile information for a specific user",
                        "use_cases": [
                            "finding user information",
                            "getting user details",
                            "viewing user profiles"
                        ]
                    },
                    "get_all_user_profiles": {
                        "description": "Get all user profiles in the system",
                        "use_cases": [
                            "listing all users",
                            "getting user overview",
                            "user management"
                        ]
                    },
                    "search_users_by_skill": {
                        "description": "Search for users who have specific skills",
                        "use_cases": [
                            "finding users with particular skills",
                            "skill-based user search",
                            "expertise discovery"
                        ]
                    },
                    "get_user_statistics": {
                        "description": "Get statistics about users and their skills",
                        "use_cases": [
                            "user statistics",
                            "skill distribution analysis",
                            "user overview data"
                        ]
                    }
                }
            },
            "user_skills": {
                "service_name": "LiveLabs User Skills & Progression",
                "tools": {
                    "query_user_skills_progression": {
                        "description": "Query user skills and progression using natural language",
                        "use_cases": [
                            "asking about user skills",
                            "skill progression queries",
                            "natural language skill questions"
                        ]
                    },
                    "set_user_skills_ai_profile": {
                        "description": "Configure AI profile for user skills queries",
                        "use_cases": [
                            "AI configuration",
                            "setting up skill analysis"
                        ]
                    },
                    "run_user_skills_example_queries": {
                        "description": "Run example queries for user skills and progression",
                        "use_cases": [
                            "demonstration queries",
                            "example skill questions",
                            "testing skill queries"
                        ]
                    }
                }
            }
        }
        log_step("AIReasoner", "AI reasoner initialized", {"available_services": list(self.available_tools.keys())})
    
    def reason_about_query(self, user_query: str) -> Dict:
        """Use AI reasoning to analyze user query and determine appropriate action"""
        log_step("AIReasoning", f"Starting AI reasoning for query: '{user_query}'")
        
        # Create a comprehensive prompt for AI reasoning
        log_step("AIReasoning", "Creating reasoning prompt")
        reasoning_prompt = self._create_reasoning_prompt(user_query)
        
        # Use AI to analyze the query (simulated for now, replace with actual AI call)
        log_step("AIReasoning", "Analyzing query with AI")
        ai_analysis = self._ai_analyze_query(reasoning_prompt, user_query)
        
        # Extract the AI's reasoning and tool selection
        service_key = ai_analysis.get('service', 'user_skills')  # Default fallback
        tool = ai_analysis.get('tool', 'query_user_skills_progression')
        reasoning = ai_analysis.get('reasoning', 'Using natural language query as fallback')
        confidence = ai_analysis.get('confidence', 0.5)
        
        log_step("AIReasoning", f"AI selected service: {service_key}, tool: {tool}", {
            "reasoning": reasoning,
            "confidence": confidence
        })
        

        
        # Check if the selected service is available
        service_available = self.mcp_manager.get_service_status(service_key) == 'connected'
        log_step("AIReasoning", f"Service availability check", {
            "service": service_key,
            "available": service_available
        })
        
        return {
            'matched_pattern': None,  # No longer using regex patterns
            'action': {
                'service': service_key,
                'tool': tool,
                'description': reasoning
            },
            'service_available': service_available,
            'reasoning': reasoning,
            'confidence': confidence,
            'ai_analysis': ai_analysis
        }
    
    def _create_reasoning_prompt(self, user_query: str) -> str:
        """Create a comprehensive prompt for AI reasoning"""
        log_step("CreateReasoningPrompt", "Building AI reasoning prompt")
        
        # Build dynamic tools description by discovering available tools
        tools_description = ""
        for service_key, service_info in self.available_tools.items():
            tools_description += f"\n## Service Key: '{service_key}' - {service_info['service_name']}:\n"
            tools_description += f"Description: {service_info['description']}\n"
            
            # Note: Tools will be discovered dynamically at runtime
            tools_description += f"Available tools: Will be discovered dynamically from the MCP service\n"
            tools_description += f"Common tools for this service:\n"
            
            # Provide common tool patterns for each service
            if service_key == "semantic_search":
                tools_description += f"- search_livelabs_workshops: Search workshops by natural language query\n"
                tools_description += f"- get_livelabs_statistics: Get workshop statistics\n"
                tools_description += f"- find_similar_livelabs_workshops: Find similar workshops\n"
            elif service_key == "user_profiles":
                tools_description += f"- get_user_profile: Get specific user profile\n"
                tools_description += f"- search_users_by_skill: Find users with specific skills\n"
                tools_description += f"- get_user_statistics: Get user statistics\n"
            elif service_key == "user_skills_progression":
                tools_description += f"- query_user_skills_progression: Analyze user skills progression\n"
                tools_description += f"- set_user_skills_ai_profile: Set AI profile for skills\n"
        
        prompt = f"""
You are an AI assistant that analyzes user queries and determines which LiveLabs MCP tool to call.

Available tools and services:
{tools_description}

User Query: "{user_query}"

Please analyze this query and determine:
1. Which service should handle this query?
2. Which specific tool should be called?
3. What is your reasoning for this choice?
4. How confident are you (0.0 to 1.0)?

Consider the user's intent, the available tools, and choose the most appropriate service and tool.

KEYWORDS TO HELP YOU CHOOSE:
- For searching/finding workshops: "search", "find", "list", "show", "get workshops", "big data", "AI", "database", etc.
- For user profile information: "user", "profile", "skills", "experience", "user info", "my profile", etc.
- For skills progression: "progression", "progress", "skill level", "advancement", "learning path", "career", etc.

EXAMPLES:
- "find big data workshops" → service: "semantic_search", tool: "search_livelabs_workshops", params: {{"query": "big data workshops"}}
- "show my user profile" → service: "user_profiles", tool: "get_user_profile", params: {{"user_id": "current"}}
- "check my skill progression" → service: "user_skills_progression", tool: "analyze_user_progression", params: {{"query": "skill progression"}}
- "find users with Python skills" → service: "user_profiles", tool: "search_users_by_skill", params: {{"skill_name": "Python"}}
- "show statistics" → service: "semantic_search", tool: "get_livelabs_statistics", params: {{}}

Respond in JSON format:
{{
    "service": "semantic_search",
    "tool": "search_livelabs_workshops", 
    "reasoning": "detailed explanation of why this tool is appropriate",
    "confidence": 0.85,
    "extracted_parameters": {{
        "query": "big data workshops"
    }}
}}

IMPORTANT: 
1. Use the exact service key and tool name as shown above. For example:
   - Use "semantic_search" (not "LiveLabs Semantic Search")
   - Use "user_profiles" (not "LiveLabs User Profiles") 
   - Use "user_skills_progression" (not "LiveLabs User Skills Progression")

2. Return ONLY valid JSON. Do not add any text before or after the JSON object.
3. Make sure all strings are properly quoted and all brackets are closed.
4. The JSON must be complete and parseable.
"""
        log_step("CreateReasoningPrompt", "Reasoning prompt created")
        return prompt
    
    def _ai_analyze_query(self, prompt: str, user_query: str) -> Dict:
        """Call LLM to choose tool based on MCP config and user input"""
        log_step("AIAnalyzeQuery", f"Calling LLM to choose tool for: '{user_query}'")
        
        try:
            # Call OCI Generative AI with the prompt containing MCP config
            import oci
            from oci.generative_ai_inference import GenerativeAiInferenceClient
            
            # Initialize OCI client using same pattern as oci_embedding.py
            config = oci.config.from_file()
            compartment_id = config.get("tenancy")
            
            # Initialize client with same endpoint and settings as oci_embedding.py
            genai_client = GenerativeAiInferenceClient(
                config=config,
                service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
                retry_strategy=oci.retry.NoneRetryStrategy(),
                timeout=(10, 240)
            )
            
            # Call OCI GenAI using chat API for Cohere Command
            content = oci.generative_ai_inference.models.TextContent(text=prompt, type="TEXT")
            message = oci.generative_ai_inference.models.Message(role="USER", content=[content])
            
            chat_request_params = {
                "api_format": oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC,
                "messages": [message],
                "max_tokens": 500,
                "temperature": 0.1
            }
            chat_request = oci.generative_ai_inference.models.GenericChatRequest(**chat_request_params)

            chat_details = oci.generative_ai_inference.models.ChatDetails(
                serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(model_id="xai.grok-4"),
                chat_request=chat_request,
                compartment_id=compartment_id
            )
            
            response = genai_client.chat(chat_details)
            
            # Parse LLM response from chat API
            llm_response = response.data.chat_response.choices[0].message.content[0].text
            log_step("AIAnalyzeQuery", f"LLM response: {llm_response}")
            
            # Parse JSON response from LLM with better error handling
            import json
            import re
            
            try:
                # Try to extract JSON from the response (in case LLM adds extra text)
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    result = json.loads(json_str)
                else:
                    # If no JSON found, try parsing the entire response
                    result = json.loads(llm_response)
                
                log_step("AIAnalyzeQuery", f"Successfully parsed JSON: {result}")
                return result
                
            except json.JSONDecodeError as json_error:
                log_step("AIAnalyzeQuery", f"JSON parsing failed: {json_error}")
                log_step("AIAnalyzeQuery", f"Raw LLM response: {llm_response}")
                
                # Fallback: try to extract key information from the response
                try:
                    # Look for service and tool mentions in the text
                    service_match = re.search(r'"service"\s*:\s*"([^"]+)"', llm_response, re.IGNORECASE)
                    tool_match = re.search(r'"tool"\s*:\s*"([^"]+)"', llm_response, re.IGNORECASE)
                    
                    if service_match and tool_match:
                        result = {
                            "service": service_match.group(1),
                            "tool": tool_match.group(1),
                            "reasoning": f"Extracted from malformed JSON: {llm_response[:100]}...",
                            "confidence": 0.5,
                            "extracted_parameters": {"query": user_query}
                        }
                        log_step("AIAnalyzeQuery", f"Extracted fallback result: {result}")
                        return result
                except Exception as extract_error:
                    log_step("AIAnalyzeQuery", f"Fallback extraction also failed: {extract_error}")
                
                # Final fallback
                return {
                    "service": "semantic_search",
                    "tool": "search_livelabs_workshops",
                    "reasoning": f"JSON parsing failed: {json_error}. Raw response: {llm_response[:100]}...",
                    "confidence": 0.1,
                    "extracted_parameters": {"query": user_query}
                }
            
        except Exception as e:
            log_step("AIAnalyzeQuery", f"LLM API call failed: {str(e)}")
            # Fallback when LLM is not available
            return {
                "service": "semantic_search",
                "tool": "search_livelabs_workshops",
                "reasoning": f"LLM API failed: {str(e)}",
                "confidence": 0.1,
                "extracted_parameters": {"query": user_query}
            }
    
    def extract_parameters(self, user_query: str, tool: str, ai_analysis: Dict) -> Dict:
        """Extract parameters from user query using AI analysis"""
        log_step("ExtractParameters", f"Extracting parameters for tool: {tool}")
        
        # Use the AI analysis to extract parameters
        extracted_params = ai_analysis.get('extracted_parameters', {})
        
        # Add any additional parameter extraction logic here
        if tool == 'search_livelabs_workshops' and 'query' not in extracted_params:
            extracted_params['query'] = user_query
        
        elif tool == 'get_user_profile':
            # Extract user ID or name from query
            import re
            user_match = re.search(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)', user_query)
            if user_match:
                extracted_params['user_id'] = user_match.group(1).lower().replace(' ', '.')
        
        elif tool == 'search_users_by_skill':
            # Extract skill name from query
            import re
            skill_match = re.search(r'\b(skill|expertise)\s+(?:in|of)?\s+([a-zA-Z\s]+)', user_query.lower())
            if skill_match:
                extracted_params['skill_name'] = skill_match.group(2).strip()
        
        log_step("ExtractParameters", f"Extracted parameters", extracted_params)
        return extracted_params

# Initialize service manager and AI reasoner
if 'mcp_manager' not in st.session_state:
    st.session_state.mcp_manager = MCPServiceManager()

if 'ai_reasoner' not in st.session_state:
    st.session_state.ai_reasoner = AIReasoner(st.session_state.mcp_manager)

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def main():
    """Main Streamlit chatbot app"""
    log_step("MainApp", "Starting main application")
    
    # Header
    st.markdown('<h1 class="main-header">🤖 LiveLabs AI Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Ask me anything about LiveLabs workshops, users, and skills!</p>', unsafe_allow_html=True)
    
    # Display debug logs in sidebar
    display_debug_logs()
    
    # Sidebar for service management
    with st.sidebar:
        st.header("🔧 Service Management")
        st.info("""
        **MCP Services Management**
        
        Click the buttons below to start/stop each service.
        Services will run as background processes.
        """)
        
        # Service status and controls
        for service_key, service in st.session_state.mcp_manager.services.items():
            st.subheader(service["name"])
            st.write(f"*{service['description']}*")
            
                        # Status indicator
            status = st.session_state.mcp_manager.get_service_status(service_key)
            if status == "connected":
                st.markdown('<p class="status-success">✅ Connected</p>', unsafe_allow_html=True)
            elif status == "testing":
                st.markdown('<p class="status-warning">🔄 Testing...</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="status-warning">⏸️ Disconnected</p>', unsafe_allow_html=True)
            
            # Service control buttons
            if st.button("🔌 Test Connection", key=f"test_{service_key}"):
                with st.spinner(f"Testing {service['name']}..."):
                    result = st.session_state.mcp_manager.test_service_connection(service_key)
                    if result.get("success"):
                        st.write("Available tools:")
                        st.json(result.get("available_tools", []))
                    else:
                        st.error(f"Test failed: {result.get('error', 'Unknown error')}")
                st.rerun()
            
            st.divider()
        
        # Quick actions
        st.header("⚡ Quick Actions")
        
        if st.button("🔍 Test All Connections"):
            log_step("UserAction", "User clicked test all connections")
            for service_key in st.session_state.mcp_manager.services.keys():
                st.session_state.mcp_manager.test_service_connection(service_key)
            st.rerun()
        
        if st.button("🗑️ Clear Chat"):
            log_step("UserAction", "User clicked clear chat")
            st.session_state.chat_history = []
            st.rerun()
    
    # Main chat interface
    st.header("💬 Chat Interface")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 You:</strong> {message['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 Assistant:</strong> {message['content']}
                </div>
                """, unsafe_allow_html=True)
                
                # Show reasoning if available
                if 'reasoning' in message:
                    st.markdown(f"""
                    <div class="reasoning-box">
                        <strong>🧠 AI Reasoning:</strong> {message['reasoning']}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show tool call if available
                if 'tool_call' in message:
                    st.markdown(f"""
                    <div class="tool-call">
                        <strong>🔧 Tool Call:</strong> {message['tool_call']}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show results if available
                if 'results' in message and message['results']:
                    # Display the actual data from MCP calls
                    if isinstance(message['results'], str):
                        # If it's a string (text response from MCP), display it nicely
                        st.markdown(f"""
                        <div class="tool-call">
                            <strong>📊 Results:</strong><br>
                            <pre style="white-space: pre-wrap; font-family: inherit; margin: 0.5rem 0; color: #4a5568;">{message['results']}</pre>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # If it's structured data, show as JSON
                        st.json(message['results'])
    
    # User input
    st.markdown("---")
    
    # Input area
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "💬 Ask me anything about LiveLabs:",
            placeholder="e.g., 'Find workshops about machine learning', 'Show me users with Python skills', 'What skills does John Smith have?'",
            key="user_input"
        )
    
    with col2:
        send_button = st.button("🚀 Send", type="primary", key="send_button")
    
    # Process user input
    if send_button and user_input:
        log_step("UserInput", f"User sent message: '{user_input}'")
        
        # Add user message to chat
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now()
        })
        
        # Use AI reasoning about the query
        log_step("ProcessUserInput", "Starting AI reasoning")
        reasoning_result = st.session_state.ai_reasoner.reason_about_query(user_input)
        
        # Generate response
        log_step("ProcessUserInput", "Generating chatbot response")
        response = generate_chatbot_response(user_input, reasoning_result)
        
        # Add assistant response to chat
        st.session_state.chat_history.append(response)
        
        # Clear input and rerun
        st.rerun()
    
    # MCP Service Testing Section
    st.markdown("---")
    st.subheader("🧪 MCP Service Testing")
    st.write("Test MCP services directly with parameters:")
    
    # Test Semantic Search
    with st.expander("🔍 Test LiveLabs Semantic Search", expanded=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            search_query = st.text_input("Search Query:", "big data service workshops", key="test_search_query")
        with col2:
            top_k = st.number_input("Top K:", min_value=1, max_value=20, value=5, key="test_top_k")
        with col3:
            if st.button("🔍 Search", key="test_search_btn"):
                log_step("TestMCP", f"Testing semantic search with query: '{search_query}', top_k: {top_k}")
                
                params = {"query": search_query, "top_k": top_k}
                result = asyncio.run(call_mcp_tool_async("semantic_search", "search_livelabs_workshops", params))
                
                if result.get("success"):
                    st.success("✅ Search successful!")
                    st.text_area("Results:", result.get("data", "No data"), height=300)
                else:
                    st.error(f"❌ Search failed: {result.get('error', 'Unknown error')}")
                    st.text_area("Error Details:", str(result), height=200)
    
    # Test User Profiles
    with st.expander("👤 Test LiveLabs User Profiles"):
        col1, col2 = st.columns([2, 1])
        with col1:
            user_id = st.text_input("User ID:", "test_user_123", key="test_user_id")
        with col2:
            if st.button("👤 Get Profile", key="test_profile_btn"):
                log_step("TestMCP", f"Testing user profile with user_id: '{user_id}'")
                
                params = {"user_id": user_id}
                result = asyncio.run(call_mcp_tool_async("user_profiles", "get_user_profile", params))
                
                if result.get("success"):
                    st.success("✅ Profile retrieval successful!")
                    st.text_area("Profile Data:", result.get("data", "No data"), height=200)
                else:
                    st.error(f"❌ Profile retrieval failed: {result.get('error', 'Unknown error')}")
                    st.text_area("Error Details:", str(result), height=150)
    
    # Test User Skills Progression
    with st.expander("📈 Test LiveLabs User Skills Progression"):
        col1, col2 = st.columns([2, 1])
        with col1:
            skills_query = st.text_input("Skills Query:", "analyze my learning progress", key="test_skills_query")
        with col2:
            if st.button("📈 Analyze", key="test_skills_btn"):
                log_step("TestMCP", f"Testing skills progression with query: '{skills_query}'")
                
                params = {"query": skills_query}
                result = asyncio.run(call_mcp_tool_async("user_skills_progression", "query_user_skills_progression", params))
                
                if result.get("success"):
                    st.success("✅ Skills analysis successful!")
                    st.text_area("Analysis Results:", result.get("data", "No data"), height=200)
                else:
                    st.error(f"❌ Skills analysis failed: {result.get('error', 'Unknown error')}")
                    st.text_area("Error Details:", str(result), height=150)
    
    # Test Statistics
    with st.expander("📊 Test LiveLabs Statistics"):
        if st.button("📊 Get Statistics", key="test_stats_btn"):
            log_step("TestMCP", "Testing statistics retrieval")
            
            params = {}
            result = asyncio.run(call_mcp_tool_async("semantic_search", "get_livelabs_statistics", params))
            
            if result.get("success"):
                st.success("✅ Statistics retrieval successful!")
                st.text_area("Statistics:", result.get("data", "No data"), height=200)
            else:
                st.error(f"❌ Statistics retrieval failed: {result.get('error', 'Unknown error')}")
                st.text_area("Error Details:", str(result), height=150)
    
    # Example questions
    st.markdown("---")
    st.subheader("💡 Example Questions")
    st.write("Try asking me:")
    
    examples = [
        "Find workshops about machine learning",
        "Show me users with Python skills",
        "What skills does John Smith have?",
        "Find similar workshops to the database tutorial",
        "How many workshops are there?",
        "Show me expert level users",
        "What are the most popular skills?"
    ]
    
    cols = st.columns(len(examples))
    for i, example in enumerate(examples):
        with cols[i]:
            if st.button(example, key=f"example_{i}"):
                log_step("UserAction", f"User clicked example: '{example}'")
                
                # Simulate user input
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': example,
                    'timestamp': datetime.now()
                })
                
                reasoning_result = st.session_state.ai_reasoner.reason_about_query(example)
                response = generate_chatbot_response(example, reasoning_result)
                st.session_state.chat_history.append(response)
                st.rerun()

def generate_chatbot_response(user_query: str, reasoning_result: Dict) -> Dict:
    """Generate chatbot response based on AI reasoning"""
    log_step("GenerateResponse", f"Generating response for query: '{user_query}'")
    
    action = reasoning_result['action']
    service_key = action['service']
    tool = action['tool']
    reasoning = reasoning_result['reasoning']
    ai_analysis = reasoning_result.get('ai_analysis', {})
    
    # Extract parameters from AI analysis
    params = ai_analysis.get('extracted_parameters', {})
    if not params:
        # Fallback: use the user query as the main parameter
        params = {'query': user_query}
    
    log_step("GenerateResponse", f"Selected service: {service_key}, tool: {tool}, params: {params}")
    
    # Check if service is available
    if not reasoning_result['service_available']:
        log_step("GenerateResponse", f"Service {service_key} not available")
        return {
            'role': 'assistant',
            'content': f"❌ I understand you want to {reasoning.lower()}, but the {action['service'].replace('_', ' ').title()} service is not connected. Please start the service first using the sidebar buttons.",
            'reasoning': reasoning,
            'timestamp': datetime.now()
        }
    
    # Extract parameters using AI analysis
    log_step("GenerateResponse", "Extracting parameters")
    params = st.session_state.ai_reasoner.extract_parameters(user_query, tool, ai_analysis)
    
    # Make real MCP tool call
    try:
        log_step("GenerateResponse", f"Making MCP tool call to {service_key}.{tool}")
        
        # Call the appropriate MCP tool based on the service and tool
        log_step("GenerateResponse", f"Calling MCP tool with params: {params}")
        results = asyncio.run(call_mcp_tool_async(service_key, tool, params))
        log_step("GenerateResponse", f"MCP tool call completed for {service_key}.{tool}")
        
        # Check if the MCP call was successful
        if not results.get('success', False):
            log_step("GenerateResponse", f"MCP tool call failed: {results.get('error', 'Unknown error')}")
            return {
                'role': 'assistant',
                'content': f"❌ Error calling {tool}: {results.get('error', 'Unknown error')}",
                'reasoning': reasoning,
                'timestamp': datetime.now()
            }
        
        # Get the actual data from the MCP call
        data = results.get('data', 'No data returned')
        log_step("GenerateResponse", f"MCP tool call successful, data length: {len(str(data))}")
        
        # Generate response based on the tool and results
        if tool == 'search_livelabs_workshops':
            response_content = f"🔍 Results for workshops related to '{params.get('query', user_query)}':"
        
        elif tool == 'get_user_profile':
            user_id = params.get('user_id', 'unknown')
            response_content = f"👤 Profile for user '{user_id}':"
        
        elif tool == 'search_users_by_skill':
            skill_name = params.get('skill_name', 'unknown skill')
            experience_level = params.get('experience_level', '')
            response_content = f"💼 Users with '{skill_name}' skills"
            if experience_level:
                response_content += f" at {experience_level} level"
            response_content += ":"
        
        elif tool == 'query_user_skills_progression':
            response_content = f"🤖 Results for your query '{user_query}':"
        
        elif tool == 'get_livelabs_statistics':
            response_content = "📊 LiveLabs Workshop Statistics:"
        
        elif tool == 'find_similar_livelabs_workshops':
            workshop_id = params.get('workshop_id', 'unknown')
            response_content = f"🔍 Similar workshops to '{workshop_id}':"
        
        else:
            response_content = f"🔧 Results from {tool}:"
        
        log_step("GenerateResponse", "Response generated successfully")
        
        return {
            'role': 'assistant',
            'content': response_content,
            'reasoning': reasoning,
            'tool_call': f"{tool}({json.dumps(params, indent=2)})",
            'results': data,  # Use the actual data from MCP call
            'timestamp': datetime.now()
        }
    
    except Exception as e:
        log_step("GenerateResponse", f"Error generating response: {str(e)}")
        return {
            'role': 'assistant',
            'content': f"❌ Sorry, I encountered an error while processing your request: {str(e)}",
            'reasoning': reasoning,
            'timestamp': datetime.now()
        }

def call_mcp_tool(service_key: str, tool: str, params: Dict) -> Any:
    """Make actual MCP tool calls to get real data"""
    log_step("CallMCPTool", f"Calling MCP tool: {service_key}.{tool}")
    
    try:
        # Get service information
        service = st.session_state.mcp_manager.get_service_info(service_key)
        
        # Call the appropriate MCP tool based on the service and tool
        log_step("CallMCPTool", f"Calling MCP tool with params: {params}")
        try:
            # Set timeout for the async operation
            results = asyncio.run(asyncio.wait_for(call_mcp_tool_async(service_key, tool, params), timeout=30.0))
            log_step("CallMCPTool", f"MCP tool call completed for {service_key}.{tool}")
            return results
        except asyncio.TimeoutError:
            log_step("CallMCPTool", f"Timeout calling MCP tool {tool}")
            return {
                "success": False,
                "error": f"Timeout calling MCP tool {tool}",
                "service": service_key,
                "tool": tool,
                "parameters": params
            }
        
    except Exception as e:
        log_step("CallMCPTool", f"Error calling MCP tool: {str(e)}")
        return {
            "error": f"Failed to call MCP tool {tool}: {str(e)}",
            "service": service_key,
            "tool": tool,
            "parameters": params
        }

async def call_mcp_tool_async(service_key: str, tool: str, params: Dict) -> Any:
    """Async function to make MCP tool calls using the MCP client library."""
    log_step("CallMCPToolAsync", f"Starting async MCP call: {service_key}.{tool}")
    
    try:
        service = st.session_state.mcp_manager.get_service_info(service_key)
        service_file = service.get('file')

        if not os.path.exists(service_file):
            log_step("CallMCPToolAsync", f"Service file not found: {service_file}")
            return {"success": False, "error": f"Service file not found: {service_file}"}

        # The MCP client library is designed to start the server process itself
        # to gain control over stdin/stdout. We define the server parameters here.
        from mcp.client.stdio import StdioServerParameters, stdio_client
        from mcp.client.session import ClientSession
        
        stdio_params = StdioServerParameters(command=sys.executable, args=[service_file])

        log_step("CallMCPToolAsync", f"Spawning and connecting to MCP service: {service_file}")
        
        # stdio_client starts the process and provides the read/write streams.
        async with stdio_client(stdio_params) as (read, write):
            # ClientSession uses these streams to communicate with the service.
            async with ClientSession(read, write) as session:
                # Wait for proper MCP initialization using the protocol's built-in method
                log_step("CallMCPToolAsync", f"Waiting for {service_key} MCP protocol initialization...")
                max_wait_time = 15.0  # Total timeout
                start_time = asyncio.get_event_loop().time()
                
                while True:
                    try:
                        # First try to initialize - this will block until server is ready
                        await session.initialize()
                        log_step("CallMCPToolAsync", f"Service {service_key} MCP protocol initialization complete.")
                        
                        # If initialize succeeds, try listing tools
                        log_step("CallMCPToolAsync", f"Connected to {service_key}, discovering tools...")
                        tools_result = await session.list_tools()
                        available_tools = [t.name for t in tools_result.tools]
                        log_step("CallMCPToolAsync", f"Available tools: {available_tools}")
                        break
                        
                    except Exception as e:
                        current_time = asyncio.get_event_loop().time()
                        if current_time - start_time > max_wait_time:
                            log_step("CallMCPToolAsync", f"Service failed to initialize within {max_wait_time}s: {e}")
                            raise Exception(f"Service failed to initialize within {max_wait_time}s: {e}")
                        
                        # Wait a bit before retrying
                        await asyncio.sleep(0.5)
                        continue

                if tool not in available_tools:
                    return {"success": False, "error": f"Tool '{tool}' not found. Available: {available_tools}"}

                log_step("CallMCPToolAsync", f"Calling tool: {tool} with params: {params}")
                result = await session.call_tool(tool, params)
                log_step("CallMCPToolAsync", f"Tool call completed for {tool}")

                content_text = ""
                if hasattr(result, 'content') and result.content:
                    for content in result.content:
                        if hasattr(content, 'text'):
                            content_text += content.text

                return {
                    "success": True,
                    "data": content_text or "No content returned",
                    "available_tools": available_tools
                }

    except Exception as e:
        log_step("CallMCPToolAsync", f"Error in MCP client communication: {e}")
        import traceback
        log_step("CallMCPToolAsync", f"Traceback: {traceback.format_exc()}")
        return {"success": False, "error": f"Failed to call MCP tool {tool}: {e}"}

if __name__ == "__main__":
    main()
