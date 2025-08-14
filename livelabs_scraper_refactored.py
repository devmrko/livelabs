#!/usr/bin/env python3
"""
Oracle LiveLabs Workshop Scraper - Refactored Version
Uses common utilities for better maintainability and reusability
"""

import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

# Import common utilities
from utils.selenium_utils import SeleniumDriver
from utils.workshop_parser import WorkshopParser
from utils.mongo_utils import MongoManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LiveLabsScraper:
    """Main LiveLabs scraper using common utilities"""
    
    def __init__(self, headless=True, save_to_mongo=False):
        self.base_url = "https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/livelabs-workshop-cards"
        self.driver_manager = SeleniumDriver(headless=headless)
        self.workshop_parser = WorkshopParser()
        self.mongo_manager = MongoManager() if save_to_mongo else None
        self.all_workshops = []
        
    def has_next_page(self):
        """Check if there's a next page available"""
        try:
            next_button = self.driver_manager.driver.find_element(By.CSS_SELECTOR, "span.a-Icon.icon-next")
            parent_element = next_button.find_element(By.XPATH, "./..")
            parent_class = parent_element.get_attribute("class") or ""
            
            if "is-disabled" in parent_class or "disabled" in parent_class:
                logger.info("Next button is disabled - reached last page")
                return False
            else:
                logger.info("Next button is available")
                return True
                
        except NoSuchElementException:
            logger.info("Next button not found - reached last page")
            return False
        except Exception as e:
            logger.error(f"Error checking next page: {e}")
            return False
    
    def go_to_next_page(self):
        """Navigate to the next page"""
        try:
            next_button = self.driver_manager.driver.find_element(By.CSS_SELECTOR, "span.a-Icon.icon-next")
            parent_element = next_button.find_element(By.XPATH, "./..")
            
            # Scroll to the button
            self.driver_manager.driver.execute_script("arguments[0].scrollIntoView(true);", parent_element)
            time.sleep(2)
            
            # Try different click methods
            try:
                parent_element.click()
            except Exception:
                self.driver_manager.driver.execute_script("arguments[0].click();", parent_element)
            
            time.sleep(5)
            logger.info("Successfully navigated to next page")
            return True
            
        except NoSuchElementException:
            logger.error("Next button not found")
            return False
        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
            return False
    
    def scrape_all_pages(self, max_pages=100):
        """Scrape all workshops from all pages"""
        try:
            self.driver_manager.setup_driver()
            logger.info("Starting LiveLabs workshop scraping...")
            
            self.driver_manager.driver.get(self.base_url)
            time.sleep(5)
            
            page_number = 1
            
            while page_number <= max_pages:
                logger.info(f"Scraping page {page_number}...")
                
                # Wait for page to load
                time.sleep(5)
                html_content = self.driver_manager.driver.page_source
                
                # Extract workshops from current page
                page_workshops = self.workshop_parser.extract_workshops_beautifulsoup(html_content)
                
                if page_workshops:
                    # Add page number to each workshop
                    for workshop in page_workshops:
                        workshop['page_number'] = page_number
                    
                    self.all_workshops.extend(page_workshops)
                    logger.info(f"Found {len(page_workshops)} workshops on page {page_number}")
                else:
                    logger.warning(f"No workshops found on page {page_number}")
                
                # Check if there's a next page
                if self.has_next_page():
                    if not self.go_to_next_page():
                        logger.error("Failed to navigate to next page")
                        break
                    page_number += 1
                else:
                    logger.info("Reached the last page")
                    break
            
            logger.info(f"Scraping completed. Total workshops found: {len(self.all_workshops)} across {page_number} pages")
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        finally:
            self.driver_manager.quit()
    
    def save_results(self, filename="livelabs_workshops.json"):
        """Save results to JSON and optionally MongoDB"""
        # Save to JSON
        self.workshop_parser.save_workshops_to_json(
            self.all_workshops, 
            filename, 
            total_pages=len(set(w.get('page_number', 1) for w in self.all_workshops))
        )
        
        # Save to MongoDB if enabled
        if self.mongo_manager:
            self.mongo_manager.insert_workshops(self.all_workshops)
            self.mongo_manager.close()
    
    def print_summary(self):
        """Print summary of results"""
        self.workshop_parser.print_workshop_summary(self.all_workshops, "LIVELABS WORKSHOP SCRAPING SUMMARY")

def main():
    """Main function"""
    # Create scraper (set save_to_mongo=True to also save to MongoDB)
    scraper = LiveLabsScraper(headless=True, save_to_mongo=False)
    
    # Scrape all pages
    scraper.scrape_all_pages()
    
    # Save results
    scraper.save_results()
    
    # Print summary
    scraper.print_summary()

if __name__ == "__main__":
    main() 