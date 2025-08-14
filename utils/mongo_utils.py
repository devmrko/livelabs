#!/usr/bin/env python3
"""
Common MongoDB utilities
"""

import os
import logging
from pymongo import MongoClient
from dotenv import load_dotenv
from urllib.parse import quote_plus
from datetime import datetime

logger = logging.getLogger(__name__)

class MongoManager:
    """Reusable MongoDB connection and operations"""
    
    def __init__(self, db_name=None, collection_name="livelabs_workshops"):
        load_dotenv()
        self.mongo_user = os.getenv("MONGO_USER")
        self.mongo_password = os.getenv("MONGO_PASSWORD")
        self.mongo_host = os.getenv("MONGO_HOST")
        self.mongo_port = os.getenv("MONGO_PORT")
        self.db_name = db_name or self.mongo_user
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        
    def build_connection_string(self):
        """Build MongoDB connection string with proper escaping"""
        if not self.mongo_user or not self.mongo_password:
            raise ValueError("MONGO_USER and MONGO_PASSWORD must be set in .env file")
        
        user_escaped = quote_plus(self.mongo_user)
        password_escaped = quote_plus(self.mongo_password)
        
        return (
            f"mongodb://{user_escaped}:{password_escaped}@{self.mongo_host}:{self.mongo_port}/"
            f"{user_escaped}?authMechanism=PLAIN&authSource=$external&ssl=true&retryWrites=false&loadBalanced=true"
        )
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            uri = self.build_connection_string()
            self.client = MongoClient(uri)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            logger.info(f"Connected to MongoDB: {self.db_name}.{self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def insert_workshops(self, workshops):
        """Insert workshops into MongoDB collection"""
        if self.collection is None:
            if not self.connect():
                return False
        
        try:
            if workshops:
                result = self.collection.insert_many(workshops)
                logger.info(f"Inserted {len(result.inserted_ids)} workshops into MongoDB")
                return True
            else:
                logger.warning("No workshops to insert")
                return False
        except Exception as e:
            logger.error(f"Error inserting workshops: {e}")
            return False
    
    def insert_single_workshop(self, workshop):
        """Insert a single workshop into MongoDB collection - commits per transaction"""
        if self.collection is None:
            if not self.connect():
                return False
        
        try:
            if workshop:
                result = self.collection.insert_one(workshop)
                logger.info(f"Inserted single workshop with ID: {result.inserted_id}")
                return True
            else:
                logger.warning("No workshop to insert")
                return False
        except Exception as e:
            logger.error(f"Error inserting single workshop: {e}")
            return False
    
    def insert_workshop_text(self, workshop_id, text_content, url):
        """Insert workshop text content"""
        if self.collection is None:
            if not self.connect():
                return False
        
        try:
            document = {
                "workshop_id": workshop_id,
                "text_content": text_content,
                "url": url,
                "inserted_at": datetime.now()
            }
            result = self.collection.insert_one(document)
            logger.info(f"Inserted workshop text for ID {workshop_id}")
            return True
        except Exception as e:
            logger.error(f"Error inserting workshop text: {e}")
            return False
    
    def find_workshops(self, filter_dict=None, limit=None):
        """Find workshops in collection"""
        if self.collection is None:
            if not self.connect():
                return []
        
        try:
            cursor = self.collection.find(filter_dict or {})
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error finding workshops: {e}")
            return []
    
    def count_workshops(self):
        """Count total workshops in collection"""
        if self.collection is None:
            if not self.connect():
                return 0
        
        try:
            return self.collection.count_documents({})
        except Exception as e:
            logger.error(f"Error counting workshops: {e}")
            return 0
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed") 