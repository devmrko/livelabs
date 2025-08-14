#!/usr/bin/env python3
"""
Test script for Oracle Database Manager
Queries the admin.livelabs_workshops2 table and logs the results
"""

import logging
import os
from utils.oracle_db import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_livelabs_workshops_query():
    """Test querying the admin.livelabs_workshops2 table"""
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    try:
        # Test 1: Get total count of workshops
        logger.info("=== Testing Workshop Count Query ===")
        count_query = "SELECT COUNT(*) FROM admin.livelabs_workshops2"
        count_result = db_manager.execute_query(count_query, fetch_one=True)
        logger.info(f"Total workshops in table: {count_result[0] if count_result else 0}")
        
        # Test 2: Get first 5 workshops with basic info
        logger.info("\n=== Testing Workshop Data Query ===")
        sample_query = """
        SELECT workshop_id, title, description, created_date 
        FROM admin.livelabs_workshops2 
        WHERE ROWNUM <= 5
        ORDER BY created_date DESC
        """
        sample_results = db_manager.execute_query(sample_query, fetch_all=True)
        
        if sample_results:
            logger.info(f"Found {len(sample_results)} sample workshops:")
            for i, row in enumerate(sample_results, 1):
                workshop_id, title, description, created_date = row
                logger.info(f"  {i}. Workshop ID: {workshop_id}")
                logger.info(f"     Title: {title[:100]}{'...' if title and len(title) > 100 else ''}")
                logger.info(f"     Description: {description[:150]}{'...' if description and len(description) > 150 else ''}")
                logger.info(f"     Created: {created_date}")
                logger.info("")
        else:
            logger.info("No workshops found in the table")
        
        # Test 3: Get column information
        logger.info("=== Testing Table Structure ===")
        columns_query = """
        SELECT column_name, data_type, data_length, nullable
        FROM user_tab_columns 
        WHERE table_name = 'LIVELABS_WORKSHOPS2'
        ORDER BY column_id
        """
        columns_result = db_manager.execute_query(columns_query, fetch_all=True)
        
        if columns_result:
            logger.info("Table structure:")
            for column_name, data_type, data_length, nullable in columns_result:
                logger.info(f"  {column_name}: {data_type}({data_length}) {'NULL' if nullable == 'Y' else 'NOT NULL'}")
        else:
            logger.info("Could not retrieve table structure")
            
    except Exception as e:
        logger.error(f"Error during database test: {e}")
        raise
    finally:
        # Clean up
        DatabaseManager.close_pool()
        logger.info("Database connection pool closed")

def test_specific_workshop_query(workshop_id=None):
    """Test querying a specific workshop by ID"""
    
    db_manager = DatabaseManager()
    
    try:
        if workshop_id:
            logger.info(f"=== Testing Specific Workshop Query (ID: {workshop_id}) ===")
            specific_query = """
            SELECT workshop_id, title, description, content, created_date, updated_date
            FROM admin.livelabs_workshops2 
            WHERE workshop_id = :workshop_id
            """
            result = db_manager.execute_query(specific_query, params={'workshop_id': workshop_id}, fetch_one=True)
            
            if result:
                workshop_id, title, description, content, created_date, updated_date = result
                logger.info(f"Workshop ID: {workshop_id}")
                logger.info(f"Title: {title}")
                logger.info(f"Description: {description[:200]}{'...' if description and len(description) > 200 else ''}")
                logger.info(f"Content length: {len(content) if content else 0} characters")
                logger.info(f"Created: {created_date}")
                logger.info(f"Updated: {updated_date}")
            else:
                logger.info(f"No workshop found with ID: {workshop_id}")
        else:
            logger.info("No workshop ID provided for specific query")
            
    except Exception as e:
        logger.error(f"Error during specific workshop query: {e}")
        raise
    finally:
        DatabaseManager.close_pool()

if __name__ == "__main__":
    logger.info("Starting Oracle Database Manager Test")
    
    # Check if environment variables are set
    required_env_vars = ["DB_USER", "DB_PASSWORD", "DB_DSN"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set these variables in your environment or .env file")
        exit(1)
    
    try:
        # Run the main test
        test_livelabs_workshops_query()
        
        # Optionally test a specific workshop (uncomment and modify as needed)
        # test_specific_workshop_query(workshop_id=1070)
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        exit(1)
