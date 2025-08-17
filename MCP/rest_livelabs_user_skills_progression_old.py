#!/usr/bin/env python3
"""
LiveLabs User Skills Progression REST API Service
Provides Oracle SELECT AI and skills progression analysis endpoints
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.oracle_db import DatabaseManager
from utils.mongo_utils import MongoManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LiveLabs User Skills Progression API",
    description="Oracle SELECT AI and skills progression analysis for LiveLabs",
    version="1.0.0"
)

# Global database managers
db_manager = None  # Oracle for workshop progressions
mongo_manager = None  # MongoDB for user profiles

# Request/Response Models
class UserSkillUpdate(BaseModel):
    skillName: str
    experienceLevel: str  # BEGINNER, INTERMEDIATE, ADVANCED
    skillAdded: Optional[str] = None  # Date string

class UpdateUserSkillsRequest(BaseModel):
    userId: str
    skills: List[UserSkillUpdate]
    name: Optional[str] = None
    email: Optional[str] = None

class UpdateUserSkillsResponse(BaseModel):
    success: bool
    message: str = ""
    updated_user: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class WorkshopProgression(BaseModel):
    userId: str
    workshopId: int
    status: str  # COMPLETED, IN_PROGRESS, NOT_STARTED
    completionDate: Optional[str] = None
    rating: Optional[int] = None

class UpdateWorkshopProgressionRequest(BaseModel):
    progressions: List[WorkshopProgression]

class UpdateWorkshopProgressionResponse(BaseModel):
    success: bool
    message: str = ""
    updated_count: int = 0
    progressions: List[Dict[str, Any]] = []
    error: Optional[str] = None

class GetProgressionRequest(BaseModel):
    userId: Optional[str] = None
    workshopId: Optional[int] = None

class GetProgressionResponse(BaseModel):
    success: bool
    progressions: List[Dict[str, Any]] = []
    total_found: int = 0
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize database managers on startup"""
    global db_manager, mongo_manager
    
    logger.info("User Skills Progression API: Initializing...")
    
    try:
        # Initialize Oracle connection for workshop progressions
        db_manager = DatabaseManager()
        test_result = db_manager.execute_query("SELECT 1 FROM DUAL", fetch_one=True)
        if test_result:
            logger.info("✅ Oracle connection established for workshop progressions")
        else:
            raise Exception("Oracle connection test failed")
        
        # Initialize MongoDB connection for user profiles
        mongo_manager = MongoManager(collection_name="user_profile_json")
        if not mongo_manager.initialize_connection():
            raise Exception("Failed to initialize MongoDB connection")
        
        logger.info("✅ MongoDB connection established for user profiles")
        logger.info("User Skills Progression API: Initialization complete")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    global db_manager, mongo_manager
    
    if db_manager:
        logger.info("Cleaning up Oracle connection...")
        DatabaseManager.close_pool()
    
    if mongo_manager:
        logger.info("Cleaning up MongoDB connection...")
        mongo_manager.close()

@app.get("/", response_model=Dict[str, str])
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "LiveLabs User Skills Progression API"}

@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """Detailed health check"""
    global db_manager, mongo_manager
    
    if not db_manager or not mongo_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return {
        "status": "healthy",
        "service": "LiveLabs User Skills Progression API",
        "version": "1.0.0",
        "oracle_connected": db_manager is not None,
        "mongodb_connected": mongo_manager is not None
    }

@app.post("/skills/progression", response_model=SkillsProgressionResponse)
async def analyze_skills_progression(request: SkillsProgressionRequest):
    """Analyze user skills progression using Oracle SELECT AI"""
    global db_manager
    
    if not db_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Analyzing skills progression for query: '{request.query}'")
        
        # Build the analysis query based on the request
        if request.user_id:
            # Specific user analysis
            base_query = f"""
            SELECT AI What are the skills and progression patterns for user '{request.user_id}' based on this query: '{request.query}'?
            FROM admin.user_profile_json
            WHERE JSON_VALUE(data, '$.userId') = '{request.user_id}'
            """
        else:
            # General skills progression analysis
            base_query = f"""
            SELECT AI Analyze the skills progression patterns based on this query: '{request.query}'
            FROM admin.user_profile_json
            WHERE JSON_EXISTS(data, '$.skills')
            """
        
        # Execute the query
        results = db_manager.execute_query(base_query)
        
        # Format the response
        analysis_text = "Skills Progression Analysis:\n\n"
        data_results = []
        
        if results:
            for row in results:
                # Convert row to dict for JSON serialization
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[f"column_{i}"] = str(value) if value is not None else ""
                data_results.append(row_dict)
                
                # Add to analysis text
                analysis_text += f"Result: {', '.join([str(v) for v in row if v is not None])}\n"
        else:
            analysis_text += "No specific progression data found for the given query.\n"
            analysis_text += f"Query analyzed: '{request.query}'\n"
            if request.user_id:
                analysis_text += f"User ID: {request.user_id}\n"
        
        logger.info(f"Skills progression analysis completed, {len(data_results)} results")
        
        return SkillsProgressionResponse(
            success=True,
            analysis=analysis_text,
            data=data_results
        )
        
    except Exception as e:
        logger.error(f"Skills progression analysis error: {e}")
        return SkillsProgressionResponse(
            success=False,
            error=str(e)
        )

@app.get("/skills/progression", response_model=SkillsProgressionResponse)
async def analyze_skills_progression_get(
    query: str = Query(..., description="Skills progression query"),
    user_id: Optional[str] = Query(None, description="Specific user ID to analyze")
):
    """GET endpoint for skills progression analysis"""
    request = SkillsProgressionRequest(query=query, user_id=user_id)
    return await analyze_skills_progression(request)

@app.post("/ai/select", response_model=SelectAIResponse)
async def execute_select_ai(request: SelectAIRequest):
    """Execute Oracle SELECT AI with natural language query"""
    global db_manager
    
    if not db_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Executing SELECT AI query: '{request.natural_language_query}'")
        
        # Build the SELECT AI query
        select_ai_query = f"""
        SELECT AI {request.natural_language_query}
        FROM admin.user_profile_json
        """
        
        # Execute the query
        results = db_manager.execute_query(select_ai_query)
        
        # Format the response
        data_results = []
        explanation = f"Natural language query: '{request.natural_language_query}'\n"
        explanation += f"Generated SQL: {select_ai_query}\n\n"
        
        if results:
            explanation += f"Results: {len(results)} rows returned\n"
            
            for row in results:
                # Convert row to dict for JSON serialization
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[f"column_{i}"] = str(value) if value is not None else ""
                data_results.append(row_dict)
        else:
            explanation += "No results returned from the query.\n"
        
        logger.info(f"SELECT AI query completed, {len(data_results)} results")
        
        return SelectAIResponse(
            success=True,
            sql_query=select_ai_query,
            results=data_results,
            explanation=explanation
        )
        
    except Exception as e:
        logger.error(f"SELECT AI error: {e}")
        return SelectAIResponse(
            success=False,
            error=str(e)
        )

@app.get("/ai/select", response_model=SelectAIResponse)
async def execute_select_ai_get(
    query: str = Query(..., description="Natural language query for SELECT AI")
):
    """GET endpoint for SELECT AI"""
    request = SelectAIRequest(natural_language_query=query)
    return await execute_select_ai(request)

@app.post("/ai/profile", response_model=AIProfileResponse)
async def set_ai_profile(request: AIProfileRequest):
    """Set up AI profile for SELECT AI queries"""
    global db_manager
    
    if not db_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Setting AI profile: {request.profile_name}")
        
        # Set the AI profile using DBMS_CLOUD_AI
        profile_sql = f"""
        BEGIN
            DBMS_CLOUD_AI.SET_PROFILE(
                profile_name => '{request.profile_name}',
                attributes => JSON_OBJECT(
                    'provider' VALUE 'oci',
                    'credential_name' VALUE 'OCI_CRED',
                    'object_list' VALUE JSON_ARRAY(
                        JSON_OBJECT(
                            'owner' VALUE 'ADMIN',
                            'name' VALUE 'USER_PROFILE_JSON'
                        )
                    ),
                    'profile_description' VALUE '{request.description}'
                )
            );
        END;
        """
        
        # Execute the profile setup
        db_manager.execute_query(profile_sql, fetch_results=False)
        
        logger.info(f"AI profile '{request.profile_name}' set successfully")
        
        return AIProfileResponse(
            success=True,
            message=f"AI profile '{request.profile_name}' has been set successfully"
        )
        
    except Exception as e:
        logger.error(f"AI profile setup error: {e}")
        return AIProfileResponse(
            success=False,
            error=str(e)
        )

@app.get("/ai/profile", response_model=AIProfileResponse)
async def set_ai_profile_get(
    profile_name: str = Query("LIVELABS_AI_PROFILE", description="AI profile name"),
    description: str = Query("AI profile for LiveLabs user skills analysis", description="Profile description")
):
    """GET endpoint for setting AI profile"""
    request = AIProfileRequest(profile_name=profile_name, description=description)
    return await set_ai_profile(request)

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "rest_livelabs_user_skills_progression:app",
        host="127.0.0.1",
        port=8003,
        reload=False,
        log_level="info"
    )
