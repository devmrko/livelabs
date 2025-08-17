#!/usr/bin/env python3
"""
MCP Server for LiveLabs Semantic Search Service
Provides semantic search using vector similarity for LiveLabs workshops
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

# Import our vector search service
from utils.vector_search import VectorSearchEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("livelabs-semantic-search-service")

# Global instance for vector search engine
vector_search_engine = None

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools"""
    tools = [
        Tool(
            name="search_livelabs_workshops",
            description="Search LiveLabs workshops using semantic similarity with natural language query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query for LiveLabs workshops (e.g., 'big data service', 'machine learning', 'cloud computing')"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of top LiveLabs workshop results to return",
                        "default": 10
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Minimum similarity threshold for LiveLabs workshop results (0.0 to 1.0)",
                        "default": 0.0
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_livelabs_statistics",
            description="Get statistics about LiveLabs workshops in the database",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="find_similar_livelabs_workshops",
            description="Find LiveLabs workshops similar to a specific workshop by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "workshop_id": {
                        "type": "string",
                        "description": "LiveLabs workshop ID to find similar workshops for"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of similar LiveLabs workshops to return",
                        "default": 5
                    }
                },
                "required": ["workshop_id"]
            }
        )
    ]
    return ListToolsResult(tools=tools)

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls"""
    try:
        if name == "search_livelabs_workshops":
            return await handle_search_livelabs_workshops(arguments)
        elif name == "get_livelabs_statistics":
            return await handle_get_livelabs_statistics(arguments)
        elif name == "find_similar_livelabs_workshops":
            return await handle_find_similar_livelabs_workshops(arguments)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")]
            )
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )

async def handle_search_livelabs_workshops(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle LiveLabs semantic search"""
    global vector_search_engine
    
    try:
        query = arguments["query"]
        top_k = arguments.get("top_k", 10)
        similarity_threshold = arguments.get("similarity_threshold", 0.0)
        
        if vector_search_engine is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Service not initialized. Please wait.")]
            )
        
        # Perform vector search
        results = vector_search_engine.search_similar_workshops(query, top_k)
        
        if results:
            # Filter by similarity threshold if specified
            if similarity_threshold > 0.0:
                results = [r for r in results if r.get('similarity', 0) >= similarity_threshold]
            
            result_text = f"🔍 LiveLabs Semantic Search Results for: '{query}'\n\n"
            
            if results:
                for i, result in enumerate(results, 1):
                    similarity = result['similarity']
                    title = result.get('title', 'N/A')
                    author = result.get('author', 'N/A')
                    difficulty = result.get('difficulty', 'N/A')
                    category = result.get('category', 'N/A')
                    description = result.get('description', 'N/A')
                    
                    # Truncate description if too long
                    if description and len(description) > 200:
                        description = description[:200] + "..."
                    
                    result_text += f"{i}. Similarity: {similarity:.4f}\n"
                    result_text += f"   Title: {title}\n"
                    result_text += f"   Author: {author}\n"
                    result_text += f"   Difficulty: {difficulty}\n"
                    result_text += f"   Category: {category}\n"
                    result_text += f"   Description: {description}\n\n"
            else:
                result_text += f"No LiveLabs workshops found above similarity threshold {similarity_threshold}"
        else:
            result_text = f"No similar LiveLabs workshops found for query: '{query}'"
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
        
    except Exception as e:
        logger.error(f"LiveLabs semantic search error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"LiveLabs semantic search error: {str(e)}")]
        )

async def handle_get_livelabs_statistics(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle getting LiveLabs workshop statistics"""
    try:
        global vector_search_engine
        
        if vector_search_engine is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Service not initialized. Please wait.")]
            )
        
        # Get real statistics from database
        try:
            # Get total count of workshops with embeddings
            total_query = "SELECT COUNT(*) as total FROM admin.livelabs_workshops2 WHERE cohere4_embedding IS NOT NULL"
            total_result = vector_search_engine.oracle_manager.execute_query(total_query, fetch_one=True)
            total_workshops = total_result[0] if total_result else 0
            
            # Get statistics by difficulty
            difficulty_query = """
            SELECT difficulty, COUNT(*) as count 
            FROM admin.livelabs_workshops2 
            WHERE cohere4_embedding IS NOT NULL AND difficulty IS NOT NULL
            GROUP BY difficulty 
            ORDER BY count DESC
            """
            difficulty_results = vector_search_engine.oracle_manager.execute_query(difficulty_query)
            
            # Get statistics by category
            category_query = """
            SELECT category, COUNT(*) as count 
            FROM admin.livelabs_workshops2 
            WHERE cohere4_embedding IS NOT NULL AND category IS NOT NULL
            GROUP BY category 
            ORDER BY count DESC
            FETCH FIRST 10 ROWS ONLY
            """
            category_results = vector_search_engine.oracle_manager.execute_query(category_query)
            
            # Format real statistics
            result_text = f"📊 LiveLabs Workshop Statistics\n\n"
            result_text += f"Total LiveLabs workshops with embeddings: {total_workshops}\n\n"
            
            result_text += "By Difficulty:\n"
            for row in difficulty_results:
                difficulty, count = row
                result_text += f"  {difficulty}: {count}\n"
            
            result_text += "\nTop LiveLabs Categories:\n"
            for row in category_results:
                category, count = row
                result_text += f"  {category}: {count}\n"
                
        except Exception as db_error:
            logger.error(f"Database query error: {db_error}")
            result_text = f"📊 LiveLabs Workshop Statistics\n\n"
            result_text += f"❌ Database query failed: {str(db_error)}"
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
        
    except Exception as e:
        logger.error(f"LiveLabs statistics error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"LiveLabs statistics error: {str(e)}")]
        )

async def handle_find_similar_livelabs_workshops(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle finding similar LiveLabs workshops by ID"""
    global vector_search_engine
    
    try:
        workshop_id = arguments["workshop_id"]
        top_k = arguments.get("top_k", 5)
        
        if vector_search_engine is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Service not initialized. Please wait.")]
            )
        
        # Get the target workshop first
        target_workshop = vector_search_engine.get_workshop_by_id(workshop_id)
        if not target_workshop:
            return CallToolResult(
                content=[TextContent(type="text", text=f"LiveLabs workshop with ID '{workshop_id}' not found")]
            )
        
        # Find similar workshops
        similar_workshops = vector_search_engine.find_similar_workshops_by_id(workshop_id, top_k)
        
        if similar_workshops:
            result_text = f"🔍 Similar LiveLabs Workshops to: '{target_workshop.get('title', 'Unknown')}'\n\n"
            
            for i, result in enumerate(similar_workshops, 1):
                similarity = result['similarity']
                title = result.get('title', 'N/A')
                author = result.get('author', 'N/A')
                difficulty = result.get('difficulty', 'N/A')
                category = result.get('category', 'N/A')
                
                result_text += f"{i}. Similarity: {similarity:.4f}\n"
                result_text += f"   Title: {title}\n"
                result_text += f"   Author: {author}\n"
                result_text += f"   Difficulty: {difficulty}\n"
                result_text += f"   Category: {category}\n\n"
        else:
            result_text = f"No similar LiveLabs workshops found for workshop ID: '{workshop_id}'"
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
        
    except Exception as e:
        logger.error(f"Find similar LiveLabs workshops error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Find similar LiveLabs workshops error: {str(e)}")]
        )

async def main():
    """Main function"""
    global vector_search_engine
    
    logger.info("Semantic Search Service: Initializing...")
    
    try:
        # Initialize the vector search engine
        vector_search_engine = VectorSearchEngine()
        if not vector_search_engine.initialize_connections():
            logger.error("Failed to initialize connections")
            # In stdio mode, we can't send a notification before the server runs,
            # so we'll just log the error and the client will time out.
            return
            
        logger.info("Semantic Search Service: Initialization complete, connections established.")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return

    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="livelabs-semantic-search-service",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(tools_changed=False),
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
