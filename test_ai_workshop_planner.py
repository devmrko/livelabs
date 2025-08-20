#!/usr/bin/env python3
"""
Test the AI Workshop Planner functionality
"""

import asyncio
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ai_reasoner import AIReasoner

def test_ai_workshop_planner():
    """Test AI Workshop Planner scenarios"""
    
    # Load services config
    with open('config/services.json', 'r') as f:
        services_config = json.load(f)
    
    # Initialize AI reasoner
    reasoner = AIReasoner(services_config)
    
    # Test scenarios for AI Workshop Planner
    test_scenarios = [
        # User management
        "새로운 사용자 김철수를 추가해주세요. 이메일은 kim@example.com입니다",
        "사용자 정보를 조회해주세요",
        
        # Skill management  
        "김철수의 스킬에 Python과 SQL을 추가해주세요",
        "내 스킬 목록을 확인해주세요",
        
        # Workshop recommendations
        "Python 관련 워크샵을 추천해주세요",
        "머신러닝 초보자를 위한 워크샵을 찾아주세요",
        "내 스킬에 맞는 워크샵을 추천해주세요",
        
        # Progress tracking
        "워크샵 완료를 기록해주세요",
        "내 학습 진도를 확인해주세요"
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {scenario}")
        print(f"{'='*60}")
        
        # Analyze with AI reasoner
        analysis = reasoner.reason_about_query(scenario)
        
        print(f"🎯 Service: {analysis.get('service')}")
        print(f"🔧 Tool: {analysis.get('tool')}")
        print(f"📋 Parameters: {analysis.get('parameters')}")
        print(f"🤖 Reasoning: {analysis.get('reasoning')}")
        print(f"✅ Workflow Complete: {analysis.get('workflow_complete')}")
        
        # Check if AI Workshop Planner logic is working
        service = analysis.get('service')
        tool = analysis.get('tool')
        
        # Validate expected behavior
        if "사용자" in scenario and "추가" in scenario:
            expected_service = "livelabs-user-skills-progression"
            expected_tool = "add_user"
        elif "스킬" in scenario and ("추가" in scenario or "업데이트" in scenario):
            expected_service = "livelabs-user-skills-progression" 
            expected_tool = "update_user_skills"
        elif "워크샵" in scenario and ("추천" in scenario or "찾아" in scenario):
            expected_service = "livelabs-semantic-search"
            expected_tool = "search_workshops"
        elif "완료" in scenario and "기록" in scenario:
            expected_service = "livelabs-user-skills-progression"
            expected_tool = "update_workshop_progress"
        else:
            expected_service = None
            expected_tool = None
            
        if expected_service and expected_tool:
            if service == expected_service and tool == expected_tool:
                print("✅ CORRECT: AI Workshop Planner logic working as expected")
            else:
                print(f"❌ INCORRECT: Expected {expected_service}.{expected_tool}, got {service}.{tool}")
        else:
            print("ℹ️  General query - checking logic manually")

if __name__ == "__main__":
    test_ai_workshop_planner()
