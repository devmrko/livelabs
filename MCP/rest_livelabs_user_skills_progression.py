#!/usr/bin/env python3
"""
LiveLabs User Skills Progression REST API Service
Provides user skills updates and workshop progression management
"""

import os
import sys

# Add the project root to Python path before other imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

import logging
import uuid
from typing import Dict, Optional, Any
from fastmcp import FastMCP
from dotenv import load_dotenv
from utils.mongo_utils import MongoManager

# Load environment variables and configure logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Global Services ---
mongo_manager = MongoManager()
mongo_manager.connect()

mcp = FastMCP(
    name="livelabs-user-skills"
)

# --- Tool Definitions ---

@mcp.tool()
async def add_user(name: str, email: str) -> Dict[str, Any]:
    """Creates a new user account in the LiveLabs system with unique userId generation.
    
    Parameters:
    - name (str): Full name of the user (e.g., 'John Smith')
    - email (str): Valid email address for the user (must be unique)
    
    Returns: JSON with success status and user details including auto-generated userId
    Use cases: User registration, account creation, onboarding new learners
    """
    logger.info(f"Executing add_user for {email}")
    try:
        users_collection = mongo_manager.db["livelabs_users_json"]
        
        if users_collection.find_one({"email": email}):
            return {"success": False, "error": f"User with email {email} already exists."}
        
        user_data = {
            "userId": str(uuid.uuid4()),
            "name": name,
            "email": email
        }
        result = users_collection.insert_one(user_data)
        if result.inserted_id:
            user_data.pop('_id', None)
            return {"success": True, "user": user_data}
        else:
            return {"success": False, "error": "Failed to add user."}
    except Exception as e:
        logger.error(f"Error in add_user: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_user(name: Optional[str] = None, email: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves user profile information from LiveLabs system by name or email lookup.
    
    Parameters:
    - name (Optional[str]): User's full name for search (partial matches supported)
    - email (Optional[str]): User's email address for exact lookup
    
    Returns: JSON with user details (userId, name, email, createdDate, metadata)
    Use cases: User lookup, profile verification, finding userId for other operations
    Note: Provide at least one parameter (name or email) for search
    """
    logger.info(f"Executing get_user for name='{name}', email='{email}'")
    try:
        users_collection = mongo_manager.db["livelabs_users_json"]
        query = {}
        if name: query["name"] = name
        if email: query["email"] = email
        
        if not query:
            return {"success": False, "error": "Either name or email is required."}

        user_doc = users_collection.find_one(query, {"_id": 0})
        if user_doc:
            logger.info(f"Raw user document: {user_doc}")
            logger.info(f"User document type: {type(user_doc)}")
            for key, value in user_doc.items():
                logger.info(f"Key: {key}, Value: {value}, Type: {type(value)}")
            
            # Convert to simple dict with string values only
            cleaned_user = {}
            for key, value in user_doc.items():
                if value is None:
                    cleaned_user[key] = None
                else:
                    # Convert everything to string to avoid encoding issues
                    cleaned_user[key] = str(value)
            
            logger.info(f"Cleaned user document: {cleaned_user}")
            return {"success": True, "user": cleaned_user}
        else:
            return {"success": False, "error": "User not found."}
    except Exception as e:
        logger.error(f"Error in get_user: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
async def update_user(userId: str, name: Optional[str] = None, email: Optional[str] = None) -> Dict[str, Any]:
    """Updates existing user profile information in the LiveLabs system.
    
    Parameters:
    - userId (str): Unique user identifier (UUID format)
    - name (Optional[str]): New full name for the user
    - email (Optional[str]): New email address for the user
    
    Returns: JSON with success status and confirmation message
    Use cases: Profile updates, name changes, email changes, account maintenance
    Note: Provide at least one field (name or email) to update
    """
    logger.info(f"Executing update_user for {userId}")
    try:
        users_collection = mongo_manager.db["livelabs_users_json"]
        update_fields = {}
        if name: update_fields["name"] = name
        if email: update_fields["email"] = email

        if not update_fields:
            return {"success": False, "error": "No fields to update."}

        result = users_collection.update_one({"userId": userId}, {"$set": update_fields})
        if result.modified_count > 0:
            return {"success": True, "message": f"User {userId} updated."}
        else:
            return {"success": False, "error": f"User {userId} not found or no changes made."}
    except Exception as e:
        logger.error(f"Error in update_user: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
async def update_user_skills(userId: str, skillName: str, experienceLevel: str) -> Dict[str, Any]:
    """Adds or updates a user's technical skill with proficiency level in the LiveLabs system.
    
    Parameters:
    - userId (str): Unique user identifier (UUID format)
    - skillName (str): Name of the skill (e.g., 'Python Programming', 'Machine Learning', 'Docker')
    - experienceLevel (str): Proficiency level - must be 'BEGINNER', 'INTERMEDIATE', or 'ADVANCED'
    
    Returns: JSON with success status and confirmation message
    Use cases: Skill tracking, competency assessment, learning path planning, resume building
    Note: If skill exists for user, it will be updated; otherwise a new skill record is created
    """
    logger.info(f"Executing update_user_skills for {userId}")
    try:
        skills_collection = mongo_manager.db["user_skills_json"]
        
        # Validate experience level
        valid_levels = ["BEGINNER", "INTERMEDIATE", "ADVANCED"]
        if experienceLevel.upper() not in valid_levels:
            return {"success": False, "error": f"Invalid experience level. Must be one of: {valid_levels}"}
        
        skill_data = {
            "userId": userId,
            "skillName": skillName,
            "experienceLevel": experienceLevel.upper()
        }
        
        # Delete existing record if it exists, then insert new one
        existing_skill = skills_collection.find_one({"userId": userId, "skillName": skillName})
        
        if existing_skill:
            # Delete existing record
            delete_result = skills_collection.delete_one({"_id": existing_skill["_id"]})
            logger.info(f"Deleted existing skill record: {delete_result.deleted_count} documents")
        
        # Insert new record without _id (let Oracle auto-generate)
        logger.info(f"Inserting skill data: {skill_data}")
        result = skills_collection.insert_one(skill_data)
        if result.inserted_id:
            action = "updated" if existing_skill else "added"
            return {"success": True, "message": f"Skill '{skillName}' {action} for user {userId}."}
        else:
            return {"success": False, "error": "Failed to add skill."}
    except Exception as e:
        logger.error(f"Error in update_user_skills: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
async def update_workshop_progress(userId: str, workshopId: str, status: str, completionDate: Optional[str] = None, rating: Optional[int] = None) -> Dict[str, Any]:
    """Tracks and updates a user's progress through LiveLabs workshops and training sessions.
    
    Parameters:
    - userId (str): Unique user identifier (UUID format)
    - workshopId (str): Workshop identifier (numeric string, e.g., '961', '1234')
    - status (str): Progress status - must be 'STARTED' or 'COMPLETED'
    - completionDate (Optional[str]): ISO format date when completed (e.g., '2025-08-19T15:57:00')
    - rating (Optional[int]): User satisfaction rating from 1-5 (5 being highest)
    
    Returns: JSON with success status and confirmation message
    Use cases: Learning progress tracking, completion certificates, course analytics, user engagement
    Note: completionDate and rating are typically provided when status is 'COMPLETED'
    """
    logger.info(f"Executing update_workshop_progress for {userId}, {workshopId}")
    try:
        progress_collection = mongo_manager.db["user_progress_json"]
        
        # Convert workshopId to integer for Oracle compatibility
        try:
            workshop_id_int = int(workshopId)
        except ValueError:
            return {"success": False, "error": f"Invalid workshopId: must be a valid integer, got '{workshopId}'"}
        
        # Validate status
        valid_statuses = ["STARTED", "COMPLETED"]
        if status.upper() not in valid_statuses:
            return {"success": False, "error": f"Invalid status. Must be one of: {valid_statuses}"}
        
        # Validate rating if provided
        if rating is not None and (rating < 1 or rating > 5):
            return {"success": False, "error": "Rating must be between 1 and 5."}
        
        update_data = {"status": status.upper()}
        if completionDate: 
            update_data["completionDate"] = completionDate
        if rating is not None: 
            update_data["rating"] = rating

        # Delete existing record if it exists, then insert new one
        existing_progress = progress_collection.find_one({"userId": userId, "workshopId": workshop_id_int})
        
        if existing_progress:
            # Delete existing record
            delete_result = progress_collection.delete_one({"_id": existing_progress["_id"]})
            logger.info(f"Deleted existing progress record: {delete_result.deleted_count} documents")
        
        # Insert new record without _id (let Oracle auto-generate)
        progress_data = {
            "userId": userId,
            "workshopId": workshop_id_int,
            **update_data
        }
        logger.info(f"Inserting progress data: {progress_data}")
        
        result = progress_collection.insert_one(progress_data)
        if result.inserted_id:
            action = "updated" if existing_progress else "created"
            return {"success": True, "message": f"Workshop {workshopId} progress {action} for user {userId}."}
        else:
            return {"success": False, "error": "Failed to create workshop progress."}
    except Exception as e:
        logger.error(f"Error in update_workshop_progress: {e}")
        return {"success": False, "error": str(e)}

# --- Main Execution ---

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8003,
        path="/"
    )

