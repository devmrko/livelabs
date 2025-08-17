#!/usr/bin/env python3
"""
Test script for Batch Embedding Processor
Tests the complete pipeline with a small sample
"""

import logging
from batch_embedding_update import BatchEmbeddingProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_batch_processor():
    """Test the batch embedding processor with a small sample"""
    logger.info("=== Testing Batch Embedding Processor ===")
    
    # Create processor
    processor = BatchEmbeddingProcessor()
    
    # Test with a very small sample
    success = processor.process_workshops(
        limit=3  # Process only 3 workshops for testing
    )
    
    if success:
        summary = processor.get_summary()
        logger.info("=== Test Results ===")
        logger.info(f"Total processed: {summary['processed_count']}")
        logger.info(f"Successfully updated: {summary['updated_count']}")
        logger.info(f"Errors: {summary['error_count']}")
        logger.info(f"Success rate: {summary['success_rate']:.2f}%")
        
        if summary['success_rate'] >= 80:
            logger.info("✅ Test passed! Batch processor is working correctly.")
            return True
        else:
            logger.warning("⚠️  Test completed but success rate is low.")
            return False
    else:
        logger.error("❌ Test failed! Batch processor encountered errors.")
        return False

def test_connections_only():
    """Test only the connection initialization"""
    logger.info("=== Testing Connections Only ===")
    
    processor = BatchEmbeddingProcessor()
    
    try:
        success = processor.initialize_connections()
        if success:
            logger.info("✅ All connections established successfully")
            processor.cleanup()
            return True
        else:
            logger.error("❌ Connection initialization failed")
            return False
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting Batch Embedding Processor Test")
    
    # First test connections
    if test_connections_only():
        logger.info("Connection test passed, proceeding with full test...")
        
        # Then test full pipeline
        if test_batch_processor():
            logger.info("🎉 All tests passed!")
        else:
            logger.error("❌ Full pipeline test failed")
            exit(1)
    else:
        logger.error("❌ Connection test failed, skipping full test")
        exit(1)
