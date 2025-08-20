#!/usr/bin/env python3
"""
Test that the system doesn't fabricate workshop information when no data is found
"""

import asyncio
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ai_reasoner import AIReasoner
from fastmcp import Client

async def test_no_fabrication():
    """Test queries that should return no data to ensure no fabrication"""
    
    # Load services config
    with open('config/services.json', 'r') as f:
        services_config = json.load(f)
    
    # Initialize AI reasoner
    reasoner = AIReasoner(services_config)
    
    # Test queries that should return no results
    test_queries = [
        "존재하지않는사용자의 skill을 감안해서 추천할 workshop을 알려줘",
        "ZZZZZ programming workshop을 찾아줘",
        "비존재언어 워크샵을 추천해줘"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing Query: {query}")
        print(f"{'='*60}")
        
        # Step 1: AI Analysis
        ai_analysis = reasoner.reason_about_query(query)
        print(f"Service: {ai_analysis.get('service')}")
        print(f"Tool: {ai_analysis.get('tool')}")
        
        # Step 2: Execute MCP call
        service = ai_analysis.get('service')
        tool = ai_analysis.get('tool')
        parameters = ai_analysis.get('parameters', {})
        
        service_ports = {
            "livelabs-nl-query": 8002,
            "livelabs-semantic-search": 8001,
            "livelabs-user-skills-progression": 8003
        }
        
        port = service_ports.get(service)
        if port:
            try:
                async with Client(f"http://localhost:{port}/") as client:
                    result = await client.call_tool(tool, parameters)
                    print(f"MCP Result Success: {result.data.get('success')}")
                    print(f"Total Found: {result.data.get('total_found', 0)}")
                    print(f"Results Count: {len(result.data.get('results', []))}")
                    print(f"Users Count: {len(result.data.get('users', []))}")
                    
                    # Check if any actual data was returned
                    has_data = (
                        result.data.get('total_found', 0) > 0 or
                        len(result.data.get('results', [])) > 0 or
                        len(result.data.get('users', [])) > 0
                    )
                    
                    if has_data:
                        print("❌ UNEXPECTED: Found data for non-existent query")
                    else:
                        print("✅ CORRECT: No data found as expected")
                        
            except Exception as e:
                print(f"MCP call failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_no_fabrication())
