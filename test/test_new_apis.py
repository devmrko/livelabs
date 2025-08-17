#!/usr/bin/env python3
"""
Test script for the updated REST APIs with new endpoints
"""

import requests
import json
import time

def test_semantic_search():
    """Test semantic search API (unchanged)"""
    print("🔍 Testing Semantic Search API...")
    
    # Test search
    search_data = {"query": "big data workshops", "top_k": 3}
    response = requests.post("http://127.0.0.1:8001/search", json=search_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Search: Found {result.get('total_found', 0)} results")
    else:
        print(f"❌ Search failed: {response.status_code} - {response.text}")
    
    # Test statistics
    response = requests.get("http://127.0.0.1:8001/statistics")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Statistics: {result.get('total_workshops', 0)} workshops")
    else:
        print(f"❌ Statistics failed: {response.status_code} - {response.text}")

def test_user_profiles():
    """Test user profiles API with new NL to SQL endpoints"""
    print("\n👥 Testing User Profiles API...")
    
    # Test search by name
    search_data = {"natural_language_query": "find user John Smith"}
    response = requests.post("http://127.0.0.1:8002/users/search/by-name", json=search_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Search by name: Found {result.get('total_found', 0)} users")
        print(f"   SQL: {result.get('sql_query', 'N/A')}")
    else:
        print(f"❌ Search by name failed: {response.status_code} - {response.text}")
    
    # Test search by skill
    search_data = {"natural_language_query": "users with Python skills"}
    response = requests.post("http://127.0.0.1:8002/users/search/by-skill", json=search_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Search by skill: Found {result.get('total_found', 0)} users")
        print(f"   SQL: {result.get('sql_query', 'N/A')}")
    else:
        print(f"❌ Search by skill failed: {response.status_code} - {response.text}")
    
    # Test combined search
    search_data = {"natural_language_query": "find John Smith with Oracle Database skills"}
    response = requests.post("http://127.0.0.1:8002/users/search/combined", json=search_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Combined search: Found {result.get('total_found', 0)} users")
        print(f"   SQL: {result.get('sql_query', 'N/A')}")
    else:
        print(f"❌ Combined search failed: {response.status_code} - {response.text}")

def test_user_skills_progression():
    """Test user skills progression API with new endpoints"""
    print("\n🎯 Testing User Skills Progression API...")
    
    # Test update user skills
    skills_data = {
        "userId": "USR001",
        "skills": [
            {"skillName": "Python", "experienceLevel": "ADVANCED", "skillAdded": "2024-08-16"},
            {"skillName": "Machine Learning", "experienceLevel": "INTERMEDIATE", "skillAdded": "2024-08-16"}
        ],
        "name": "John Smith Updated",
        "email": "john.updated@example.com"
    }
    
    response = requests.post("http://127.0.0.1:8003/skills/update", json=skills_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Update skills: {result.get('message', 'Success')}")
    else:
        print(f"❌ Update skills failed: {response.status_code} - {response.text}")
    
    # Test update workshop progression
    progression_data = {
        "progressions": [
            {
                "userId": "USR001",
                "workshopId": 979,
                "status": "COMPLETED",
                "completionDate": "2024-08-16T10:00:00",
                "rating": 5
            }
        ]
    }
    
    response = requests.post("http://127.0.0.1:8003/progression/update", json=progression_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Update progression: Updated {result.get('updated_count', 0)} records")
    else:
        print(f"❌ Update progression failed: {response.status_code} - {response.text}")
    
    # Test get progression
    get_data = {"userId": "USR001"}
    response = requests.post("http://127.0.0.1:8003/progression/get", json=get_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Get progression: Found {result.get('total_found', 0)} records")
    else:
        print(f"❌ Get progression failed: {response.status_code} - {response.text}")

def main():
    """Run all tests"""
    print("🚀 Testing Updated REST APIs\n")
    
    # Test each service
    test_semantic_search()
    test_user_profiles()
    test_user_skills_progression()
    
    print("\n✅ API testing completed!")

if __name__ == "__main__":
    main()
