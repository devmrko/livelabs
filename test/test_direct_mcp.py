#!/usr/bin/env python3
"""
Direct test of MCP service functions without MCP protocol
"""

import asyncio
import sys
import os

# Add current directory to path to import MCP services
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_semantic_search():
    """Test semantic search service directly"""
    print("🧪 Testing LiveLabs Semantic Search Service Directly...")
    
    try:
        # Import the MCP service module
        from mcp_livelabs_semantic_search import handle_search_livelabs_workshops
        
        # Test the semantic search function with a real query
        print("Testing search_livelabs_workshops with 'big data'...")
        result = await handle_search_livelabs_workshops({
            "query": "big data",
            "top_k": 5,
            "similarity_threshold": 0.0
        })
        
        if result and result.content and len(result.content) > 0:
            content = result.content[0]
            if hasattr(content, 'text'):
                print(f"✅ Success: {content.text[:300]}...")
                return True
            else:
                print(f"✅ Success: {str(content)[:300]}...")
                return True
        else:
            print("❌ No content returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

async def main():
    """Main test function"""
    success = await test_semantic_search()
    
    print(f"\n📊 Test Results:")
    print(f"Direct MCP Test: {'✅ PASS' if success else '❌ FAIL'}")

if __name__ == "__main__":
    asyncio.run(main())
