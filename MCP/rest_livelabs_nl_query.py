#!/usr/bin/env python3
"""
LiveLabs User Profiles REST API Service
Provides user profile and skill management endpoints
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.oracle_db import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LiveLabs Natural Language Query to Database API",
    description="Natural language query interface for user profiles using Oracle SELECT AI",
    version="1.0.0"
)

# Global Oracle database manager
db_manager = None

# Request/Response Models
class UserProfile(BaseModel):
    userId: str
    name: str
    email: str
    created: str
    skills: List[Dict[str, Any]] = []

class UserProfilesResponse(BaseModel):
    success: bool
    profiles: List[UserProfile] = []
    total_found: int = 0
    error: Optional[str] = None

class NaturalLanguageSearchRequest(BaseModel):
    natural_language_query: str  # Any free-form natural language query about users

class UserSearchResponse(BaseModel):
    success: bool
    users: List[UserProfile] = []
    total_found: int = 0
    sql_query: str = ""
    explanation: str = ""
    error: Optional[str] = None

class StatisticsResponse(BaseModel):
    success: bool
    total_users: int = 0
    skill_breakdown: Dict[str, int] = {}
    experience_breakdown: Dict[str, int] = {}
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the Oracle database manager on startup"""
    global db_manager
    
    logger.info("User Profiles API: Initializing...")
    
    try:
        # Initialize Oracle connection
        db_manager = DatabaseManager()
        test_result = db_manager.execute_query("SELECT 1 FROM DUAL", fetch_one=True)
        if test_result:
            logger.info("✅ Oracle connection established for user profiles")
        else:
            raise Exception("Oracle connection test failed")
        
        logger.info("User Profiles API: Initialization complete")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    global db_manager
    
    if db_manager:
        logger.info("Cleaning up Oracle connection...")
        DatabaseManager.close_pool()

@app.get("/", response_model=Dict[str, str])
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "LiveLabs Natural Language Query to Database API"}

@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """Detailed health check"""
    global db_manager
    
    if not db_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return {
        "status": "healthy",
        "service": "LiveLabs Natural Language Query to Database API",
        "version": "1.0.0"
    }





@app.post("/users/search/nl", response_model=UserSearchResponse)
async def search_users_natural_language(request: NaturalLanguageSearchRequest):
    """Enhanced strategy: Filter by user first, then let AI analyze the filtered data"""
    global db_manager
    
    if not db_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Enhanced NL query: '{request.natural_language_query}'")
        
        # Set the AI profile first
        profile_name = "DISCOVERYDAY_AI_PROFILE"
        profile_query = f"""
        BEGIN
            DBMS_CLOUD_AI.SET_PROFILE('{profile_name}');
        END;
        """
        db_manager.execute_query(profile_query, is_ddl=True)
        
        # Use LLM-driven approach without hardcoded filters
        escaped_query = request.natural_language_query.replace("'", "''")
        
        # Let Oracle SELECT AI handle the query intelligently with enhanced prompting
        enhanced_prompt = f"""For the query: "{escaped_query}"

If this is about a specific user's skills or workshop history:
1. First identify the user by name
2. Get all their profile data (skills, experience levels, completed workshops)  
3. Then analyze what they should learn or their current status

If this is a general query, answer directly.

Query: {escaped_query}"""
        
        logger.info(f"Enhanced LLM-driven query: {enhanced_prompt}")
        
        # Generate SQL with enhanced prompting - escape single quotes properly
        escaped_prompt = enhanced_prompt.replace("'", "''")
        showsql_query = f"SELECT AI SHOWSQL '{escaped_prompt}'"
        logger.info(f"Running SHOWSQL: {showsql_query}")
        
        showsql_results = db_manager.execute_query(showsql_query, fetch_all=True)
        generated_sql = ""
        if showsql_results and len(showsql_results) > 0:
            generated_sql = str(showsql_results[0][0]) if showsql_results[0] and showsql_results[0][0] else ""
            logger.info(f"Generated SQL: {generated_sql}")
        
        # Get narrative response with enhanced prompting
        analysis_query = f"SELECT AI NARRATE '{escaped_prompt}'"
        logger.info(f"AI analysis query: {analysis_query}")
        
        # Execute the analysis query
        narrate_results = db_manager.execute_query(analysis_query, fetch_all=True)
        logger.info(f"Analysis results: {narrate_results}")
        
        narration = ""
        if narrate_results and len(narrate_results) > 0:
            logger.info(f"NARRATE first result: {narrate_results[0]}")
            narration = str(narrate_results[0][0]) if narrate_results[0] and narrate_results[0][0] else "No results"
            logger.info(f"Final narration: {narration}")
        else:
            logger.warning("No NARRATE results returned")
        
        # Include both the generated SQL and narration in response
        display_info = f"**Generated SQL:**\n```sql\n{generated_sql}\n```\n\n**AI Response:**\n{narration}" if generated_sql else narration
        
        return UserSearchResponse(
            success=True,
            users=[],  # NARRATE returns text, not structured data
            total_found=0,
            sql_query=generated_sql if generated_sql else narrate_query,
            explanation=display_info  # Show both SQL and narration
        )
        
    except Exception as e:
        logger.error(f"SELECT AI error: {e}")
        return UserSearchResponse(
            success=False,
            error=str(e)
        )



if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "rest_livelabs_nl_query:app",
        host="127.0.0.1",
        port=8002,
        reload=False,
        log_level="info"
    )
