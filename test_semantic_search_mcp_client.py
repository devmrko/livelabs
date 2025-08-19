#!/usr/bin/env python3
"""FastMCP client test for semantic search service"""

import asyncio
import logging
from fastmcp import Client

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

client = Client("http://localhost:8001/")

async def main():
    async with client:
        print(f"Client connected: {client.is_connected()}")

        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")

        # Test search_workshops
        if any(tool.name == "search_workshops" for tool in tools):
            print("\n--- Testing search_workshops ---")
            search_result = await client.call_tool("search_workshops", {
                "query": "machine learning python",
                "top_k": 5
            })
            print(f"search_workshops result: {search_result}")

        # Test get_workshop_statistics
        if any(tool.name == "get_workshop_statistics" for tool in tools):
            print("\n--- Testing get_workshop_statistics ---")
            stats_result = await client.call_tool("get_workshop_statistics", {})
            print(f"get_workshop_statistics result: {stats_result}")

        print(f"Client connected after exit: {client.is_connected()}")

if __name__ == "__main__":
    asyncio.run(main())
