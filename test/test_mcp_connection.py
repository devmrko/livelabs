#!/usr/bin/env python3
"""
Simple test script to verify MCP service connectivity
"""

import asyncio
import sys
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_mcp_service(service_file: str, tool_name: str, params: dict):
    """Test MCP service connectivity"""
    print(f"Testing {service_file} with tool {tool_name}")
    
    try:
        # Create MCP client parameters
        server_params = StdioServerParameters(
            command="python",
            args=[service_file],
            env={}
        )
        
        # Create client session
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the session
                await session.initialize(
                    protocol_version="2024-11-05",
                    capabilities={},
                    client_info={
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                )
                
                # List available tools
                tools_result = await session.list_tools()
                available_tools = [t.name for t in tools_result.tools]
                print(f"Available tools: {available_tools}")
                
                if tool_name not in available_tools:
                    print(f"❌ Tool '{tool_name}' not found")
                    return False
                
                # Call the tool
                print(f"Calling tool: {tool_name} with params: {params}")
                result = await session.call_tool(
                    name=tool_name,
                    arguments=params
                )
                
                # Display result
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        print(f"✅ Success: {content.text[:200]}...")
                    else:
                        print(f"✅ Success: {str(content)[:200]}...")
                else:
                    print("✅ Success: No content returned")
                
                return True
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

async def main():
    """Main test function"""
    print("🧪 Testing MCP Services...")
    
    # Test semantic search service
    print("\n1. Testing LiveLabs Semantic Search Service")
    success1 = await test_mcp_service(
        "mcp_livelabs_semantic_search.py",
        "get_livelabs_statistics",
        {}
    )
    
    # Test user profiles service
    print("\n2. Testing LiveLabs User Profiles Service")
    success2 = await test_mcp_service(
        "mcp_livelabs_user_profiles.py",
        "get_user_statistics",
        {}
    )
    
    # Test user skills service
    print("\n3. Testing LiveLabs User Skills Service")
    success3 = await test_mcp_service(
        "mcp_livelabs_user_skills_progression.py",
        "get_user_skills_connection_status",
        {}
    )
    
    print(f"\n📊 Test Results:")
    print(f"Semantic Search: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"User Profiles: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"User Skills: {'✅ PASS' if success3 else '❌ FAIL'}")

if __name__ == "__main__":
    asyncio.run(main())
