#!/usr/bin/env python3
"""
Batch Job: MongoDB -> OCI Embeddings -> Oracle Database Update
Selects workshops from MongoDB, generates embeddings via OCI, and updates Oracle DB
"""

import logging
import os
import json
from typing import List, Dict, Any
from datetime import datetime
from utils.mongo_utils import MongoManager
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

class BatchEmbeddingProcessor:
    """Batch processor for MongoDB -> OCI Embeddings -> Oracle DB updates"""
    
    def __init__(self):
        self.mongo_manager = None
        self.oracle_manager = None
        self.oci_client = None
        self.compartment_id = None
        self.processed_count = 0
        self.updated_count = 0
        self.error_count = 0
        
    def initialize_connections(self):
        """Initialize all database and OCI connections"""
        logger.info("=== Initializing Connections ===")
        
        # Initialize MongoDB connection
        try:
            self.mongo_manager = MongoManager(collection_name="livelabs_workshops_json2")
            if not self.mongo_manager.connect():
                raise Exception("Failed to connect to MongoDB")
            logger.info("✅ MongoDB connection established")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            return False
        
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
    
    def get_workshops_from_mongo(self, limit: int = None) -> List[Dict[str, Any]]:
        """Retrieve workshops from MongoDB"""
        logger.info(f"=== Retrieving Workshops from MongoDB ===")
        
        try:
            workshops = self.mongo_manager.find_workshops(limit=limit)
            logger.info(f"✅ Retrieved {len(workshops)} workshops from MongoDB")
            return workshops
        except Exception as e:
            logger.error(f"❌ Error retrieving workshops from MongoDB: {e}")
            return []
    
    def prepare_text_for_embedding(self, workshop: Dict[str, Any]) -> str:
        """Prepare workshop text for embedding generation using entire JSON document"""
        # Convert the entire workshop document to JSON string
        # This preserves the complete structure and all data
        
        try:
            # Convert the entire workshop document to JSON
            json_text = json.dumps(workshop, ensure_ascii=False, default=str)
            
            # Limit total length to avoid token limits (typically 8192 tokens for Cohere)
            # Assuming average 4 characters per token, limit to ~6000 characters
            if len(json_text) > 6000:
                json_text = json_text[:6000] + "..."
            
            return json_text
            
        except Exception as e:
            logger.error(f"Error converting workshop to JSON: {e}")
            # Fallback: return a simple string representation
            return str(workshop)
    
    def generate_embeddings(self, workshops: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """Generate embeddings for each workshop individually"""
        logger.info(f"=== Generating Embeddings for {len(workshops)} workshops ===")
        
        embeddings_dict = {}
        
        for i, workshop in enumerate(workshops, 1):
            mongo_id = workshop.get('_id')  # MongoDB _id field
            if not mongo_id:
                logger.warning(f"⚠️  Workshop {i} missing _id field, skipping")
                continue
            
            try:
                # Prepare text for this workshop
                text = self.prepare_text_for_embedding(workshop)
                
                # Log a sample of the embedding text for the first workshop
                if i == 1:
                    logger.info(f"Sample JSON embedding text for workshop {mongo_id}:")
                    logger.info(f"  Length: {len(text)} characters")
                    logger.info(f"  Preview: {text[:200]}...")
                
                # Generate embedding for this workshop
                embeddings = get_embeddings(self.oci_client, self.compartment_id, [text])
                
                if embeddings and len(embeddings) == 1:
                    # Store the embedding for this workshop
                    embeddings_dict[mongo_id] = embeddings[0]
                    logger.info(f"✅ Generated embedding for workshop {mongo_id} ({i}/{len(workshops)})")
                else:
                    logger.warning(f"⚠️  Failed to generate embedding for workshop {mongo_id}")
                    
            except Exception as e:
                logger.error(f"❌ Error generating embedding for workshop {mongo_id}: {e}")
                continue
        
        logger.info(f"✅ Total embeddings generated: {len(embeddings_dict)}")
        return embeddings_dict
    
    def update_oracle_with_embeddings(self, embeddings_dict: Dict[str, List[float]]) -> bool:
        """Update Oracle database with embeddings"""
        logger.info(f"=== Updating Oracle Database ===")
        
        if not embeddings_dict:
            logger.warning("No embeddings to update")
            return True
        
        success_count = 0
        error_count = 0
        
        for mongo_id, embedding in embeddings_dict.items():
            try:
                # Convert embedding list to string for Oracle storage
                embedding_str = json.dumps(embedding)
                
                # Update query for Oracle - using mongo_id as primary key
                update_query = """
                UPDATE admin.livelabs_workshops2 
                SET cohere4_embedding = :embedding
                WHERE mongo_id = :mongo_id
                """
                
                params = {
                    'embedding': embedding_str,
                    'mongo_id': mongo_id
                }
                
                # Execute update
                result = self.oracle_manager.execute_query(
                    update_query, 
                    params=params, 
                    commit=True
                )
                
                if result is not None:
                    success_count += 1
                    if success_count % 10 == 0:
                        logger.info(f"Updated {success_count} workshops so far...")
                else:
                    error_count += 1
                    logger.warning(f"⚠️  No rows updated for mongo_id: {mongo_id}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error updating workshop {mongo_id}: {e}")
                continue
        
        logger.info(f"✅ Oracle update completed: {success_count} successful, {error_count} errors")
        return error_count == 0
    
    def process_workshops(self, limit: int = None):
        """Main processing method"""
        logger.info("=== Starting Workshop Embedding Processing ===")
        
        # Initialize connections
        if not self.initialize_connections():
            logger.error("❌ Failed to initialize connections")
            return False
        
        try:
            # Get workshops from MongoDB
            workshops = self.get_workshops_from_mongo(limit=limit)
            if not workshops:
                logger.error("❌ No workshops retrieved from MongoDB")
                return False
            
            self.processed_count = len(workshops)
            logger.info(f"Processing {self.processed_count} workshops")
            
            # Generate embeddings
            embeddings_dict = self.generate_embeddings(workshops)
            if not embeddings_dict:
                logger.error("❌ No embeddings generated")
                return False
            
            # Update Oracle database
            success = self.update_oracle_with_embeddings(embeddings_dict)
            if success:
                self.updated_count = len(embeddings_dict)
                logger.info(f"✅ Successfully updated {self.updated_count} workshops")
            else:
                logger.error("❌ Oracle update failed")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up connections"""
        logger.info("=== Cleaning Up Connections ===")
        
        if self.mongo_manager:
            self.mongo_manager.close()
            logger.info("MongoDB connection closed")
        
        if self.oracle_manager:
            DatabaseManager.close_pool()
            logger.info("Oracle connection pool closed")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary"""
        return {
            'processed_count': self.processed_count,
            'updated_count': self.updated_count,
            'error_count': self.error_count,
            'success_rate': (self.updated_count / self.processed_count * 100) if self.processed_count > 0 else 0
        }

def main():
    """Main function to run the batch processing"""
    logger.info("Starting Batch Embedding Update Job")
    
    # Check environment variables
    required_env_vars = [
        "MONGO_USER", "MONGO_PASSWORD", "MONGO_HOST", "MONGO_PORT",
        "DB_USER", "DB_PASSWORD", "DB_DSN"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        exit(1)
    
    # Create processor
    processor = BatchEmbeddingProcessor()
    
    # Process with parameters (adjust as needed)
    success = processor.process_workshops(
        #limit=50  # Process first 50 workshops (adjust or remove for all)

    )
    
    if success:
        summary = processor.get_summary()
        logger.info("=== Processing Summary ===")
        logger.info(f"Total processed: {summary['processed_count']}")
        logger.info(f"Successfully updated: {summary['updated_count']}")
        logger.info(f"Errors: {summary['error_count']}")
        logger.info(f"Success rate: {summary['success_rate']:.2f}%")
        logger.info("🎉 Batch processing completed successfully!")
    else:
        logger.error("❌ Batch processing failed")
        exit(1)

if __name__ == "__main__":
    main()
