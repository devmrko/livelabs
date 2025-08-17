#!/usr/bin/env python3
"""
MCP Server for LiveLabs User Skills & Progression Service
Provides natural language queries for user skills, progression, and user-related data using Oracle SELECT AI
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.server.lowlevel.server import NotificationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Import our SELECT AI service
from oracle_select_ai_example import OracleSelectAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("livelabs-user-skills-progression-service")

# Global instance for SELECT AI engine
select_ai_engine = None

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools"""
    tools = [
        Tool(
            name="query_user_skills_progression",
            description="Query user skills and progression data using natural language with Oracle SELECT AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query about user skills and progression (e.g., 'what kinds of skill John Smith have, and how good are those', 'show me users with expert level machine learning skills', 'find users who have progressed from beginner to expert')"
                    },
                    "profile_name": {
                        "type": "string",
                        "description": "AI profile name for SELECT AI",
                        "default": "DISCOVERYDAY_AI_PROFILE"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="set_user_skills_ai_profile",
            description="Set the AI profile for user skills and progression queries",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile_name": {
                        "type": "string",
                        "description": "AI profile name to set for user skills queries"
                    }
                },
                "required": ["profile_name"]
            }
        ),
        Tool(
            name="run_user_skills_example_queries",
            description="Run predefined example queries to demonstrate user skills and progression capabilities",
            inputSchema={
                "type": "object",
                "properties": {
                    "example_type": {
                        "type": "string",
                        "description": "Type of user skills examples to run: 'skills', 'progression', 'users', 'all'",
                        "default": "all"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_user_skills_connection_status",
            description="Check the connection status to Oracle database for user skills queries",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]
    return ListToolsResult(tools=tools)

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls"""
    try:
        if name == "query_user_skills_progression":
            return await handle_user_skills_progression_query(arguments)
        elif name == "set_user_skills_ai_profile":
            return await handle_set_user_skills_ai_profile(arguments)
        elif name == "run_user_skills_example_queries":
            return await handle_run_user_skills_examples(arguments)
        elif name == "get_user_skills_connection_status":
            return await handle_get_user_skills_connection_status(arguments)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")]
            )
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )

async def handle_user_skills_progression_query(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle user skills and progression query"""
    global select_ai_engine
    
    try:
        query = arguments["query"]
        profile_name = arguments.get("profile_name", "DISCOVERYDAY_AI_PROFILE")
        
        if select_ai_engine is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Service not initialized. Please wait.")]
            )
        
        # Set AI profile
        if not select_ai_engine.set_ai_profile(profile_name):
            return CallToolResult(
                content=[TextContent(type="text", text=f"Failed to set AI profile: {profile_name}")]
            )
        
        # Execute SELECT AI query
        results = select_ai_engine.execute_select_ai_query(query)
        
        if results is not None:
            result_text = f"🤖 LiveLabs User Skills & Progression Query Results for: '{query}'\n\n"
            
            if results:
                result_text += f"Found {len(results)} results:\n\n"
                for i, row in enumerate(results, 1):
                    result_text += f"Row {i}: {row}\n"
            else:
                result_text += "No results returned."
        else:
            result_text = f"User skills and progression query failed for: '{query}'"
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
        
    except Exception as e:
        logger.error(f"User skills and progression query error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"User skills and progression query error: {str(e)}")]
        )

async def handle_set_user_skills_ai_profile(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle setting AI profile for user skills queries"""
    global select_ai_engine
    
    try:
        profile_name = arguments["profile_name"]
        
        if select_ai_engine is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Service not initialized. Please wait.")]
            )
        
        # Set AI profile
        success = select_ai_engine.set_ai_profile(profile_name)
        
        if success:
            result_text = f"✅ User skills AI profile set successfully: {profile_name}"
        else:
            result_text = f"❌ Failed to set user skills AI profile: {profile_name}"
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
        
    except Exception as e:
        logger.error(f"Set user skills AI profile error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Set user skills AI profile error: {str(e)}")]
        )

async def handle_run_user_skills_examples(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle running user skills example queries"""
    global select_ai_engine
    
    try:
        example_type = arguments.get("example_type", "all")
        
        if select_ai_engine is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Service not initialized. Please wait.")]
            )
        
        # Set AI profile
        if not select_ai_engine.set_ai_profile("DISCOVERYDAY_AI_PROFILE"):
            return CallToolResult(
                content=[TextContent(type="text", text="Failed to set AI profile")]
            )
        
        # Run examples
        result_text = f"🧪 Running LiveLabs User Skills & Progression Examples ({example_type})\n\n"
        
        if example_type in ["skills", "all"]:
            result_text += "=== User Skills Examples ===\n\n"
            
            skills_queries = [
                "what kinds of skill John Smith have, and how good are those",
                "show me users with machine learning skills",
                "find users with expert level skills",
                "what are the most popular skills among users"
            ]
            
            for query in skills_queries:
                result_text += f"Query: {query}\n"
                results = select_ai_engine.execute_select_ai_query(query)
                if results is not None:
                    if results:
                        result_text += f"Results: {len(results)} found\n"
                        for i, row in enumerate(results[:3], 1):  # Show first 3 results
                            result_text += f"  {i}. {row}\n"
                    else:
                        result_text += "Results: No results found\n"
                else:
                    result_text += "Results: Query failed\n"
                result_text += "\n"
        
        if example_type in ["progression", "all"]:
            result_text += "=== User Progression Examples ===\n\n"
            
            progression_queries = [
                "find users who have progressed from beginner to expert",
                "show me users who have improved their skills over time",
                "what skills do users typically start with",
                "find users with the most skill progression"
            ]
            
            for query in progression_queries:
                result_text += f"Query: {query}\n"
                results = select_ai_engine.execute_select_ai_query(query)
                if results is not None:
                    if results:
                        result_text += f"Results: {len(results)} found\n"
                        for i, row in enumerate(results[:3], 1):  # Show first 3 results
                            result_text += f"  {i}. {row}\n"
                    else:
                        result_text += "Results: No results found\n"
                else:
                    result_text += "Results: Query failed\n"
                result_text += "\n"
        
        if example_type in ["users", "all"]:
            result_text += "=== User Analysis Examples ===\n\n"
            
            user_queries = [
                "who are the most skilled users",
                "find users with diverse skill sets",
                "show me users who started recently",
                "what is the average skill level across users"
            ]
            
            for query in user_queries:
                result_text += f"Query: {query}\n"
                results = select_ai_engine.execute_select_ai_query(query)
                if results is not None:
                    if results:
                        result_text += f"Results: {len(results)} found\n"
                        for i, row in enumerate(results[:3], 1):  # Show first 3 results
                            result_text += f"  {i}. {row}\n"
                    else:
                        result_text += "Results: No results found\n"
                else:
                    result_text += "Results: Query failed\n"
                result_text += "\n"
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
        
    except Exception as e:
        logger.error(f"Run user skills examples error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Run user skills examples error: {str(e)}")]
        )

async def handle_get_user_skills_connection_status(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle getting user skills query connection status"""
    global select_ai_engine
    
    try:
        if select_ai_engine is None:
            result_text = """
🔌 LiveLabs User Skills & Progression Connection Status

LiveLabs User Skills & Progression Service:
- Status: Not initialized
- Action: Run a query to initialize the connection
"""
        else:
            # Try to test the connection
            try:
                test_query = "SELECT 1 FROM DUAL"
                cursor = select_ai_engine.oracle_manager.get_cursor()
                cursor.execute(test_query)
                result = cursor.fetchone()
                cursor.close()
                
                if result:
                    result_text = """
🔌 LiveLabs User Skills & Progression Connection Status

LiveLabs User Skills & Progression Service:
- Status: ✅ Connected and working
- Database: Accessible
- SELECT AI: Ready for user skills queries
"""
                else:
                    result_text = """
🔌 LiveLabs User Skills & Progression Connection Status

LiveLabs User Skills & Progression Service:
- Status: ⚠️ Connected but query test failed
- Database: Connection established
- SELECT AI: May have issues
"""
            except Exception as conn_error:
                result_text = f"""
🔌 LiveLabs User Skills & Progression Connection Status

LiveLabs User Skills & Progression Service:
- Status: ❌ Connection error
- Error: {str(conn_error)}
- Action: Check database credentials and network
"""
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
        
    except Exception as e:
        logger.error(f"User skills connection status error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"User skills connection status error: {str(e)}")]
        )

async def main():
    """Main function"""
    global select_ai_engine
    
    logger.info("User Skills Progression Service: Initializing...")
    
    try:
        # Initialize the SELECT AI engine
        select_ai_engine = OracleSelectAI()
        if not select_ai_engine.initialize_connection():
            logger.error("Failed to initialize connection for user skills progression")
            return
            
        logger.info("User Skills Progression Service: Initialization complete, connection established.")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return

    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="livelabs-user-skills-progression-service",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(tools_changed=False),
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
