#!/usr/bin/env python3
"""
Test script for MongoDB Manager
Loads data from livelabs_workshops.json and tests various MongoDB operations
"""

import logging
import json
import os
from utils.mongo_utils import MongoManager

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

def load_workshops_from_json():
    """Load workshops data from the JSON file"""
    try:
        with open('livelabs_workshops.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        workshops = data.get('workshops', [])
        logger.info(f"Loaded {len(workshops)} workshops from JSON file")
        logger.info(f"Total workshops in JSON: {data.get('total_workshops', 0)}")
        logger.info(f"Scraped at: {data.get('scraped_at', 'Unknown')}")
        
        return workshops
    except FileNotFoundError:
        logger.error("livelabs_workshops.json file not found")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading workshops from JSON: {e}")
        return []

def test_mongo_connection():
    """Test MongoDB connection"""
    logger.info("=== Testing MongoDB Connection ===")
    
    mongo_manager = MongoManager(collection_name="livelabs_workshops_json")
    
    try:
        if mongo_manager.connect():
            logger.info("✅ MongoDB connection successful")
            return mongo_manager
        else:
            logger.error("❌ MongoDB connection failed")
            return None
    except Exception as e:
        logger.error(f"❌ Error connecting to MongoDB: {e}")
        return None

def test_workshop_data_analysis(mongo_manager, workshops):
    """Test analyzing workshop data from MongoDB"""
    logger.info("=== Testing Workshop Data Analysis ===")
    
    if not workshops:
        logger.warning("No workshops to analyze")
        return False
    
    try:
        # Get sample workshop IDs from JSON for testing
        sample_ids = [workshop['id'] for workshop in workshops[:5]]
        logger.info(f"Analyzing workshops with IDs: {sample_ids}")
        
        # Find these specific workshops in MongoDB
        for workshop_id in sample_ids:
            workshop = mongo_manager.find_workshops(
                filter_dict={"id": workshop_id}, 
                limit=1
            )
            if workshop:
                w = workshop[0]
                logger.info(f"  Found workshop {workshop_id}: {w.get('title', 'N/A')}")
                logger.info(f"    Duration: {w.get('duration', 'N/A')}")
                logger.info(f"    Views: {w.get('views', 'N/A')}")
            else:
                logger.info(f"  Workshop {workshop_id} not found in MongoDB")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error analyzing workshop data: {e}")
        return False

def test_single_workshop_query(mongo_manager):
    """Test querying a single workshop by ID"""
    logger.info("=== Testing Single Workshop Query ===")
    
    try:
        # Query a specific workshop that should exist
        workshop = mongo_manager.find_workshops(
            filter_dict={"id": "648"}, 
            limit=1
        )
        
        if workshop:
            w = workshop[0]
            logger.info(f"✅ Found workshop: {w.get('title', 'N/A')}")
            logger.info(f"   ID: {w.get('id', 'N/A')}")
            logger.info(f"   Description: {w.get('description', 'N/A')[:100]}...")
            logger.info(f"   Duration: {w.get('duration', 'N/A')}")
            logger.info(f"   Views: {w.get('views', 'N/A')}")
            logger.info(f"   URL: {w.get('url', 'N/A')}")
            return True
        else:
            logger.warning("⚠️  Workshop with ID '648' not found")
            return False
    except Exception as e:
        logger.error(f"❌ Error querying single workshop: {e}")
        return False

def test_find_workshops(mongo_manager):
    """Test finding workshops in MongoDB"""
    logger.info("=== Testing Workshop Search ===")
    
    try:
        # Test 1: Find all workshops
        all_workshops = mongo_manager.find_workshops(limit=3)
        logger.info(f"Found {len(all_workshops)} workshops (limited to 3)")
        
        if all_workshops:
            for i, workshop in enumerate(all_workshops, 1):
                logger.info(f"  {i}. ID: {workshop.get('id', 'N/A')}")
                logger.info(f"     Title: {workshop.get('title', 'N/A')[:60]}...")
                logger.info(f"     Duration: {workshop.get('duration', 'N/A')}")
                logger.info("")
        
        # Test 2: Find workshops with high view counts
        popular_workshops = mongo_manager.find_workshops(
            filter_dict={"views": {"$gt": 50000}}, 
            limit=2
        )
        logger.info(f"Found {len(popular_workshops)} popular workshops (>50k views)")
        
        if popular_workshops:
            for workshop in popular_workshops:
                logger.info(f"  Popular: {workshop.get('title', 'N/A')[:50]}... ({workshop.get('views', 0)} views)")
        
        # Test 3: Find workshop by ID
        specific_workshop = mongo_manager.find_workshops(
            filter_dict={"id": "648"}, 
            limit=1
        )
        if specific_workshop:
            workshop = specific_workshop[0]
            logger.info(f"Found specific workshop: {workshop.get('title', 'N/A')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error finding workshops: {e}")
        return False

def test_count_workshops(mongo_manager):
    """Test counting workshops in MongoDB"""
    logger.info("=== Testing Workshop Count ===")
    
    try:
        total_count = mongo_manager.count_workshops()
        logger.info(f"Total workshops in collection: {total_count}")
        
        # Count workshops by different criteria
        high_views_count = mongo_manager.collection.count_documents({"views": {"$gt": 100000}})
        logger.info(f"Workshops with >100k views: {high_views_count}")
        
        apex_count = mongo_manager.collection.count_documents({"title": {"$regex": "APEX", "$options": "i"}})
        logger.info(f"Workshops with 'APEX' in title: {apex_count}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error counting workshops: {e}")
        return False

def test_workshop_text_query(mongo_manager):
    """Test querying workshop text content"""
    logger.info("=== Testing Workshop Text Query ===")
    
    try:
        # Create a separate manager for workshop text collection
        text_manager = MongoManager(collection_name="workshop_texts")
        if not text_manager.connect():
            logger.warning("⚠️  workshop_texts collection not available, skipping text query test")
            return True  # Not a failure, just skip
        
        # Query existing workshop text documents
        text_docs = text_manager.find_workshops(limit=3)
        
        if text_docs:
            logger.info(f"✅ Found {len(text_docs)} workshop text documents")
            for i, doc in enumerate(text_docs, 1):
                logger.info(f"  {i}. Workshop ID: {doc.get('workshop_id', 'N/A')}")
                logger.info(f"     URL: {doc.get('url', 'N/A')}")
                logger.info(f"     Inserted: {doc.get('inserted_at', 'N/A')}")
        else:
            logger.info("ℹ️  No workshop text documents found in collection")
        
        text_manager.close()
        return True
    except Exception as e:
        logger.error(f"❌ Error querying workshop text: {e}")
        return False

def test_advanced_queries(mongo_manager):
    """Test advanced query operations"""
    logger.info("=== Testing Advanced Queries ===")
    
    try:
        # Test 1: Find workshops with high view counts
        high_views_workshops = mongo_manager.find_workshops(
            filter_dict={"views": {"$gt": 100000}}, 
            limit=3
        )
        logger.info(f"✅ Found {len(high_views_workshops)} workshops with >100k views")
        
        # Test 2: Find workshops by duration pattern
        short_workshops = mongo_manager.find_workshops(
            filter_dict={"duration": {"$regex": "15 mins"}}, 
            limit=2
        )
        logger.info(f"✅ Found {len(short_workshops)} workshops with 15-minute duration")
        
        # Test 3: Find workshops by title pattern
        apex_workshops = mongo_manager.find_workshops(
            filter_dict={"title": {"$regex": "APEX", "$options": "i"}}, 
            limit=3
        )
        logger.info(f"✅ Found {len(apex_workshops)} workshops with 'APEX' in title")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error in advanced queries: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting MongoDB Manager Test")
    
    # Check if environment variables are set
    required_env_vars = ["MONGO_USER", "MONGO_PASSWORD", "MONGO_HOST", "MONGO_PORT"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set these variables in your environment or .env file")
        exit(1)
    
    # Load workshops from JSON
    workshops = load_workshops_from_json()
    if not workshops:
        logger.error("No workshops loaded from JSON file")
        exit(1)
    
    # Test MongoDB connection
    mongo_manager = test_mongo_connection()
    if not mongo_manager:
        logger.error("MongoDB connection failed, exiting")
        exit(1)
    
    try:
        # Run all tests
        test_results = []
        
        test_results.append(test_workshop_data_analysis(mongo_manager, workshops))
        test_results.append(test_single_workshop_query(mongo_manager))
        test_results.append(test_find_workshops(mongo_manager))
        test_results.append(test_count_workshops(mongo_manager))
        test_results.append(test_workshop_text_query(mongo_manager))
        test_results.append(test_advanced_queries(mongo_manager))
        
        # Summary
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        logger.info(f"\n=== Test Summary ===")
        logger.info(f"Passed: {passed_tests}/{total_tests} tests")
        
        if passed_tests == total_tests:
            logger.info("🎉 All tests completed successfully!")
        else:
            logger.warning("⚠️  Some tests failed")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        exit(1)
    finally:
        # Close MongoDB connection
        mongo_manager.close()
        logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main()
