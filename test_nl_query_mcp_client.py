#!/usr/bin/env python3
"""
Test client for the LiveLabs Natural Language Query MCP service
"""

import asyncio
import logging
from fastmcp import Client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_nl_query_service():
    """Test the natural language query MCP service"""
    
    async with Client("http://localhost:8002/") as client:
        print(f"Client connected: {client.is_connected}")
        
        # List available tools
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        print(f"Available tools: {tool_names}")
        
        # Test query_database_nl with a sample query
        print("\n--- Testing query_database_nl ---")
        result = await client.call_tool("query_database_nl", {
            "natural_language_query": "Who are the Python developers with intermediate skills?",
            "top_k": 5
        })
        print(f"query_database_nl result: {result}")
        
        # Test another query
        print("\n--- Testing another query ---")
        result2 = await client.call_tool("query_database_nl", {
            "natural_language_query": "What workshops has John completed?",
            "top_k": 10
        })
        print(f"Second query result: {result2}")
        
        print(f"Client connected after exit: {client.is_connected}")

if __name__ == "__main__":
    asyncio.run(test_nl_query_service())
