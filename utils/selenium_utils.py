#!/usr/bin/env python3
"""
Selenium utilities for web scraping with anti-detection measures
"""

import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class SeleniumDriver:
    """Enhanced Selenium driver with anti-detection measures"""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures"""
        try:
            options = Options()
            
            # Anti-detection measures
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Random user agent
            user_agents = [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            ]
            options.add_argument(f"--user-agent={random.choice(user_agents)}")
            
            # Additional stealth options
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")  # Faster loading
            options.add_argument("--disable-javascript")  # Only if not needed
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            
            # Window size
            options.add_argument("--window-size=1920,1080")
            
            if self.headless:
                options.add_argument("--headless")
            
            # Setup service with permission handling
            try:
                driver_path = ChromeDriverManager().install()
                # Ensure we're using the actual chromedriver executable, not a notice file
                if 'THIRD_PARTY_NOTICES' in driver_path:
                    # Find the actual chromedriver in the same directory
                    import os
                    driver_dir = os.path.dirname(driver_path)
                    for file in os.listdir(driver_dir):
                        if file.startswith('chromedriver') and not file.endswith('.txt'):
                            driver_path = os.path.join(driver_dir, file)
                            break
                
                # Fix permissions on chromedriver
                import os
                import stat
                try:
                    os.chmod(driver_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                    logger.info(f"Fixed permissions for ChromeDriver at: {driver_path}")
                except Exception as perm_error:
                    logger.warning(f"Could not fix permissions: {perm_error}")
                
                service = Service(driver_path)
                logger.info(f"Using ChromeDriver at: {driver_path}")
            except Exception as e:
                logger.warning(f"ChromeDriverManager failed: {e}")
                # Try to use system ChromeDriver
                try:
                    service = Service()  # Use system ChromeDriver
                    logger.info("Using system ChromeDriver")
                except Exception as e2:
                    logger.error(f"System ChromeDriver also failed: {e2}")
                    # Try to install chromedriver manually
                    try:
                        import subprocess
                        import sys
                        subprocess.run([sys.executable, "-m", "pip", "install", "chromedriver-autoinstaller"], check=True)
                        import chromedriver_autoinstaller
                        chromedriver_autoinstaller.install()
                        service = Service()
                        logger.info("Installed and using chromedriver-autoinstaller")
                    except Exception as e3:
                        logger.error(f"All ChromeDriver setup methods failed: {e3}")
                        return False
            
            # Create driver
            try:
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                logger.warning(f"Chrome driver creation failed: {e}")
                # Try without service (let Selenium find Chrome automatically)
                try:
                    self.driver = webdriver.Chrome(options=options)
                    logger.info("Created Chrome driver without explicit service")
                except Exception as e2:
                    logger.error(f"All Chrome driver creation methods failed: {e2}")
                    return False
            
            # Execute stealth script
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set random viewport
            width = random.randint(1200, 1920)
            height = random.randint(800, 1080)
            self.driver.set_window_size(width, height)
            
            logger.info("Chrome driver setup complete with anti-detection measures")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return False
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """Add random delay to simulate human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def close_overlay_if_present(self):
        """Close any overlay that might intercept clicks"""
        try:
            self.random_delay(1, 2)
            
            # Common overlay selectors
            overlay_selectors = [
                'div.truste_overlay',
                'div[id^="pop-div"]',
                '.modal-overlay',
                '.cookie-banner',
                '.privacy-notice',
                'button[aria-label="Close"]',
                'button.close',
                '.close-button'
            ]
            
            for selector in overlay_selectors:
                try:
                    overlays = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if overlays:
                        for overlay in overlays:
                            if overlay.is_displayed():
                                # Try to find close button within overlay
                                close_buttons = overlay.find_elements(By.CSS_SELECTOR, 'button, .close, [aria-label*="close"], [aria-label*="Close"]')
                                if close_buttons:
                                    close_buttons[0].click()
                                    logger.info(f"Closed overlay with selector: {selector}")
                                    self.random_delay(1, 2)
                                    break
                                else:
                                    # Remove overlay with JavaScript
                                    self.driver.execute_script("arguments[0].remove();", overlay)
                                    logger.info(f"Removed overlay with selector: {selector}")
                                    self.random_delay(1, 2)
                                    break
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.warning(f"No overlay to close or error closing overlay: {e}")
    
    def wait_and_click(self, by, value, description="element", timeout=30):
        """Wait for element and click with retry mechanism"""
        try:
            # Wait for element to be present and clickable
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            self.random_delay(0.5, 1)
            
            # Try multiple click methods
            click_methods = [
                lambda: element.click(),
                lambda: self.driver.execute_script("arguments[0].click();", element),
                lambda: ActionChains(self.driver).move_to_element(element).click().perform()
            ]
            
            for i, click_method in enumerate(click_methods):
                try:
                    click_method()
                    logger.info(f"Successfully clicked {description} using method {i+1}")
                    self.random_delay(1, 2)
                    return True
                except ElementClickInterceptedException:
                    logger.warning(f"Click intercepted for {description}, trying method {i+2}")
                    self.close_overlay_if_present()
                    continue
                except Exception as e:
                    logger.warning(f"Click method {i+1} failed for {description}: {e}")
                    continue
            
            logger.error(f"All click methods failed for {description}")
            return False
            
        except TimeoutException:
            logger.debug(f"Timeout waiting for {description} - element not found")
            return False
        except Exception as e:
            logger.error(f"Error clicking {description}: {e}")
            return False
    
    def try_click_btn_toggle(self):
        """Try to click btn_toggle button if present"""
        try:
            btn_toggle = self.driver.find_element(By.ID, "btn_toggle")
            if btn_toggle.is_displayed():
                btn_toggle.click()
                logger.info("Clicked btn_toggle button")
                self.random_delay(1, 2)
                return True
        except NoSuchElementException:
            pass
        except Exception as e:
            logger.warning(f"Error clicking btn_toggle: {e}")
        return False
    
    def extract_text_from_element(self, selector, timeout=10):
        """Extract text from element with wait"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element.text
        except TimeoutException:
            logger.warning(f"Timeout waiting for element: {selector}")
            return ""
        except Exception as e:
            logger.error(f"Error extracting text from {selector}: {e}")
            return ""
    
    def search_all_frames_for_text(self, selector):
        """Search for text in main page and all iframes"""
        text_content = ""
        
        # Try main page first
        try:
            self.try_click_btn_toggle()
            text_content = self.driver.execute_script(
                f"return document.querySelector('{selector}') ? document.querySelector('{selector}').innerText : ''"
            )
            if text_content:
                logger.info(f"Found text in main page with selector: {selector}")
                return text_content
        except Exception as e:
            logger.warning(f"Error searching main page: {e}")
        
        # Search all iframes
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            logger.info(f"Searching {len(iframes)} iframes for text")
            
            for idx, iframe in enumerate(iframes):
                try:
                    self.driver.switch_to.frame(iframe)
                    self.try_click_btn_toggle()
                    
                    text_content = self.driver.execute_script(
                        f"return document.querySelector('{selector}') ? document.querySelector('{selector}').innerText : ''"
                    )
                    
                    self.driver.switch_to.default_content()
                    
                    if text_content:
                        logger.info(f"Found text in iframe {idx+1} with selector: {selector}")
                        return text_content
                        
                except Exception as e:
                    logger.warning(f"Error searching iframe {idx+1}: {e}")
                    self.driver.switch_to.default_content()
                    continue
        except Exception as e:
            logger.error(f"Error searching iframes: {e}")
        
        return text_content
    
    def quit(self):
        """Quit the driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Driver quit successfully")
            except Exception as e:
                logger.warning(f"Error quitting driver: {e}") 