#!/usr/bin/env python3
"""FastMCP client test based on documentation"""

import asyncio
import logging
import uuid
from fastmcp import Client

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

client = Client("http://localhost:8003/")

async def main():
    async with client:
        print(f"Client connected: {client.is_connected()}")

        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")

        if any(tool.name == "add_user" for tool in tools):
            print("\n--- Testing add_user ---")
            user_email = f"testuser_{uuid.uuid4()}@example.com"
            add_user_result = await client.call_tool("add_user", {"name": "Test User", "email": user_email})
            print(f"add_user result: {add_user_result}")

        if any(tool.name == "get_user" for tool in tools):
            print("\n--- Testing get_user ---")
            get_user_result = await client.call_tool("get_user", {"email": user_email})
            print(f"get_user result: {get_user_result}")
            
            # Extract userId for subsequent tests
            if get_user_result.data.get("success"):
                user_id = get_user_result.data["user"]["userId"]
                print(f"Extracted userId: {user_id}")
                
                if any(tool.name == "update_user" for tool in tools):
                    print("\n--- Testing update_user ---")
                    update_result = await client.call_tool("update_user", {"userId": user_id, "name": "Updated Test User"})
                    print(f"update_user result: {update_result}")
                
                if any(tool.name == "update_user_skills" for tool in tools):
                    print("\n--- Testing update_user_skills ---")
                    skills_result = await client.call_tool("update_user_skills", {
                        "userId": user_id, 
                        "skillName": "Python Programming", 
                        "experienceLevel": "INTERMEDIATE"
                    })
                    print(f"update_user_skills result: {skills_result}")
                
                if any(tool.name == "update_workshop_progress" for tool in tools):
                    print("\n--- Testing update_workshop_progress ---")
                    progress_result = await client.call_tool("update_workshop_progress", {
                        "userId": user_id,
                        "workshopId": "961",
                        "status": "COMPLETED",
                        "completionDate": "2025-08-19T15:57:00",
                        "rating": 5
                    })
                    print(f"update_workshop_progress result: {progress_result}")

    print(f"Client connected after exit: {client.is_connected()}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
