#!/usr/bin/env python3
"""
Test the enhanced AI reasoner with the multi-step workflow
"""

import asyncio
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ai_reasoner import AIReasoner

def test_enhanced_reasoning():
    """Test the enhanced AI reasoner"""
    
    # Load services config
    with open('config/services.json', 'r') as f:
        services_config = json.load(f)
    
    # Initialize AI reasoner
    reasoner = AIReasoner(services_config)
    
    # Test query
    query = "고정민의 skill을 감안해서 추천할 workshop을 알려줘"
    
    print("=== Step 1: Initial Query Analysis ===")
    step1_result = reasoner.reason_about_query(query)
    print(f"Service: {step1_result.get('service')}")
    print(f"Tool: {step1_result.get('tool')}")
    print(f"Parameters: {step1_result.get('parameters')}")
    print(f"Workflow Complete: {step1_result.get('workflow_complete')}")
    print(f"Reasoning: {step1_result.get('reasoning')}")
    
    # Simulate successful first step result
    mock_nl_query_result = {
        "service": "livelabs-nl-query",
        "action": "query_database_nl",
        "result": {
            "success": True,
            "users": [],
            "total_found": 0,
            "explanation": "The result shows that user \"고정민\" has an intermediate level skill in Python.",
            "query": "고정민의 스킬을 알려줘"
        }
    }
    
    print("\n=== Step 2: Follow-up Analysis (after NL Query) ===")
    step2_result = reasoner.reason_about_query(query, previous_results=[mock_nl_query_result])
    print(f"Service: {step2_result.get('service')}")
    print(f"Tool: {step2_result.get('tool')}")
    print(f"Parameters: {step2_result.get('parameters')}")
    print(f"Workflow Complete: {step2_result.get('workflow_complete')}")
    print(f"Reasoning: {step2_result.get('reasoning')}")

if __name__ == "__main__":
    test_enhanced_reasoning()
