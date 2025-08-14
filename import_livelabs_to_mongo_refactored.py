#!/usr/bin/env python3
"""
Import LiveLabs workshops to MongoDB - Refactored Version
Uses common utilities for better maintainability and reusability
"""

import logging
from utils.mongo_utils import MongoManager
from utils.workshop_parser import WorkshopParser

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_workshops_to_mongo(json_filename="livelabs_workshops.json", collection_name="livelabs_workshops"):
    """Import workshops from JSON file to MongoDB"""
    
    # Load workshops from JSON
    workshops = WorkshopParser.load_workshops_from_json(json_filename)
    
    if not workshops:
        logger.error(f"No workshops found in {json_filename}")
        return False
    
    # Create MongoDB manager
    mongo_manager = MongoManager(collection_name=collection_name)
    
    # Insert workshops
    success = mongo_manager.insert_workshops(workshops)
    
    if success:
        logger.info(f"Successfully imported {len(workshops)} workshops to MongoDB")
        
        # Print summary
        WorkshopParser.print_workshop_summary(workshops, "IMPORTED WORKSHOPS SUMMARY")
        
        # Show MongoDB stats
        count = mongo_manager.count_workshops()
        logger.info(f"Total workshops in MongoDB: {count}")
    else:
        logger.error("Failed to import workshops to MongoDB")
    
    # Close connection
    mongo_manager.close()
    
    return success

def main():
    """Main function"""
    # Import workshops to MongoDB
    success = import_workshops_to_mongo()
    
    if success:
        print("✅ Successfully imported workshops to MongoDB")
    else:
        print("❌ Failed to import workshops to MongoDB")

if __name__ == "__main__":
    main() 