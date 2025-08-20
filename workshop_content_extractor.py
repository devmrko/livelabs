#!/usr/bin/env python3
"""
한국어 요약:
이 스크립트는 특정 Oracle LiveLabs 워크샵에 접속하여 전체 텍스트 콘텐츠를 추출하는 도구입니다.
워크샵 페이지에서 'Start' 버튼과 'Run on Your Tenancy' 버튼을 자동으로 클릭하고,
iframe을 포함한 다양한 위치에서 .hol-Content 또는 #contentBox 요소를 찾아 텍스트를 추출합니다.
쿠키/개인정보 오버레이를 자동으로 제거하고 버튼 토글 기능도 지원합니다.

Oracle LiveLabs Workshop Text Scraper
Goes to a specific workshop, clicks start and run buttons, extracts all visible text, saves to JSON.
"""

import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://apexapps.oracle.com"
WORKSHOP_PATH = "/pls/apex/r/dbpm/livelabs/view-workshop?wid=648&clear=RR,180&session=112872587055069"
FULL_URL = BASE_URL + WORKSHOP_PATH

class LiveLabsWorkshopTextScraper:
    def __init__(self):
        self.driver = None
        self.text_content = ""

    def setup_driver(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Uncomment for headless
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)

    def close_overlay_if_present(self):
        """Try to close or remove the cookie/privacy overlay if present."""
        try:
            # Wait briefly for overlay to appear
            time.sleep(2)
            # Try to find the overlay by id or class
            overlays = self.driver.find_elements(By.CSS_SELECTOR, 'div.truste_overlay, div[id^="pop-div"]')
            if overlays:
                logger.info("Overlay detected. Attempting to close or remove it...")
                # Try to find a close/accept button inside the overlay
                for overlay in overlays:
                    try:
                        # Try common close/accept selectors
                        close_btn = overlay.find_element(By.CSS_SELECTOR, '.close, .accept, button, .truste_btn_accept')
                        close_btn.click()
                        logger.info("Overlay closed by clicking button.")
                        time.sleep(1)
                        return
                    except Exception:
                        pass
                # If no button, remove overlay with JS
                for overlay in overlays:
                    self.driver.execute_script("arguments[0].parentNode.removeChild(arguments[0]);", overlay)
                logger.info("Overlay removed with JavaScript.")
                time.sleep(1)
        except Exception as e:
            logger.warning(f"No overlay to close or error closing overlay: {e}")

    def try_click_btn_toggle(self):
        """Try to click the #btn_toggle button if present and clickable in the current frame."""
        try:
            from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException
            import selenium.common.exceptions
            import time
            btn = self.driver.find_element(By.ID, "btn_toggle")
            if btn.is_displayed() and btn.is_enabled():
                print("Clicking #btn_toggle button...")
                btn.click()
                time.sleep(1)
                return True
        except (selenium.common.exceptions.NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException):
            print("#btn_toggle button not found or not clickable in this frame.")
        except Exception as e:
            print(f"Error clicking #btn_toggle: {e}")
        return False

    def scrape_workshop(self):
        try:
            self.setup_driver()
            logger.info(f"Navigating to: {FULL_URL}")
            print(f"Navigating to: {FULL_URL}")
            self.driver.get(FULL_URL)
            self.close_overlay_if_present()
            logger.info("Waiting for start button...")
            print("Waiting for start button...")
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "start-button-id"))
            )
            logger.info("Clicking start button...")
            print("Clicking start button...")
            self.driver.find_element(By.ID, "start-button-id").click()
            time.sleep(2)
            logger.info("Waiting for 'Run on Your Tenancy' button...")
            print("Waiting for 'Run on Your Tenancy' button...")
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "runOnYourTenancy"))
            )
            logger.info("Clicking 'Run on Your Tenancy' button...")
            print("Clicking 'Run on Your Tenancy' button...")
            self.driver.find_element(By.ID, "runOnYourTenancy").click()
            time.sleep(3)
            # Try to find .hol-Content in main page first
            print("Trying to find .hol-Content in main page...")
            try:
                self.try_click_btn_toggle()
                self.text_content = self.driver.execute_script(
                    "return document.querySelector('.hol-Content') ? document.querySelector('.hol-Content').innerText : ''"
                )
                if self.text_content.strip():
                    print(f"Found .hol-Content in main page, length: {len(self.text_content)}")
                    logger.info(f"Extracted {len(self.text_content)} characters of text from .hol-Content (main page).")
                    return
            except Exception as e:
                print(f"Not found in main page: {e}")
            # If not found, search all iframes
            print("Searching all iframes for .hol-Content...")
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Found {len(iframes)} iframes.")
            for idx, iframe in enumerate(iframes):
                try:
                    self.driver.switch_to.frame(iframe)
                    print(f"Switched to iframe {idx}.")
                    self.try_click_btn_toggle()
                    text = self.driver.execute_script(
                        "return document.querySelector('.hol-Content') ? document.querySelector('.hol-Content').innerText : ''"
                    )
                    if text.strip():
                        self.text_content = text
                        print(f"Found .hol-Content in iframe {idx}, length: {len(text)}")
                        logger.info(f"Extracted {len(text)} characters of text from .hol-Content (iframe {idx}).")
                        self.driver.switch_to.default_content()
                        return
                    self.driver.switch_to.default_content()
                except Exception as e:
                    print(f"Error in iframe {idx}: {e}")
                    self.driver.switch_to.default_content()
            # If still not found, try div#contentBox in main page
            print("Trying to find div#contentBox in main page...")
            try:
                self.try_click_btn_toggle()
                self.text_content = self.driver.execute_script(
                    "return document.getElementById('contentBox') ? document.getElementById('contentBox').innerText : ''"
                )
                if self.text_content.strip():
                    print(f"Found div#contentBox in main page, length: {len(self.text_content)}")
                    logger.info(f"Extracted {len(self.text_content)} characters of text from div#contentBox (main page).")
                    return
            except Exception as e:
                print(f"Not found div#contentBox in main page: {e}")
            # If still not found, try div#contentBox in all iframes
            print("Searching all iframes for div#contentBox...")
            for idx, iframe in enumerate(iframes):
                try:
                    self.driver.switch_to.frame(iframe)
                    print(f"Switched to iframe {idx} for contentBox.")
                    self.try_click_btn_toggle()
                    text = self.driver.execute_script(
                        "return document.getElementById('contentBox') ? document.getElementById('contentBox').innerText : ''"
                    )
                    if text.strip():
                        self.text_content = text
                        print(f"Found div#contentBox in iframe {idx}, length: {len(text)}")
                        logger.info(f"Extracted {len(text)} characters of text from div#contentBox (iframe {idx}).")
                        self.driver.switch_to.default_content()
                        return
                    self.driver.switch_to.default_content()
                except Exception as e:
                    print(f"Error in iframe {idx} for contentBox: {e}")
                    self.driver.switch_to.default_content()
            print(".hol-Content and div#contentBox not found in any frame.")
            self.text_content = ""
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            print(f"Error during scraping: {e}")
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()

    def save_to_json(self, filename="workshop_text.json"):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "url": FULL_URL,
                    "text": self.text_content
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"Workshop text saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")

def main():
    scraper = LiveLabsWorkshopTextScraper()
    scraper.scrape_workshop()
    scraper.save_to_json()

if __name__ == "__main__":
    main() 