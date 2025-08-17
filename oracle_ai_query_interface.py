#!/usr/bin/env python3
"""
Oracle AI Query Interface
Interactive interface for Oracle SELECT AI natural language database queries
Provides command-line and programmatic access to AI-powered database querying
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

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
except ImportError:
    logger.info("python-dotenv not available, using system environment variables")

class OracleAIQueryInterface:
    """Interactive interface for Oracle SELECT AI natural language queries"""
    
    def __init__(self):
        self.oracle_manager = None
        
    def initialize_connection(self):
        """Initialize Oracle connection"""
        logger.info("=== Initializing Oracle Connection ===")
        
        try:
            self.oracle_manager = DatabaseManager()
            # Test connection
            test_result = self.oracle_manager.execute_query("SELECT 1 FROM DUAL", fetch_one=True)
            if test_result:
                logger.info("✅ Oracle connection established")
                return True
            else:
                raise Exception("Oracle connection test failed")
        except Exception as e:
            logger.error(f"❌ Oracle connection failed: {e}")
            return False
    
    def set_ai_profile(self, profile_name: str = "DISCOVERYDAY_AI_PROFILE"):
        """Set the AI profile for SELECT AI"""
        try:
            logger.info(f"Setting AI profile: {profile_name}")
            
            # Set the AI profile
            profile_query = f"""
            BEGIN
                DBMS_CLOUD_AI.SET_PROFILE('{profile_name}');
            END;
            """
            
            result = self.oracle_manager.execute_query(profile_query, is_ddl=True)
            logger.info("✅ AI profile set successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting AI profile: {e}")
            return False
    
    def execute_select_ai_query(self, natural_language_query: str):
        """Execute a SELECT AI query using natural language"""
        try:
            logger.info(f"=== Executing SELECT AI Query ===")
            logger.info(f"Natural Language Query: {natural_language_query}")
            
            # Format the SELECT AI query
            select_ai_query = f"""
            SELECT AI {natural_language_query}
            """
            
            logger.info("Executing query...")
            results = self.oracle_manager.execute_query(select_ai_query, fetch_all=True)
            
            if results:
                logger.info(f"✅ Query executed successfully. Found {len(results)} results:")
                logger.info("=" * 80)
                
                # Display results
                for i, row in enumerate(results, 1):
                    logger.info(f"Row {i}: {row}")
                
                logger.info("=" * 80)
                return results
            else:
                logger.info("✅ Query executed successfully. No results returned.")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error executing SELECT AI query: {e}")
            return None
    
    def interactive_select_ai(self):
        """Interactive SELECT AI interface"""
        logger.info("=== Oracle AI Query Interactive Interface ===")
        
        # Set AI profile first
        if not self.set_ai_profile():
            logger.error("Failed to set AI profile. Exiting.")
            return
        
        try:
            while True:
                print("\n" + "="*60)
                print("Oracle SELECT AI Query Interface")
                print("="*60)
                print("Enter your natural language query (or 'quit' to exit):")
                print("Examples:")
                print("- what kinds of skill John Smith have, and how good are those")
                print("- show me all workshops about database security")
                print("- find workshops with more than 100000 views")
                print("- what are the most popular workshop categories")
                
                # Get user input
                query = input("\n> ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if not query:
                    print("Please enter a query.")
                    continue
                
                print(f"\nExecuting: SELECT AI {query}")
                
                # Execute the SELECT AI query
                results = self.execute_select_ai_query(query)
                
                if results is not None:
                    print(f"\nQuery completed successfully!")
                else:
                    print(f"\nQuery failed. Check logs for details.")
        
        except KeyboardInterrupt:
            print("\n\nInterface interrupted. Goodbye!")
        except Exception as e:
            logger.error(f"❌ Interactive interface error: {e}")
    
    def run_example_queries(self):
        """Run some example SELECT AI queries"""
        logger.info("=== Running Example AI Queries ===")
        
        # Set AI profile first
        if not self.set_ai_profile():
            logger.error("Failed to set AI profile. Exiting.")
            return
        
        # Example queries
        example_queries = [
            "what kinds of skill John Smith have, and how good are those",
            "show me all workshops about database security",
            "find workshops with more than 100000 views",
            "what are the most popular workshop categories",
            "show me beginner level workshops about APEX",
            "find workshops created by Oracle team",
            "what workshops are available for machine learning"
        ]
        
        for i, query in enumerate(example_queries, 1):
            logger.info(f"\n--- Example {i} ---")
            results = self.execute_select_ai_query(query)
            
            if results is None:
                logger.error(f"Example {i} failed")
            
            logger.info("\n" + "-"*60)
    
    def cleanup(self):
        """Clean up connections"""
        logger.info("=== Cleaning Up Connections ===")
        
        if self.oracle_manager:
            DatabaseManager.close_pool()
            logger.info("Oracle connection pool closed")

def main():
    """Main function to run Oracle AI query interface"""
    logger.info("Starting Oracle AI Query Interface")
    
    # Check environment variables
    required_env_vars = ["DB_USER", "DB_PASSWORD", "DB_DSN"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        exit(1)
    
    # Create AI query interface
    ai_interface = OracleAIQueryInterface()
    
    # Initialize connection
    if not ai_interface.initialize_connection():
        logger.error("❌ Failed to initialize connection")
        exit(1)
    
    try:
        # Choose mode
        print("\nOracle AI Query Interface")
        print("1. Run example queries")
        print("2. Interactive mode")
        print("3. Custom query")
        
        choice = input("\nChoose option (1-3): ").strip()
        
        if choice == "1":
            ai_interface.run_example_queries()
        elif choice == "2":
            ai_interface.interactive_select_ai()
        elif choice == "3":
            # Set AI profile first
            if not ai_interface.set_ai_profile():
                logger.error("Failed to set AI profile. Exiting.")
                return
            
            # Get custom query
            custom_query = input("Enter your SELECT AI query: ").strip()
            if custom_query:
                ai_interface.execute_select_ai_query(custom_query)
            else:
                print("No query provided.")
        else:
            print("Invalid choice. Exiting.")
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        exit(1)
    finally:
        ai_interface.cleanup()

if __name__ == "__main__":
    main()
