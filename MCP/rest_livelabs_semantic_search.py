#!/usr/bin/env python3
"""
LiveLabs Semantic Search MCP Service
Provides vector search and statistics endpoints via FastMCP
"""

import os
import sys

# Add the project root to Python path before other imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

import logging
from typing import Dict, List, Optional, Any
from fastmcp import FastMCP
from dotenv import load_dotenv
from utils.vector_search import VectorSearchEngine

# Load environment variables and configure logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Global Services ---
vector_search_engine = VectorSearchEngine()
vector_search_engine.initialize_connections()

mcp = FastMCP(
    name="livelabs-semantic-search"
)

# --- Tool Definitions ---

@mcp.tool()
async def search_workshops(query: str, top_k: int = 10) -> Dict[str, Any]:
    """Performs semantic search for LiveLabs workshops using vector similarity matching.
    
    Parameters:
    - query (str): Search query text (e.g., 'machine learning with Python', 'database optimization')
    - top_k (int): Maximum number of results to return (default: 10, max: 50)
    
    Returns: JSON with success status, workshop results with metadata (title, author, difficulty, similarity)
    Use cases: Workshop discovery, content recommendation, learning path planning, skill-based search
    """
    logger.info(f"Executing search_workshops for query: '{query}'")
    try:
        if not vector_search_engine:
            return {"success": False, "error": "Search engine not initialized"}
        
        # Execute the search
        results = vector_search_engine.search_similar_workshops(
            query_text=query,
            top_k=min(top_k, 50)  # Cap at 50 results
        )
        
        # Format results - results is already a list of dicts
        search_results = []
        for result in results:
            search_results.append({
                "id": result.get("id"),
                "title": result.get("title", ""),
                "author": result.get("author", ""),
                "difficulty": result.get("difficulty", ""),
                "category": result.get("category", ""),
                "duration": result.get("duration", ""),
                "content": result.get("text_content", ""),
                "similarity": result.get("similarity", 0.0),
                "url": result.get("url", "")
            })
        
        return {
            "success": True,
            "results": search_results,
            "total_found": len(search_results),
            "query": query
        }
        
    except Exception as e:
        logger.error(f"Error in search_workshops: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_workshop_statistics() -> Dict[str, Any]:
    """Retrieves comprehensive statistics about available LiveLabs workshops and training content.
    
    Returns: JSON with workshop counts, difficulty distribution, category breakdown, and metadata
    Use cases: Content analytics, curriculum planning, learning path design, progress tracking
    Note: Provides overview of entire workshop catalog for administrative and planning purposes
    """
    logger.info("Executing get_workshop_statistics")
    try:
        if not vector_search_engine:
            return {"success": False, "error": "Search engine not initialized"}
        
        # Get basic statistics from Oracle database
        query = """
        SELECT 
            COUNT(*) as total_workshops
        FROM admin.livelabs_workshops
        """
        
        result = vector_search_engine.oracle_manager.execute_query(query, fetch_one=True)
        
        total_workshops = result[0] if result else 0
        
        return {
            "success": True,
            "total_workshops": total_workshops,
            "difficulty_breakdown": {"Unknown": total_workshops},
            "category_breakdown": {"Unknown": total_workshops}
        }
        
    except Exception as e:
        logger.error(f"Error in get_workshop_statistics: {e}")
        return {"success": False, "error": str(e)}

# --- Main Execution ---

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8001,
        path="/"
    )
