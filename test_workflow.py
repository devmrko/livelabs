#!/usr/bin/env python3
"""
Test the multi-step workflow: nl-query → semantic search
"""

import asyncio
import logging
from fastmcp import Client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_workflow():
    """Test the multi-step workflow"""
    
    # Step 1: Query user skills using nl-query service
    print("=== Step 1: Getting 고정민's skills ===")
    async with Client("http://localhost:8002/") as client:
        result1 = await client.call_tool("query_database_nl", {
            "natural_language_query": "고정민의 스킬을 알려줘",
            "top_k": 10
        })
        print(f"NL Query result: {result1.data}")
        
        # Extract skills from the explanation
        explanation = result1.data.get("explanation", "")
        print(f"Explanation: {explanation}")
    
    # Step 2: Search workshops based on skills
    print("\n=== Step 2: Finding skill-related workshops ===")
    async with Client("http://localhost:8001/") as client:
        # Use a general query since we may not have specific user data
        result2 = await client.call_tool("search_workshops", {
            "query": "python programming database development",
            "top_k": 5
        })
        print(f"Semantic search result: {result2.data}")
        
        if result2.data.get("success"):
            workshops = result2.data.get("results", [])
            print(f"\nFound {len(workshops)} workshops:")
            for i, workshop in enumerate(workshops, 1):
                print(f"{i}. {workshop.get('title')} (Similarity: {workshop.get('similarity', 0):.3f})")

if __name__ == "__main__":
    asyncio.run(test_workflow())
