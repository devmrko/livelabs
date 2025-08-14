#!/usr/bin/env python3
"""
Interactive Vector Search for LiveLabs Workshops
Allows user to input custom search queries
"""

import logging
from vector_search import VectorSearchEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def interactive_search():
    """Interactive search function"""
    logger.info("=== Interactive Vector Search ===")
    
    # Create search engine
    search_engine = VectorSearchEngine()
    
    # Initialize connections
    if not search_engine.initialize_connections():
        logger.error("❌ Failed to initialize connections")
        return
    
    try:
        while True:
            print("\n" + "="*60)
            print("LiveLabs Workshop Vector Search")
            print("="*60)
            print("Enter your search query (or 'quit' to exit):")
            
            # Get user input
            query = input("> ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not query:
                print("Please enter a search query.")
                continue
            
            print(f"\nSearching for: '{query}'")
            
            # Perform search
            results = search_engine.search_similar_workshops(query, top_k=10)
            
            if results:
                print(f"\nFound {len(results)} similar workshops:")
                print("-" * 60)
                
                for i, result in enumerate(results, 1):
                    similarity = result['similarity']
                    
                    print(f"{i}. Similarity: {similarity:.4f}")
                    print(f"   Title: {result.get('title', 'N/A')}")
                    print(f"   ID: {result.get('id', 'N/A')}")
                    print(f"   Author: {result.get('author', 'N/A')}")
                    print(f"   Difficulty: {result.get('difficulty', 'N/A')}")
                    print(f"   Category: {result.get('category', 'N/A')}")
                    print(f"   Duration: {result.get('duration_estimate', 'N/A')}")
                    
                    description = result.get('description', '')
                    if description:
                        desc_preview = description[:100] + "..." if len(description) > 100 else description
                        print(f"   Description: {desc_preview}")
                    
                    text_content = result.get('text_content', '')
                    if text_content:
                        content_preview = text_content[:150] + "..." if len(text_content) > 150 else text_content
                        print(f"   Content: {content_preview}")
                    
                    print()
            else:
                print("No similar workshops found.")
    
    except KeyboardInterrupt:
        print("\n\nSearch interrupted. Goodbye!")
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
    finally:
        search_engine.cleanup()

if __name__ == "__main__":
    interactive_search()
