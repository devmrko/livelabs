#!/usr/bin/env python3
"""
Test script for the NL Query to Database service
"""

import requests
import json

def test_nl_query_service():
    """Test the natural language query service"""
    print("🧠 Testing NL Query to Database Service\n")
    
    # Test queries to demonstrate the natural language capabilities
    test_queries = [
        "Who are the Python developers?",
        "Find users with advanced Oracle skills",
        "Show me data scientists",
        "Who has machine learning experience?",
        "List all users with their skills",
        "Find John Smith's profile",
        "Who are the most experienced developers?",
        "Show users with cloud computing skills"
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
                if result.get('success'):
                    print(f"   ✅ Query successful")
                    print(f"   📝 SQL: {result.get('sql_query', 'N/A')}")
                    print(f"   🤖 AI Response: {result.get('explanation', 'No response')}")
                else:
                    print(f"   ❌ Query failed: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code} - {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()  # Empty line for readability

def test_health_check():
    """Test the health check endpoint"""
    print("🏥 Testing Health Check...")
    
    try:
        response = requests.get("http://127.0.0.1:8002/health")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Service: {result.get('service', 'Unknown')}")
            print(f"   ✅ Status: {result.get('status', 'Unknown')}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    print()

def main():
    """Run all tests"""
    print("🚀 Testing LiveLabs NL Query to Database Service\n")
    
    # Test health first
    test_health_check()
    
    # Test natural language queries
    test_nl_query_service()
    
    print("✅ NL Query testing completed!")

if __name__ == "__main__":
    main()
