#!/usr/bin/env python3
"""
LiveLabs Semantic Search REST API Service
Provides vector search and statistics endpoints
"""

import os
import sys
import json
import logging
import asyncio
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

from utils.vector_search import VectorSearchEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LiveLabs Semantic Search API",
    description="Vector search and statistics for LiveLabs workshops",
    version="1.0.0"
)

# Global vector search engine
vector_search_engine = None

# Request/Response Models
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 10

class SearchResult(BaseModel):
    id: int
    title: str
    author: str
    difficulty: str
    category: str
    duration: str
    content: str
    similarity: float
    url: str

class SearchResponse(BaseModel):
    success: bool
    results: List[SearchResult] = []
    total_found: int = 0
    error: Optional[str] = None

class StatisticsResponse(BaseModel):
    success: bool
    total_workshops: int = 0
    difficulty_breakdown: Dict[str, int] = {}
    category_breakdown: Dict[str, int] = {}
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the vector search engine on startup"""
    global vector_search_engine
    
    logger.info("Semantic Search API: Initializing...")
    
    try:
        vector_search_engine = VectorSearchEngine()
        if not vector_search_engine.initialize_connections():
            raise Exception("Failed to initialize connections")
        
        logger.info("Semantic Search API: Initialization complete, connections established.")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    global vector_search_engine
    
    if vector_search_engine:
        logger.info("Cleaning up connections...")
        # Add cleanup logic if needed

@app.get("/", response_model=Dict[str, str])
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "LiveLabs Semantic Search API"}

@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """Detailed health check"""
    global vector_search_engine
    
    if not vector_search_engine:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return {
        "status": "healthy",
        "service": "LiveLabs Semantic Search API",
        "version": "1.0.0"
    }

@app.get("/mcp/tools", response_model=Dict[str, Any])
async def list_tools():
    """Return available tools for this MCP service"""
    return {
        "tools": [
            {
                "name": "search_livelabs_workshops",
                "description": "Search for LiveLabs workshops using semantic similarity based on query text",
                "parameters": {
                    "query": {
                        "type": "string", 
                        "required": True, 
                        "description": "Search query text"
                    },
                    "top_k": {
                        "type": "integer", 
                        "required": False, 
                        "description": "Number of results to return (default: 10)"
                    }
                },
                "use_when": "User wants to find workshops or courses related to specific topics",
                "examples": [
                    "find machine learning workshops", 
                    "search for database courses", 
                    "show me cloud computing labs"
                ]
            }
        ],
        "service_info": {
            "name": "LiveLabs Semantic Search API",
            "version": "1.0.0",
            "description": "Vector search and statistics for LiveLabs workshops"
        }
    }

@app.post("/search", response_model=SearchResponse)
async def search_workshops(request: SearchRequest):
    """Search for workshops using vector similarity"""
    global vector_search_engine
    
    if not vector_search_engine:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Searching for: '{request.query}' with top_k={request.top_k}")
        
        # Perform vector search
        results = vector_search_engine.search_similar_workshops(
            query_text=request.query,
            top_k=request.top_k
        )
        
        # Convert results to response format
        search_results = []
        for result in results:
            # Ensure types for pydantic validation
            author = result.get('author') or ""
            try:
                similarity_val = float(result.get('similarity')) if result.get('similarity') is not None else 0.0
            except (ValueError, TypeError):
                similarity_val = 0.0

            content_src = result.get('text_content', result.get('content', '')) or ''
            content_trim = (content_src[:500] + "...") if len(content_src) > 500 else content_src

            search_results.append(SearchResult(
                id=int(result['id']),
                title=str(result.get('title', '')),
                author=str(author),
                difficulty=str(result.get('difficulty', '')),
                category=str(result.get('category', '')),
                duration=str(result.get('duration_estimate', result.get('duration', '')) or ''),
                content=content_trim,
                similarity=similarity_val,
                url=str(result.get('url', '') or '')
            ))
        
        logger.info(f"Found {len(search_results)} results")
        
        return SearchResponse(
            success=True,
            results=search_results,
            total_found=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return SearchResponse(
            success=False,
            error=str(e)
        )

@app.get("/search", response_model=SearchResponse)
async def search_workshops_get(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(10, description="Number of results to return")
):
    """GET endpoint for searching workshops"""
    request = SearchRequest(query=query, top_k=top_k)
    return await search_workshops(request)

@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Get workshop statistics"""
    global vector_search_engine
    
    if not vector_search_engine:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info("Getting workshop statistics")
        
        # Get real statistics from database
        total_query = "SELECT COUNT(*) as total FROM admin.livelabs_workshops2 WHERE cohere4_embedding IS NOT NULL"
        total_result = vector_search_engine.oracle_manager.execute_query(total_query, fetch_one=True)
        total_workshops = total_result[0] if total_result else 0

        difficulty_query = """
        SELECT difficulty, COUNT(*) as count
        FROM admin.livelabs_workshops2
        WHERE cohere4_embedding IS NOT NULL AND difficulty IS NOT NULL
        GROUP BY difficulty
        ORDER BY count DESC
        """
        difficulty_results = vector_search_engine.oracle_manager.execute_query(difficulty_query)

        category_query = """
        SELECT category, COUNT(*) as count
        FROM admin.livelabs_workshops2
        WHERE cohere4_embedding IS NOT NULL AND category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
        FETCH FIRST 10 ROWS ONLY
        """
        category_results = vector_search_engine.oracle_manager.execute_query(category_query)

        # Format results
        difficulty_breakdown = {}
        for row in difficulty_results:
            difficulty, count = row
            difficulty_breakdown[difficulty] = count

        category_breakdown = {}
        for row in category_results:
            category, count = row
            category_breakdown[category] = count

        logger.info(f"Statistics: {total_workshops} workshops, {len(difficulty_breakdown)} difficulties, {len(category_breakdown)} categories")

        return StatisticsResponse(
            success=True,
            total_workshops=total_workshops,
            difficulty_breakdown=difficulty_breakdown,
            category_breakdown=category_breakdown
        )

    except Exception as e:
        logger.error(f"Statistics error: {e}")
        return StatisticsResponse(
            success=False,
            error=str(e)
        )

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "rest_livelabs_semantic_search:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
        log_level="info"
    )
