#!/usr/bin/env python3
"""
Test the complete Streamlit multi-step workflow simulation
"""

import asyncio
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ai_reasoner import AIReasoner
from fastmcp import Client

async def simulate_streamlit_workflow():
    """Simulate the exact workflow that happens in Streamlit"""
    
    # Load services config
    with open('config/services.json', 'r') as f:
        services_config = json.load(f)
    
    # Initialize AI reasoner
    reasoner = AIReasoner(services_config)
    
    # Test query
    user_query = "고정민의 skill을 감안해서 추천할 workshop을 알려줘"
    print(f"User Query: {user_query}")
    
    # Step 1: AI Analysis
    print("\n=== Step 1: AI Analysis ===")
    ai_analysis = reasoner.reason_about_query(user_query)
    print(f"Service: {ai_analysis.get('service')}")
    print(f"Tool: {ai_analysis.get('tool')}")
    print(f"Parameters: {ai_analysis.get('parameters')}")
    print(f"Workflow Complete: {ai_analysis.get('workflow_complete')}")
    
    # Step 2: Execute first MCP call
    print("\n=== Step 2: Execute First MCP Call ===")
    service = ai_analysis.get('service')
    tool = ai_analysis.get('tool')
    parameters = ai_analysis.get('parameters', {})
    
    # Map service to port
    service_ports = {
        "livelabs-nl-query": 8002,
        "livelabs-semantic-search": 8001,
        "livelabs-user-skills-progression": 8003
    }
    
    port = service_ports.get(service)
    if not port:
        print(f"Unknown service: {service}")
        return
    
    # Execute MCP call
    try:
        async with Client(f"http://localhost:{port}/") as client:
            result = await client.call_tool(tool, parameters)
            print(f"Result: {result.data}")
            
            # Store result for next step
            step_result = {
                "service": service,
                "action": tool,
                "result": result.data
            }
            
    except Exception as e:
        print(f"MCP call failed: {e}")
        return
    
    # Step 3: Check if workflow continues
    print("\n=== Step 3: Check Workflow Continuation ===")
    if not ai_analysis.get('workflow_complete'):
        print("Workflow not complete, analyzing next step...")
        
        # Re-analyze with previous results
        next_analysis = reasoner.reason_about_query(user_query, previous_results=[step_result])
        print(f"Next Service: {next_analysis.get('service')}")
        print(f"Next Tool: {next_analysis.get('tool')}")
        print(f"Next Parameters: {next_analysis.get('parameters')}")
        print(f"Next Workflow Complete: {next_analysis.get('workflow_complete')}")
        
        # Execute second MCP call
        print("\n=== Step 4: Execute Second MCP Call ===")
        next_service = next_analysis.get('service')
        next_tool = next_analysis.get('tool')
        next_parameters = next_analysis.get('parameters', {})
        
        next_port = service_ports.get(next_service)
        if next_port:
            try:
                async with Client(f"http://localhost:{next_port}/") as client:
                    final_result = await client.call_tool(next_tool, next_parameters)
                    print(f"Final Result: {final_result.data}")
                    
                    if final_result.data.get('success'):
                        workshops = final_result.data.get('results', [])
                        print(f"\n🎯 Found {len(workshops)} recommended workshops for 고정민:")
                        for i, workshop in enumerate(workshops[:3], 1):
                            print(f"{i}. {workshop.get('title')} (Similarity: {workshop.get('similarity', 0):.3f})")
                    
            except Exception as e:
                print(f"Second MCP call failed: {e}")
    else:
        print("Workflow complete after first step")

if __name__ == "__main__":
    asyncio.run(simulate_streamlit_workflow())
