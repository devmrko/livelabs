#!/usr/bin/env python3
"""
Test script for LiveLabs REST APIs
"""

import requests
import time
import subprocess
import sys

def test_api_endpoint(url, description):
    """Test a single API endpoint"""
    try:
        print(f"Testing {description}...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ {description} - OK")
            return True
        else:
            print(f"❌ {description} - HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {description} - Error: {e}")
        return False

def test_semantic_search():
    """Test semantic search API"""
    print("\n🔍 Testing Semantic Search API...")
    
    base_url = "http://127.0.0.1:8001"
    
    # Test health
    test_api_endpoint(f"{base_url}/health", "Health Check")
    
    # Test search
    try:
        search_response = requests.get(f"{base_url}/search", params={"query": "big data", "top_k": 3}, timeout=10)
        if search_response.status_code == 200:
            data = search_response.json()
            if data.get("success"):
                print(f"✅ Search - Found {data.get('total_found', 0)} results")
            else:
                print(f"❌ Search - API error: {data.get('error')}")
        else:
            print(f"❌ Search - HTTP {search_response.status_code}")
    except Exception as e:
        print(f"❌ Search - Error: {e}")
    
    # Test statistics
    test_api_endpoint(f"{base_url}/statistics", "Statistics")

def test_user_profiles():
    """Test user profiles API"""
    print("\n👥 Testing User Profiles API...")
    
    base_url = "http://127.0.0.1:8002"
    
    # Test health
    test_api_endpoint(f"{base_url}/health", "Health Check")
    
    # Test users
    test_api_endpoint(f"{base_url}/users", "Get Users")
    
    # Test statistics
    test_api_endpoint(f"{base_url}/statistics", "Statistics")

def test_user_skills():
    """Test user skills progression API"""
    print("\n📈 Testing User Skills Progression API...")
    
    base_url = "http://127.0.0.1:8003"
    
    # Test health
    test_api_endpoint(f"{base_url}/health", "Health Check")
    
    # Test skills progression
    try:
        progression_response = requests.get(f"{base_url}/skills/progression", params={"query": "skill development"}, timeout=10)
        if progression_response.status_code == 200:
            data = progression_response.json()
            if data.get("success"):
                print(f"✅ Skills Progression - Analysis completed")
            else:
                print(f"❌ Skills Progression - API error: {data.get('error')}")
        else:
            print(f"❌ Skills Progression - HTTP {progression_response.status_code}")
    except Exception as e:
        print(f"❌ Skills Progression - Error: {e}")

def main():
    """Test all REST APIs"""
    print("🧪 LiveLabs REST API Test Suite")
    print("=" * 50)
    
    # Check if services are running
    services = [
        ("Semantic Search", "http://127.0.0.1:8001/health"),
        ("User Profiles", "http://127.0.0.1:8002/health"),
        ("User Skills Progression", "http://127.0.0.1:8003/health")
    ]
    
    running_services = []
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                running_services.append(name)
                print(f"✅ {name} service is running")
            else:
                print(f"❌ {name} service is not responding")
        except:
            print(f"❌ {name} service is not running")
    
    if not running_services:
        print("\n⚠️  No services are running. Please start the services first:")
        print("   python rest_livelabs_semantic_search.py")
        print("   python rest_livelabs_user_profiles.py")
        print("   python rest_livelabs_user_skills_progression.py")
        return
    
    print(f"\n🚀 Testing {len(running_services)} running services...")
    
    # Test each running service
    if "Semantic Search" in running_services:
        test_semantic_search()
    
    if "User Profiles" in running_services:
        test_user_profiles()
    
    if "User Skills Progression" in running_services:
        test_user_skills()
    
    print("\n" + "=" * 50)
    print("✅ REST API testing completed!")

if __name__ == "__main__":
    main()
