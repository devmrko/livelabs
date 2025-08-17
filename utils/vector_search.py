#!/usr/bin/env python3
"""
Vector Search for LiveLabs Workshops
Converts input text to embedding and finds closest matches in Oracle database
"""

import logging
import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple
from utils.oci_embedding import init_client, get_embeddings
from utils.oracle_db import DatabaseManager
import oci

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
except ImportError:
    logger.info("python-dotenv not available, using system environment variables")

class VectorSearchEngine:
    """Vector search engine for LiveLabs workshops"""
    
    def __init__(self):
        self.oracle_manager = None
        self.oci_client = None
        self.compartment_id = None
        
    def initialize_connections(self):
        """Initialize Oracle and OCI connections"""
        logger.info("=== Initializing Connections ===")
        
        # Initialize Oracle connection
        try:
            self.oracle_manager = DatabaseManager()
            # Test connection
            test_result = self.oracle_manager.execute_query("SELECT 1 FROM DUAL", fetch_one=True)
            if test_result:
                logger.info("✅ Oracle connection established")
            else:
                raise Exception("Oracle connection test failed")
        except Exception as e:
            logger.error(f"❌ Oracle connection failed: {e}")
            return False
        
        # Initialize OCI client
        try:
            config = oci.config.from_file()
            self.compartment_id = config.get("tenancy")
            if not self.compartment_id:
                raise Exception("Compartment ID not found in OCI config")
            
            self.oci_client = init_client(config)
            logger.info("✅ OCI client initialized")
        except Exception as e:
            logger.error(f"❌ OCI client initialization failed: {e}")
            return False
        
        return True
    
    def text_to_embedding(self, text: str) -> List[float]:
        """Convert input text to embedding vector"""
        try:
            logger.info(f"Converting text to embedding: '{text}'")
            
            # Generate embedding for the input text
            embeddings = get_embeddings(self.oci_client, self.compartment_id, [text])
            
            if embeddings and len(embeddings) == 1:
                embedding_vector = embeddings[0]
                logger.info(f"✅ Generated embedding with {len(embedding_vector)} dimensions")
                return embedding_vector
            else:
                logger.error("❌ Failed to generate embedding")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            return None
    
    def search_similar_workshops(self, query_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar workshops using Oracle's native vector search"""
        logger.info(f"=== Vector Search for: '{query_text}' ===")
        
        # Convert query text to embedding
        query_embedding = self.text_to_embedding(query_text)
        if not query_embedding:
            logger.error("❌ Failed to generate query embedding")
            return []
        
        try:
            # Convert embedding list to Oracle vector format
            # Oracle expects the vector in a specific format
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # Use Oracle's native vector_distance function with COSINE similarity
            # Handle CLOB columns using DBMS_LOB package
            query = """
            SELECT 
                w.id,
                w.mongo_id,
                w.title,
                'https://livelabs.oracle.com' || w.url AS url,
                DBMS_LOB.SUBSTR(w.description, 4000, 1) AS description,
                w.author,
                w.difficulty,
                w.category,
                w.duration_estimate,
                DBMS_LOB.SUBSTR(w.text_content, 4000, 1) AS text_content,
                vector_distance(w.cohere4_embedding, :query_vector, COSINE) AS similarity
            FROM admin.livelabs_workshops2 w
            WHERE w.cohere4_embedding IS NOT NULL
            ORDER BY similarity
            FETCH FIRST :top_k ROWS ONLY
            """
            
            params = {
                'query_vector': embedding_str,
                'top_k': top_k
            }
            
            results = self.oracle_manager.execute_query(query, params=params, fetch_all=True)
            
            if results:
                workshops = []
                for row in results:
                    # Column order must match the SELECT above
                    workshop = {
                        'id': row[0],
                        'mongo_id': row[1],
                        'title': row[2],
                        'url': row[3],
                        'description': row[4],
                        'author': row[5],
                        'difficulty': row[6],
                        'category': row[7],
                        'duration_estimate': row[8],
                        'text_content': row[9],
                        'similarity': row[10]
                    }
                    workshops.append(workshop)
                
                logger.info(f"✅ Found {len(workshops)} similar workshops using Oracle vector search")
                return workshops
            else:
                logger.warning("⚠️  No similar workshops found")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error in vector search: {e}")
            return []
    
    def display_search_results(self, results: List[Dict[str, Any]], query_text: str):
        """Display search results in a formatted way"""
        logger.info(f"\n=== Search Results for: '{query_text}' ===")
        
        if not results:
            logger.info("No similar workshops found")
            return
        
        for i, result in enumerate(results, 1):
            similarity = result['similarity']
            
            logger.info(f"\n{i}. Similarity: {similarity:.4f}")
            logger.info(f"   Title: {result.get('title', 'N/A')}")
            logger.info(f"   ID: {result.get('id', 'N/A')}")
            logger.info(f"   Author: {result.get('author', 'N/A')}")
            logger.info(f"   Difficulty: {result.get('difficulty', 'N/A')}")
            logger.info(f"   Category: {result.get('category', 'N/A')}")
            logger.info(f"   Duration: {result.get('duration_estimate', 'N/A')}")
            
            description = result.get('description', '')
            if description:
                # Truncate long descriptions
                desc_preview = description[:150] + "..." if len(description) > 150 else description
                logger.info(f"   Description: {desc_preview}")
            
            text_content = result.get('text_content', '')
            if text_content:
                # Truncate long text content
                content_preview = text_content[:200] + "..." if len(text_content) > 200 else text_content
                logger.info(f"   Content: {content_preview}")
    
    def cleanup(self):
        """Clean up connections"""
        logger.info("=== Cleaning Up Connections ===")
        
        if self.oracle_manager:
            DatabaseManager.close_pool()
            logger.info("Oracle connection pool closed")

def main():
    """Main function to run vector search"""
    logger.info("Starting Vector Search Engine")
    
    # Check environment variables
    required_env_vars = ["DB_USER", "DB_PASSWORD", "DB_DSN"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        exit(1)
    
    # Create search engine
    search_engine = VectorSearchEngine()
    
    # Initialize connections
    if not search_engine.initialize_connections():
        logger.error("❌ Failed to initialize connections")
        exit(1)
    
    try:
        # Example search queries
        search_queries = [
            "big data service",
            "machine learning",
            "database security",
            "cloud infrastructure",
            "APEX development"
        ]
        
        for query in search_queries:
            # Perform vector search
            results = search_engine.search_similar_workshops(query, top_k=10)
            
            # Display results
            search_engine.display_search_results(results, query)
            
            logger.info("\n" + "="*80 + "\n")
    
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        exit(1)
    finally:
        search_engine.cleanup()

if __name__ == "__main__":
    main()
