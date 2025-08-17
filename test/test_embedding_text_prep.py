#!/usr/bin/env python3
"""
Test script for embedding text preparation
Tests how the complete workshop document is converted to embedding text
"""

import logging
from batch_embedding_update import BatchEmbeddingProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_text_preparation():
    """Test the text preparation function with sample workshop data"""
    logger.info("=== Testing Embedding Text Preparation ===")
    
    # Sample workshop data (similar to what would come from MongoDB)
    sample_workshop = {
        "_id": "test_123",  # MongoDB _id field (maps to mongo_id in Oracle)
        "id": "test_123",
        "title": "Sample Workshop Title",
        "description": "This is a sample workshop description for testing purposes.",
        "duration": "2 hours",
        "views": 1500,
        "url": "/sample/workshop/123",
        "page_number": 1,
        "keywords": ["Oracle", "Cloud", "Database", "AI"],
        "author": "Oracle Team",
        "difficulty": "INTERMEDIATE",
        "category": "Database",
        "text_content": "This is the main content of the workshop. It contains detailed information about the workshop topics and procedures.",
        "created_at": "2025-01-15",
        "language": "en",
        "source": "Oracle LiveLabs"
    }
    
    # Create processor instance
    processor = BatchEmbeddingProcessor()
    
    # Test text preparation
    embedding_text = processor.prepare_text_for_embedding(sample_workshop)
    
    logger.info("=== Sample Workshop Data ===")
    for key, value in sample_workshop.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n=== Generated Embedding Text (JSON) ===")
    logger.info(f"Length: {len(embedding_text)} characters")
    logger.info(f"Text: {embedding_text}")
    
    # Check if it's valid JSON
    try:
        import json
        parsed_json = json.loads(embedding_text)
        logger.info("✅ Generated text is valid JSON")
        
        # Check if all original fields are preserved
        original_keys = set(sample_workshop.keys())
        json_keys = set(parsed_json.keys())
        
        if original_keys == json_keys:
            logger.info("✅ All original fields preserved in JSON")
        else:
            missing_keys = original_keys - json_keys
            extra_keys = json_keys - original_keys
            logger.warning(f"⚠️  Field mismatch - Missing: {missing_keys}, Extra: {extra_keys}")
        
        # Check length
        if len(embedding_text) > 6000:
            logger.warning(f"⚠️  Text is too long ({len(embedding_text)} chars), may be truncated")
        else:
            logger.info(f"✅ Text length is appropriate ({len(embedding_text)} chars)")
        
        return original_keys == json_keys and len(embedding_text) <= 6000
        
    except json.JSONDecodeError:
        logger.warning("⚠️  Generated text is not valid JSON")
        return False

if __name__ == "__main__":
    logger.info("Starting Embedding Text Preparation Test")
    
    if test_text_preparation():
        logger.info("🎉 Text preparation test passed!")
    else:
        logger.error("❌ Text preparation test failed")
        exit(1)
