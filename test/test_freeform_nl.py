#!/usr/bin/env python3
"""
Test script for free-form natural language user search
"""

import requests
import json

def test_freeform_queries():
    """Test various free-form natural language queries"""
    print("🧠 Testing Free-Form Natural Language User Search\n")
    
    # Test queries that demonstrate the flexibility
    test_queries = [
        "find user John Smith",
        "users with Python skills",
        "advanced Oracle developers",
        "john.smith@example.com",
        "USR001",
        "users created in 2025",
        "developers with machine learning and Python experience",
        "find Sarah or Michael with database skills",
        "intermediate JavaScript developers who also know React",
        "all users with cloud experience",
        "show me data scientists",
        "users with email containing oracle",
        "anyone with AI or artificial intelligence skills"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"🔍 Test {i}: '{query}'")
        
        try:
            response = requests.post(
                "http://127.0.0.1:8002/users/search/nl",
                json={"natural_language_query": query}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Found {result.get('total_found', 0)} users")
                print(f"   🧠 Query interpretation: {result.get('explanation', '').split('Generated MongoDB query:')[0].strip()}")
                print(f"   📝 MongoDB query: {result.get('sql_query', 'N/A')}")
                
                # Show first result if available
                if result.get('users'):
                    first_user = result['users'][0]
                    print(f"   👤 Sample user: {first_user.get('name', 'N/A')} ({first_user.get('userId', 'N/A')})")
                    if first_user.get('skills'):
                        skills = [skill.get('skillName', '') for skill in first_user['skills'][:3]]
                        print(f"   🎯 Skills: {', '.join(skills)}")
                
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()  # Empty line for readability

def main():
    """Run free-form NL tests"""
    test_freeform_queries()
    print("✅ Free-form NL testing completed!")

if __name__ == "__main__":
    main()
