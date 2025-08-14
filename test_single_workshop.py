#!/usr/bin/env python3
"""
Test script for single workshop debugging using Selenium with proper waiting
"""

import logging
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_single_workshop():
    """Test scraping a single workshop using Selenium with proper waiting"""
    
    # Test workshop URL
    url = "https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=1070&clear=RR,180&session=11192223075513"
    
    # Setup Chrome options
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = None
    
    try:
        logger.info("Setting up Chrome driver...")
        driver = webdriver.Chrome(options=options)
        
        logger.info(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait until the content is fully loaded (timeout: 15 seconds)
        logger.info("Waiting for content to load...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "t-Body-contentInner"))
        )
        
        logger.info("Content loaded successfully!")
        
        # Get the element's text
        content_div = driver.find_element(By.CLASS_NAME, "t-Body-contentInner")
        
        # Find the "Other Workshops you might like" section to stop before it
        full_text = content_div.text.strip()
        
        # Split the text at "Other Workshops you might like" and take only the first part
        if "Other Workshops you might like" in full_text:
            text = full_text.split("Other Workshops you might like")[0].strip()
            logger.info("Found 'Other Workshops you might like' section - extracted content before it")
        else:
            text = full_text
            logger.info("No 'Other Workshops you might like' section found - using full content")
        
        logger.info(f"Extracted {len(text)} characters of content")
        
        # Save the extracted content
        with open("workshop_1070_content.txt", 'w', encoding='utf-8') as f:
            f.write(text)
        logger.info("Saved content to workshop_1070_content.txt")
        
        # Create JSON output
        result = {
            "url": url,
            "text": text,
            "text_length": len(text),
            "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save JSON result
        with open("workshop_1070_result.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info("Saved JSON result to workshop_1070_result.json")
        
        # Print first 500 characters as preview
        print("\n" + "="*50)
        print("CONTENT PREVIEW:")
        print("="*50)
        print(text[:500] + "..." if len(text) > 500 else text)
        print("="*50)
        
        # Also try to get page title
        try:
            title = driver.title
            logger.info(f"Page title: {title}")
            
            with open("workshop_1070_title.txt", 'w', encoding='utf-8') as f:
                f.write(title)
            logger.info("Saved title to workshop_1070_title.txt")
        except Exception as e:
            logger.debug(f"Could not get title: {e}")
        
        # Save page source for inspection
        try:
            page_source = driver.page_source
            with open("workshop_1070_page_source.html", 'w', encoding='utf-8') as f:
                f.write(page_source)
            logger.info("Saved page source to workshop_1070_page_source.html")
        except Exception as e:
            logger.debug(f"Could not save page source: {e}")
        
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        
        # Save page source even if there's an error
        if driver:
            try:
                page_source = driver.page_source
                with open("workshop_1070_error_page_source.html", 'w', encoding='utf-8') as f:
                    f.write(page_source)
                logger.info("Saved error page source to workshop_1070_error_page_source.html")
            except Exception as save_error:
                logger.error(f"Could not save error page source: {save_error}")
    
    finally:
        if driver:
            driver.quit()
            logger.info("Driver closed")

if __name__ == "__main__":
    test_single_workshop() 