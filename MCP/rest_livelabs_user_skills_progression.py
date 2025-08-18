#!/usr/bin/env python3
"""
LiveLabs User Skills Progression REST API Service
Provides user skills updates and workshop progression management
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.oracle_db import DatabaseManager
from utils.mongo_utils import MongoManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LiveLabs User Skills Progression API",
    description="User skills updates and workshop progression management for LiveLabs",
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
        "oracle_connected": "yes" if db_manager is not None else "no",
        "mongodb_connected": "yes" if mongo_manager is not None else "no"
    }

@app.get("/mcp/tools", response_model=Dict[str, Any])
async def list_tools():
    """Return available tools for this MCP service"""
    return {
        "tools": [
            {
                "name": "update_user_skills",
                "description": "Update a user's skills or add new skills to their profile",
                "parameters": {
                    "user_id": {
                        "type": "string", 
                        "required": True, 
                        "description": "User ID to update"
                    },
                    "skills": {
                        "type": "array", 
                        "required": True, 
                        "description": "List of skills to add or update"
                    },
                    "skill_level": {
                        "type": "string", 
                        "required": False, 
                        "default": "beginner", 
                        "description": "Skill level: beginner, intermediate, advanced"
                    }
                },
                "use_when": "User wants to add or update their skills",
                "examples": [
                    "add Python to my skills", 
                    "I learned machine learning", 
                    "update my Java level to advanced"
                ]
            },
            {
                "name": "mark_workshop_complete",
                "description": "Mark a workshop as completed for a user",
                "parameters": {
                    "user_id": {
                        "type": "string", 
                        "required": True, 
                        "description": "User ID"
                    },
                    "workshop_id": {
                        "type": "string", 
                        "required": True, 
                        "description": "Workshop ID or name"
                    },
                    "completion_date": {
                        "type": "string", 
                        "required": False, 
                        "description": "Completion date (ISO format)"
                    }
                },
                "use_when": "User reports completing a workshop or course",
                "examples": [
                    "I completed the Docker workshop", 
                    "finished AI fundamentals course", 
                    "mark Oracle DB course as done"
                ]
            }
        ],
        "service_info": {
            "name": "LiveLabs User Skills Progression API",
            "version": "1.0.0",
            "description": "User skills updates and workshop progression management for LiveLabs"
        }
    }

@app.post("/skills/update")
async def update_user_skills(request: UpdateUserSkillsRequest):
    """Update user skills in MongoDB user profile"""
    global mongo_manager
    
    if not mongo_manager:
        raise HTTPException(status_code=503, detail="MongoDB service not initialized")
    
    try:
        logger.info(f"Updating skills for user: {request.userId}")
        
        # Prepare skills data
        skills_data = []
        for skill in request.skills:
            skill_entry = {
                "skillName": skill.skillName,
                "experienceLevel": skill.experienceLevel.upper(),
                "skillAdded": skill.skillAdded or datetime.now().strftime("%Y-%m-%d")
            }
            skills_data.append(skill_entry)
        
        # Build update document
        update_doc = {"skills": skills_data}
        if request.name:
            update_doc["name"] = request.name
        if request.email:
            update_doc["email"] = request.email
        
        # Update skills in the separate user_skills_json collection
        # First, remove existing skills for this user
        skills_collection = mongo_manager.collection.database["user_skills_json"]
        skills_collection.delete_many({"userId": request.userId})
        
        # Then insert new skills
        skills_to_insert = []
        for skill in request.skills:
            skill_doc = {
                "userId": request.userId,
                "skillName": skill.skillName,
                "experienceLevel": skill.experienceLevel.upper(),
                "skillAdded": skill.skillAdded or datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            skills_to_insert.append(skill_doc)
        
        if skills_to_insert:
            result = skills_collection.insert_many(skills_to_insert)
            # Get the inserted documents for response
            inserted_skills = list(skills_collection.find({"userId": request.userId}))
        else:
            result = None
            inserted_skills = []
        
        if result or len(inserted_skills) > 0:
            # Convert ObjectId to string and clean up any non-UTF-8 data
            clean_skills = []
            for skill in inserted_skills:
                clean_skill = {}
                for key, value in skill.items():
                    if key == '_id':
                        clean_skill[key] = str(value)
                    elif isinstance(value, str):
                        # Ensure string values are UTF-8 compatible
                        try:
                            clean_skill[key] = value.encode('utf-8', 'ignore').decode('utf-8')
                        except:
                            clean_skill[key] = str(value)
                    else:
                        clean_skill[key] = value
                clean_skills.append(clean_skill)
            
            message = f"Successfully updated {len(clean_skills)} skills for user {request.userId}"
            logger.info(message)
            
            # Create a completely clean response with only basic data types
            response_data = {
                "success": True,
                "message": message,
                "updated_user": {
                    "userId": str(request.userId),
                    "skills": [
                        {
                            "skillName": str(skill.get("skillName", "")),
                            "experienceLevel": str(skill.get("experienceLevel", "")),
                            "userId": str(skill.get("userId", ""))
                        }
                        for skill in clean_skills
                    ]
                }
            }
            
            return response_data
        else:
            raise Exception("Failed to update user skills")
        
    except Exception as e:
        logger.error(f"Error updating user skills: {e}")
        return {
            "success": False,
            "message": f"Error updating user skills: {str(e)}",
            "updated_user": None
        }

@app.post("/progression/update")
async def update_workshop_progression(request: UpdateWorkshopProgressionRequest):
    """Update workshop progression using MongoDB JSON Relational Duality View"""
    global mongo_manager
    
    if not mongo_manager:
        raise HTTPException(status_code=503, detail="MongoDB service not initialized")
    
    try:
        logger.info(f"Updating {len(request.progressions)} workshop progressions")
        
        updated_progressions = []
        
        progress_collection = mongo_manager.collection.database["user_progress_json"]
        
        for progression in request.progressions:
            # Create progression document with valid status values
            # Map status to match database constraint: status IN ('STARTED', 'COMPLETED')
            valid_status = progression.status
            if progression.status == "IN_PROGRESS":
                valid_status = "STARTED"
            elif progression.status not in ["STARTED", "COMPLETED"]:
                valid_status = "STARTED"  # Default to STARTED for any other status
                
            progression_doc = {
                "userId": progression.userId,
                "workshopId": progression.workshopId,
                "status": valid_status
            }
            
            # Add optional fields
            if progression.completionDate:
                progression_doc["completionDate"] = progression.completionDate
            elif valid_status == "COMPLETED":
                progression_doc["completionDate"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            
            if progression.rating:
                progression_doc["rating"] = progression.rating
            
            # Always set created timestamp
            progression_doc["created"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            
            # Check if record exists first (upsert not supported on duality views)
            query = {"userId": progression.userId, "workshopId": progression.workshopId}
            existing_record = progress_collection.find_one(query)
            
            if existing_record:
                # Update existing record
                result = progress_collection.find_one_and_update(
                    query,
                    {"$set": progression_doc},
                    return_document=True
                )
            else:
                # Insert new record
                insert_result = progress_collection.insert_one(progression_doc)
                if insert_result.inserted_id:
                    result = progress_collection.find_one({"_id": insert_result.inserted_id})
                else:
                    result = None
            
            if result:
                # Convert ObjectId to string and clean up any non-UTF-8 data
                clean_result = {}
                for key, value in result.items():
                    if key == '_id':
                        clean_result[key] = str(value)
                    elif isinstance(value, str):
                        # Ensure string values are UTF-8 compatible
                        try:
                            clean_result[key] = value.encode('utf-8', 'ignore').decode('utf-8')
                        except:
                            clean_result[key] = str(value)
                    else:
                        clean_result[key] = value
                updated_progressions.append(clean_result)
        
        message = f"Successfully updated {len(updated_progressions)} workshop progressions"
        logger.info(message)
        
        # Create a completely clean response with only basic data types
        clean_progressions = []
        for prog in updated_progressions:
            clean_prog = {
                "userId": str(prog.get("userId", "")),
                "workshopId": str(prog.get("workshopId", "")),
                "status": str(prog.get("status", "")),
                "rating": int(prog.get("rating", 0)) if prog.get("rating") else None
            }
            # Handle completionDate safely
            completion_date = prog.get("completionDate")
            if completion_date:
                clean_prog["completionDate"] = str(completion_date)
            clean_progressions.append(clean_prog)
        
        response_data = {
            "success": True,
            "message": message,
            "updated_count": len(clean_progressions),
            "progressions": clean_progressions
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error updating workshop progression: {e}")
        return {
            "success": False,
            "message": f"Error updating workshop progression: {str(e)}",
            "updated_count": 0,
            "progressions": []
        }

@app.post("/progression/get", response_model=GetProgressionResponse)
async def get_workshop_progression(request: GetProgressionRequest):
    """Get workshop progression records"""
    global db_manager
    
    if not db_manager:
        raise HTTPException(status_code=503, detail="Oracle service not initialized")
    
    try:
        logger.info(f"Getting workshop progression - userId: {request.userId}, workshopId: {request.workshopId}")
        
        # Build query based on filters
        where_conditions = []
        params = {}
        
        if request.userId:
            where_conditions.append("user_id = :user_id")
            params['user_id'] = request.userId
        
        if request.workshopId:
            where_conditions.append("workshop_id = :workshop_id")
            params['workshop_id'] = request.workshopId
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"""
        SELECT user_id, workshop_id, status, completion_date, rating, 
               created_date, updated_date
        FROM admin.livelabs_workshop_progression
        {where_clause}
        ORDER BY created_date DESC
        """
        
        results = db_manager.execute_query(query, params=params)
        
        progressions = []
        if results:
            for row in results:
                progression = {
                    'userId': row[0],
                    'workshopId': row[1],
                    'status': row[2],
                    'completionDate': str(row[3]) if row[3] else None,
                    'rating': row[4],
                    'createdDate': str(row[5]) if row[5] else None,
                    'updatedDate': str(row[6]) if row[6] else None
                }
                progressions.append(progression)
        
        logger.info(f"Found {len(progressions)} progression records")
        
        return GetProgressionResponse(
            success=True,
            progressions=progressions,
            total_found=len(progressions)
        )
        
    except Exception as e:
        logger.error(f"Error getting workshop progression: {e}")
        return GetProgressionResponse(
            success=False,
            error=str(e)
        )

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "rest_livelabs_user_skills_progression:app",
        host="127.0.0.1",
        port=8003,
        reload=False,
        log_level="info"
    )
