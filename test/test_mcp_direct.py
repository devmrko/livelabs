#!/usr/bin/env python3
"""
Test script to directly test the MCP semantic search service
"""

import asyncio
import json
import subprocess
import sys
import time
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters

async def test_mcp_semantic_search():
    """Test the MCP semantic search service directly"""
    
    # Start the MCP service
    print("Starting MCP semantic search service...")
    process = subprocess.Popen(
        [sys.executable, "mcp_livelabs_semantic_search.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a moment for the service to start
    time.sleep(2)
    
    try:
        # Create stdio parameters
        stdio_params = StdioServerParameters(
            command=sys.executable,
            args=["mcp_livelabs_semantic_search.py"]
        )
        
        # Connect to the MCP service
        async with ClientSession(stdio_params) as session:
            print("Connected to MCP service")
            
            # Test the search_livelabs_workshops tool
            print("\nTesting search_livelabs_workshops...")
            result = await session.call_tool(
                "search_livelabs_workshops",
                {"query": "big data service workshops", "top_k": 5}
            )
            
            print(f"Tool call result: {result}")
            
            if result.content:
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(f"Response: {content.text}")
            
    except Exception as e:
        print(f"Error testing MCP service: {e}")
    finally:
        # Clean up
        if process.poll() is None:
            process.terminate()
            process.wait()

if __name__ == "__main__":
    asyncio.run(test_mcp_semantic_search())
