#!/usr/bin/env python3
"""
LiveLabs Natural Language Query MCP Service
Provides natural language query interface using Oracle SELECT AI
"""

import os
import sys

# Add the project root to Python path before other imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

import logging
from typing import Dict, Optional, Any
from fastmcp import FastMCP
from dotenv import load_dotenv
from utils.oracle_db import DatabaseManager

# Load environment variables and configure logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Global Services ---
db_manager = DatabaseManager()

mcp = FastMCP(
    name="livelabs-nl-query"
)

# --- Tool Definitions ---

@mcp.tool()
async def query_database_nl(natural_language_query: str, top_k: int = 10) -> Dict[str, Any]:
    """Processes natural language queries about LiveLabs users, skills, and workshops using Oracle SELECT AI.
    
    Parameters:
    - natural_language_query (str): Natural language question about data (e.g., 'Who are the Python developers?', 'Show me users with cloud skills')
    - top_k (int): Maximum number of results to return (default: 10, max: 50)
    
    Returns: JSON with success status, generated SQL query, AI explanation, and structured results
    Use cases: Data exploration, user analytics, skill analysis, learning path recommendations
    Note: Leverages Oracle SELECT AI for intelligent query interpretation and response generation
    """
    logger.info(f"Executing query_database_nl for: '{natural_language_query}'")
    try:
        if not db_manager:
            return {"success": False, "error": "Database not initialized"}
        
        # Set the AI profile
        profile_name = "DISCOVERYDAY_AI_PROFILE"
        profile_query = f"""
        BEGIN
            DBMS_CLOUD_AI.SET_PROFILE('{profile_name}');
        END;
        """
        db_manager.execute_query(profile_query, is_ddl=True)
        
        # Escape and enhance the query
        escaped_query = natural_language_query.replace("'", "''")
        enhanced_prompt = f"""For the query: "{escaped_query}"

If this is about a specific user's skills or workshop history:
1. First identify the user by name
2. Get all their profile data (skills, experience levels, completed workshops)  
3. Then analyze what they should learn or their current status

If this is a general query, answer directly.
Limit results to {min(top_k, 50)} items if applicable.

Query: {escaped_query}"""
        
        # Generate SQL
        escaped_prompt = enhanced_prompt.replace("'", "''")
        showsql_query = f"SELECT AI SHOWSQL '{escaped_prompt}'"
        
        showsql_results = db_manager.execute_query(showsql_query, fetch_all=True)
        generated_sql = ""
        if showsql_results and len(showsql_results) > 0:
            generated_sql = str(showsql_results[0][0]) if showsql_results[0] and showsql_results[0][0] else ""
        
        # Get AI narrative response
        analysis_query = f"SELECT AI NARRATE '{escaped_prompt}'"
        narrate_results = db_manager.execute_query(analysis_query, fetch_all=True)
        
        narration = ""
        if narrate_results and len(narrate_results) > 0:
            narration = str(narrate_results[0][0]) if narrate_results[0] and narrate_results[0][0] else "No results"
        
        return {
            "success": True,
            "users": [],  # NARRATE returns text, not structured data
            "total_found": 0,
            "sql_query": generated_sql,
            "explanation": narration,
            "query": natural_language_query
        }
        
    except Exception as e:
        logger.error(f"Error in query_database_nl: {e}")
        return {"success": False, "error": str(e)}





# --- Main Execution ---



if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8002,
        path="/"
    )
