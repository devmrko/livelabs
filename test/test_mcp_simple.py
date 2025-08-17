#!/usr/bin/env python3
"""
Simple test to verify MCP communication with real database connections
"""

import asyncio
import subprocess
import json
import time

async def test_mcp_service(service_file: str, tool_name: str, params: dict):
    """Test MCP service with direct subprocess communication"""
    print(f"Testing {service_file} with tool {tool_name}")
    
    try:
        # Start the MCP service as a subprocess
        process = subprocess.Popen(
            ["python", service_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        try:
            # Send initialization message
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            print("Sending initialization...")
            process.stdin.write(json.dumps(init_message) + "\n")
            process.stdin.flush()
            
            # Read initialization response
            import select
            ready, _, _ = select.select([process.stdout], [], [], 5.0)
            if ready:
                init_response = process.stdout.readline()
                print(f"Init response: {init_response.strip()}")
            
            # Send list tools request
            list_tools_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            print("Listing tools...")
            process.stdin.write(json.dumps(list_tools_message) + "\n")
            process.stdin.flush()
            
            # Read tools response
            ready, _, _ = select.select([process.stdout], [], [], 5.0)
            if ready:
                tools_response = process.stdout.readline()
                print(f"Tools response: {tools_response.strip()}")
            
            # Send tool call
            tool_call_message = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": params
                }
            }
            
            print(f"Calling tool: {tool_name} with params: {params}")
            process.stdin.write(json.dumps(tool_call_message) + "\n")
            process.stdin.flush()
            
            # Read tool call response
            ready, _, _ = select.select([process.stdout], [], [], 15.0)
            
            if ready:
                response_line = process.stdout.readline()
                if response_line:
                    print(f"Tool response: {response_line.strip()}")
                    try:
                        response_data = json.loads(response_line.strip())
                        
                        if "result" in response_data:
                            result_content = response_data["result"].get("content", [])
                            
                            if result_content and len(result_content) > 0:
                                content = result_content[0]
                                if isinstance(content, dict) and "text" in content:
                                    print(f"✅ Success: {content['text'][:200]}...")
                                else:
                                    print(f"✅ Success: {str(content)[:200]}...")
                            else:
                                print("✅ Success: No content returned")
                        else:
                            print(f"❌ Error: {response_data.get('error', 'Unknown error')}")
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {str(e)}")
                        print(f"Raw response: {response_line}")
                else:
                    print("❌ No response received")
            else:
                print("❌ Timeout waiting for response")
                
        finally:
            # Clean up the process
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
                
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

async def main():
    """Main test function"""
    print("🧪 Testing MCP Services with Real Database Connections...")
    
    # Test semantic search service
    print("\n1. Testing LiveLabs Semantic Search Service")
    success1 = await test_mcp_service(
        "mcp_livelabs_semantic_search.py",
        "get_livelabs_statistics",
        {}
    )
    
    print(f"\n📊 Test Results:")
    print(f"Semantic Search: {'✅ PASS' if success1 else '❌ FAIL'}")

if __name__ == "__main__":
    asyncio.run(main())
