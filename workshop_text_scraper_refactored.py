#!/usr/bin/env python3
"""
Oracle LiveLabs Workshop Text Scraper - Refactored Version
Scrapes text content for all workshops from livelabs_workshops.json
Saves results incrementally for progress monitoring
"""

import logging
import json
import time
import os
import random
from datetime import datetime
from typing import List, Dict, Any

# Import common utilities
from utils.selenium_utils import SeleniumDriver
from utils.mongo_utils import MongoManager
from utils.workshop_parser import WorkshopParser
from selenium.webdriver.common.by import By

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkshopTextScraper:
    """Scraper for individual workshop text content"""
    
    def __init__(self, headless=True, save_to_mongo=False):
        self.base_url = "https://apexapps.oracle.com"
        self.driver_manager = SeleniumDriver(headless=headless)
        self.mongo_manager = MongoManager(collection_name="workshop_texts") if save_to_mongo else None
        self.workshops_data = []
        self.progress_file = "workshop_texts_progress.json"
        
    def load_workshops(self, json_file="livelabs_workshops.json"):
        """Load workshops from JSON file"""
        try:
            workshops = WorkshopParser.load_workshops_from_json(json_file)
            logger.info(f"Loaded {len(workshops)} workshops from {json_file}")
            return workshops
        except Exception as e:
            logger.error(f"Error loading workshops: {e}")
            return []
    
    def load_progress(self):
        """Load existing progress from file"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.workshops_data = data.get('workshops', [])
                    logger.info(f"Loaded {len(self.workshops_data)} existing results from progress file")
                    
                    # Get successfully processed workshop IDs
                    successful_ids = set()
                    for workshop in self.workshops_data:
                        if workshop.get('success', False):
                            successful_ids.add(workshop.get('workshop_id'))
                    
                    logger.info(f"Found {len(successful_ids)} successfully scraped workshops")
                    return successful_ids
            except Exception as e:
                logger.warning(f"Error loading progress file: {e}")
        return set()
    
    def save_progress(self, successful_ids):
        """Save current progress to file"""
        try:
            successful_workshops = [w for w in self.workshops_data if w['success']]
            failed_workshops = [w for w in self.workshops_data if not w['success']]
            
            data = {
                "total_workshops": len(self.workshops_data),
                "successful_scrapes": len(successful_workshops),
                "failed_scrapes": len(failed_workshops),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "successful_ids": list(successful_ids),
                "workshops": self.workshops_data
            }
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Progress saved: {data['successful_scrapes']} successful, {data['failed_scrapes']} failed")
            
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def scrape_workshop_text(self, workshop: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape text content from a specific workshop"""
        # Check if workshop is None or invalid
        if not workshop or not isinstance(workshop, dict):
            logger.error(f"Invalid workshop data: {workshop}")
            return {
                'workshop_id': 'unknown',
                'title': 'Invalid Workshop Data',
                'url': '',
                'text_content': '',
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'success': False,
                'error': 'Invalid workshop data'
            }
        
        workshop_id = workshop.get('id', 'unknown')
        workshop_url = workshop.get('url', '')
        workshop_title = workshop.get('title', 'Unknown')
        
        logger.info(f"Scraping workshop {workshop_id}: {workshop_title}")
        
        result = {
            'workshop_id': workshop_id,
            'title': workshop_title,
            'url': workshop_url,
            'text_content': '',
            'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'success': False,
            'error': None
        }
        
        if not workshop_url:
            result['error'] = "No URL provided"
            return result
        
        try:
            # Check if driver is available
            if not self.driver_manager.driver:
                result['error'] = "Chrome driver not available"
                return result
            
            # Navigate to workshop page
            full_url = self.base_url + workshop_url
            self.driver_manager.driver.get(full_url)
            self.driver_manager.close_overlay_if_present()
            
            # Try to click start button first
            start_button_clicked = self.driver_manager.wait_and_click(By.ID, "start-button-id", description="start button", timeout=10)
            
            if start_button_clicked:
                time.sleep(2)
                
                # Try to click runOnYourTenancy button
                tenancy_button_clicked = self.driver_manager.wait_and_click(By.ID, "runOnYourTenancy", description="runOnYourTenancy button", timeout=10)
                
                if tenancy_button_clicked:
                    time.sleep(3)
                    logger.info("Successfully clicked both start and tenancy buttons")
                else:
                    logger.info("Start button clicked but no runOnYourTenancy button found - extracting from current page")
            else:
                logger.info("No start button found - extracting from current page")
            
            # Extract text content from current page
            logger.info("Extracting text content from current page...")
            
            # First try the interactive approach (hol-Content or contentBox)
            text_content = self.driver_manager.search_all_frames_for_text(".hol-Content")
            
            if not text_content:
                # Try alternative selector
                text_content = self.driver_manager.search_all_frames_for_text("#contentBox")
            
            # If interactive approach didn't work, try the t-Body-contentInner approach
            if not text_content:
                logger.info("Interactive content not found, trying t-Body-contentInner approach...")
                try:
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    
                    # Wait for t-Body-contentInner to load
                    WebDriverWait(self.driver_manager.driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "t-Body-contentInner"))
                    )
                    
                    # Get the element's text
                    content_div = self.driver_manager.driver.find_element(By.CLASS_NAME, "t-Body-contentInner")
                    full_text = content_div.text.strip()
                    
                    # Split the text at "Other Workshops you might like" and take only the first part
                    if "Other Workshops you might like" in full_text:
                        text_content = full_text.split("Other Workshops you might like")[0].strip()
                        logger.info("Found 'Other Workshops you might like' section - extracted content before it")
                    else:
                        text_content = full_text
                        logger.info("No 'Other Workshops you might like' section found - using full content")
                        
                except Exception as e:
                    logger.warning(f"t-Body-contentInner approach failed: {e}")
                    text_content = ""
            
            if text_content:
                result['text_content'] = text_content
                result['success'] = True
                logger.info(f"Successfully extracted {len(text_content)} characters for workshop {workshop_id}")
            else:
                result['error'] = "No text content found with any method"
                logger.warning(f"No text content found for workshop {workshop_id} with any extraction method")
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error scraping workshop {workshop_id}: {e}")
        
        return result
    
    def scrape_all_workshops(self, max_workshops=None, delay_between=5):
        """Scrape text content for all workshops with progress tracking and anti-detection"""
        workshops = self.load_workshops()
        
        if not workshops:
            logger.error("No workshops loaded")
            return False
        
        # Load existing progress
        successful_ids = self.load_progress()
        logger.info(f"Already successfully scraped {len(successful_ids)} workshops")
        
        # Filter out already successfully processed workshops and invalid workshops
        remaining_workshops = []
        for w in workshops:
            if w and isinstance(w, dict) and w.get('id') and w.get('id') not in successful_ids:
                remaining_workshops.append(w)
            elif not w or not isinstance(w, dict):
                logger.warning(f"Skipping invalid workshop data: {w}")
        
        logger.info(f"Remaining workshops to process: {len(remaining_workshops)}")
        
        if max_workshops:
            remaining_workshops = remaining_workshops[:max_workshops]
            logger.info(f"Limiting to first {max_workshops} remaining workshops")
        
        if not remaining_workshops:
            logger.info("All workshops already processed!")
            return True
        
        logger.info(f"Starting to scrape {len(remaining_workshops)} workshops...")
        
        try:
            if not self.driver_manager.setup_driver():
                logger.error("Failed to setup Chrome driver")
                return False
            
            for i, workshop in enumerate(remaining_workshops, 1):
                workshop_id = workshop.get('id', 'unknown')
                if not workshop_id or workshop_id == 'unknown':
                    logger.warning(f"Skipping workshop with invalid ID: {workshop}")
                    continue
                    
                logger.info(f"Progress: {i}/{len(remaining_workshops)} (Workshop {workshop_id})")
                
                # Add longer random delay between workshops to avoid detection
                if i > 1:
                    random_delay = random.uniform(delay_between, delay_between + 10)
                    logger.info(f"Waiting {random_delay:.1f} seconds before next workshop...")
                    time.sleep(random_delay)
                
                # Scrape workshop text
                result = self.scrape_workshop_text(workshop)
                self.workshops_data.append(result)
                
                # Only add to successful_ids if scraping was successful
                if result['success']:
                    successful_ids.add(workshop_id)
                
                # Save progress after each workshop
                self.save_progress(successful_ids)
                
                # If we get blocked, wait longer
                if not result['success'] and 'blocked' in result.get('error', '').lower():
                    logger.warning("Possible blocking detected, waiting 30 seconds...")
                    time.sleep(30)
            
            logger.info(f"Completed scraping {len(remaining_workshops)} workshops")
            return True
            
        except Exception as e:
            logger.error(f"Error during batch scraping: {e}")
            # Save progress even if there's an error
            self.save_progress(successful_ids)
            return False
        finally:
            self.driver_manager.quit()
    
    def save_to_json(self, filename="all_workshop_texts.json"):
        """Save all workshop text content to final JSON file"""
        try:
            data = {
                "total_workshops": len(self.workshops_data),
                "successful_scrapes": len([w for w in self.workshops_data if w['success']]),
                "failed_scrapes": len([w for w in self.workshops_data if not w['success']]),
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "workshops": self.workshops_data
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Final results saved to {filename}")
            logger.info(f"Summary: {data['successful_scrapes']} successful, {data['failed_scrapes']} failed")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return False
    
    def save_to_mongo(self):
        """Save all workshop text content to MongoDB"""
        if not self.mongo_manager:
            logger.warning("MongoDB not configured")
            return False
        
        successful_inserts = 0
        for workshop_data in self.workshops_data:
            if workshop_data['success']:
                if self.mongo_manager.insert_workshop_text(
                    workshop_data['workshop_id'],
                    workshop_data['text_content'],
                    workshop_data['url']
                ):
                    successful_inserts += 1
        
        logger.info(f"Inserted {successful_inserts} workshop texts to MongoDB")
        return successful_inserts > 0

def main():
    """Main function - scrape all workshops"""
    # Create scraper
    scraper = WorkshopTextScraper(headless=False, save_to_mongo=False)
    
    # Scrape all workshops
    if scraper.scrape_all_workshops():
        # Save final results to JSON
        scraper.save_to_json()
        
        # Optionally save to MongoDB
        # scraper.save_to_mongo()
        
        print(f"Successfully processed {len(scraper.workshops_data)} workshops")
        print(f"Check {scraper.progress_file} for real-time progress")
    else:
        print("Failed to scrape workshops")

if __name__ == "__main__":
    main() 