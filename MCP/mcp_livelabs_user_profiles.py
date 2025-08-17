#!/usr/bin/env python3
"""
MCP Server for LiveLabs User Profiles Service
Provides user profile management using MongoDB JSON Relational Duality View
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.server.lowlevel.server import NotificationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Import our MongoDB utilities
from utils.mongo_utils import MongoManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("livelabs-user-profiles-service")

# Global instance for MongoDB manager
mongo_manager = None

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools"""
    tools = [
        Tool(
            name="get_user_profile",
            description="Get a specific user profile by user ID or MongoDB ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID to find profile for"
                    },
                    "mongo_id": {
                        "type": "string",
                        "description": "MongoDB ID to find profile for"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_all_user_profiles",
            description="Get all user profiles with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of user profiles to return",
                        "default": 50
                    },
                    "skip": {
                        "type": "integer",
                        "description": "Number of user profiles to skip",
                        "default": 0
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="search_users_by_skill",
            description="Search users by specific skills",
            inputSchema={
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "Skill name to search for"
                    },
                    "experience_level": {
                        "type": "string",
                        "description": "Experience level filter (e.g., 'beginner', 'intermediate', 'expert')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 20
                    }
                },
                "required": ["skill_name"]
            }
        ),
        Tool(
            name="get_user_statistics",
            description="Get statistics about user profiles and skills",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_users_with_most_skills",
            description="Get users with the most skills",
            inputSchema={
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "Number of top users to return",
                        "default": 10
                    }
                },
                "required": []
            }
        )
    ]
    return ListToolsResult(tools=tools)

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls"""
    try:
        if name == "get_user_profile":
            return await handle_get_user_profile(arguments)
        elif name == "get_all_user_profiles":
            return await handle_get_all_user_profiles(arguments)
        elif name == "search_users_by_skill":
            return await handle_search_users_by_skill(arguments)
        elif name == "get_user_statistics":
            return await handle_get_user_statistics(arguments)
        elif name == "get_users_with_most_skills":
            return await handle_get_users_with_most_skills(arguments)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")]
            )
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )

async def handle_get_user_profile(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle getting a specific user profile"""
    global mongo_manager
    
    try:
        user_id = arguments.get("user_id")
        mongo_id = arguments.get("mongo_id")
        
        if mongo_manager is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Service not initialized. Please wait.")]
            )
        
        # Build query based on provided parameters
        query = {}
        if user_id:
            query["userId"] = user_id
        elif mongo_id:
            query["_id"] = mongo_id
        else:
            return CallToolResult(
                content=[TextContent(type="text", text="Please provide either user_id or mongo_id")]
            )
        
        # Get user profile
        user_profiles = mongo_manager.find_workshops("user_profile_json", query, limit=1)
        
        if user_profiles:
            user_profile = user_profiles[0]
            result_text = f"""
👤 LiveLabs User Profile

User ID: {user_profile.get('userId', 'N/A')}
Name: {user_profile.get('name', 'N/A')}
Email: {user_profile.get('email', 'N/A')}
Created: {user_profile.get('created', 'N/A')}
MongoDB ID: {user_profile.get('_id', 'N/A')}

Skills ({len(user_profile.get('skills', []))} total):
"""
            
            skills = user_profile.get('skills', [])
            if skills:
                for i, skill in enumerate(skills, 1):
                    skill_name = skill.get('skillName', 'N/A')
                    experience_level = skill.get('experienceLevel', 'N/A')
                    skill_added = skill.get('skillAdded', 'N/A')
                    result_text += f"  {i}. {skill_name} ({experience_level}) - Added: {skill_added}\n"
            else:
                result_text += "  No skills recorded yet.\n"
        else:
            result_text = f"No user profile found for the provided criteria."
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
        
    except Exception as e:
        logger.error(f"Get user profile error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Get user profile error: {str(e)}")]
        )

async def handle_get_all_user_profiles(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle getting all user profiles"""
    global mongo_manager
    
    try:
        limit = arguments.get("limit", 50)
        skip = arguments.get("skip", 0)
        
        if mongo_manager is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Service not initialized. Please wait.")]
            )
        
        # Get user profiles
        user_profiles = mongo_manager.find_workshops("user_profile_json", {}, limit=limit, skip=skip)
        
        if user_profiles:
            result_text = f"""
👥 LiveLabs User Profiles (showing {len(user_profiles)} of {limit})

"""
            
            for i, profile in enumerate(user_profiles, 1):
                name = profile.get('name', 'N/A')
                email = profile.get('email', 'N/A')
                user_id = profile.get('userId', 'N/A')
                skills_count = len(profile.get('skills', []))
                
                result_text += f"{i}. {name} ({email})\n"
                result_text += f"   User ID: {user_id}\n"
                result_text += f"   Skills: {skills_count}\n\n"
        else:
            result_text = "No user profiles found."
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
        
    except Exception as e:
        logger.error(f"Get all user profiles error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Get all user profiles error: {str(e)}")]
        )

async def handle_search_users_by_skill(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle searching users by skill"""
    global mongo_manager
    
    try:
        skill_name = arguments["skill_name"]
        experience_level = arguments.get("experience_level")
        limit = arguments.get("limit", 20)
        
        if mongo_manager is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Service not initialized. Please wait.")]
            )
        
        # Build query for skill search
        skill_query = {"skillName": {"$regex": skill_name, "$options": "i"}}
        if experience_level:
            skill_query["experienceLevel"] = {"$regex": experience_level, "$options": "i"}
        
        query = {"skills": {"$elemMatch": skill_query}}
        
        # Get users with matching skills
        user_profiles = mongo_manager.find_workshops("user_profile_json", query, limit=limit)
        
        if user_profiles:
            result_text = f"""
🔍 Users with Skill: '{skill_name}'
{f"Experience Level: '{experience_level}'" if experience_level else ""}

Found {len(user_profiles)} users:

"""
            
            for i, profile in enumerate(user_profiles, 1):
                name = profile.get('name', 'N/A')
                email = profile.get('email', 'N/A')
                user_id = profile.get('userId', 'N/A')
                
                # Find the matching skill details
                matching_skills = []
                for skill in profile.get('skills', []):
                    if skill_name.lower() in skill.get('skillName', '').lower():
                        if not experience_level or experience_level.lower() in skill.get('experienceLevel', '').lower():
                            matching_skills.append(skill)
                
                result_text += f"{i}. {name} ({email})\n"
                result_text += f"   User ID: {user_id}\n"
                
                for skill in matching_skills:
                    skill_name_found = skill.get('skillName', 'N/A')
                    experience = skill.get('experienceLevel', 'N/A')
                    added = skill.get('skillAdded', 'N/A')
                    result_text += f"   - {skill_name_found} ({experience}) - Added: {added}\n"
                result_text += "\n"
        else:
            result_text = f"No users found with skill '{skill_name}'"
            if experience_level:
                result_text += f" and experience level '{experience_level}'"
            result_text += "."
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
        
    except Exception as e:
        logger.error(f"Search users by skill error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Search users by skill error: {str(e)}")]
        )

async def handle_get_user_statistics(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle getting user statistics"""
    global mongo_manager
    
    try:
        if mongo_manager is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Service not initialized. Please wait.")]
            )
        
        # Get all user profiles for statistics
        all_profiles = mongo_manager.find_workshops("user_profile_json", {})
        
        if all_profiles:
            total_users = len(all_profiles)
            
            # Calculate statistics
            total_skills = 0
            skill_counts = {}
            experience_levels = {}
            users_with_skills = 0
            
            for profile in all_profiles:
                skills = profile.get('skills', [])
                if skills:
                    users_with_skills += 1
                    total_skills += len(skills)
                    
                    for skill in skills:
                        skill_name = skill.get('skillName', 'Unknown')
                        experience = skill.get('experienceLevel', 'Unknown')
                        
                        skill_counts[skill_name] = skill_counts.get(skill_name, 0) + 1
                        experience_levels[experience] = experience_levels.get(experience, 0) + 1
            
            avg_skills_per_user = total_skills / total_users if total_users > 0 else 0
            
            result_text = f"""
📊 LiveLabs User Profile Statistics

Total Users: {total_users}
Users with Skills: {users_with_skills}
Total Skills Recorded: {total_skills}
Average Skills per User: {avg_skills_per_user:.2f}

Top Skills:
"""
            
            # Show top 10 skills
            for skill, count in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                result_text += f"  {skill}: {count} users\n"
            
            result_text += "\nExperience Levels:\n"
            for level, count in sorted(experience_levels.items(), key=lambda x: x[1], reverse=True):
                result_text += f"  {level}: {count} skills\n"
        else:
            result_text = "No user profiles found for statistics."
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
        
    except Exception as e:
        logger.error(f"Get user statistics error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Get user statistics error: {str(e)}")]
        )

async def handle_get_users_with_most_skills(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle getting users with most skills"""
    global mongo_manager
    
    try:
        top_n = arguments.get("top_n", 10)
        
        if mongo_manager is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Service not initialized. Please wait.")]
            )
        
        # Get all user profiles
        all_profiles = mongo_manager.find_workshops("user_profile_json", {})
        
        if all_profiles:
            # Sort by number of skills
            profiles_with_skill_count = []
            for profile in all_profiles:
                skills_count = len(profile.get('skills', []))
                profiles_with_skill_count.append((profile, skills_count))
            
            # Sort by skill count (descending) and take top N
            top_profiles = sorted(profiles_with_skill_count, key=lambda x: x[1], reverse=True)[:top_n]
            
            result_text = f"""
🏆 Top {len(top_profiles)} Users with Most Skills

"""
            
            for i, (profile, skills_count) in enumerate(top_profiles, 1):
                name = profile.get('name', 'N/A')
                email = profile.get('email', 'N/A')
                user_id = profile.get('userId', 'N/A')
                
                result_text += f"{i}. {name} ({email})\n"
                result_text += f"   User ID: {user_id}\n"
                result_text += f"   Skills: {skills_count}\n"
                
                # Show first few skills
                skills = profile.get('skills', [])
                if skills:
                    result_text += "   Top Skills:\n"
                    for skill in skills[:5]:  # Show first 5 skills
                        skill_name = skill.get('skillName', 'N/A')
                        experience = skill.get('experienceLevel', 'N/A')
                        result_text += f"     - {skill_name} ({experience})\n"
                    if len(skills) > 5:
                        result_text += f"     ... and {len(skills) - 5} more\n"
                result_text += "\n"
        else:
            result_text = "No user profiles found."
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
        
    except Exception as e:
        logger.error(f"Get users with most skills error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Get users with most skills error: {str(e)}")]
        )

async def main():
    """Main function"""
    global mongo_manager
    
    logger.info("User Profiles Service: Initializing...")
    
    try:
        # Initialize the MongoDB manager
        mongo_manager = MongoManager()
        if not mongo_manager.initialize_connection():
            logger.error("Failed to initialize MongoDB connection")
            return
            
        logger.info("User Profiles Service: Initialization complete, MongoDB connection established.")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return

    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="livelabs-user-profiles-service",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(tools_changed=False),
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
