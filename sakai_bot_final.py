# -*- coding: utf-8 -*-
"""
Sakai LMS Announcement Bot
Automatically fetches announcements from Sakai and sends them via Telegram.
"""

import json
import os
import sys
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# --- ENVIRONMENT CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
SAKAI_URL = os.getenv("SAKAI_URL", "https://online.deu.edu.tr/portal").strip()
SAKAI_USERNAME = os.getenv("SAKAI_USERNAME", "").strip()
SAKAI_PASSWORD = os.getenv("SAKAI_PASSWORD", "").strip()
HEADLESS = os.getenv("HEADLESS", "0").lower() in ("1", "true", "yes")

# --- CONSTANTS ---
ANNOUNCEMENTS_FILE = "duyurular.json"
TIMEOUT_PAGE_LOAD = 10
TIMEOUT_ELEMENT = 15
MAX_ANNOUNCEMENTS = 20
TELEGRAM_RATE_LIMIT = 1.0


def validate_configuration() -> bool:
    """Validate required environment variables."""
    required_vars = {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        "SAKAI_USERNAME": SAKAI_USERNAME,
        "SAKAI_PASSWORD": SAKAI_PASSWORD,
    }

    for var_name, var_value in required_vars.items():
        if not var_value:
            logger.error(f"Missing environment variable: {var_name}")
            return False

    return True


def send_telegram_notification(title: str, content: str) -> bool:
    """
    Send notification to Telegram.
    
    Args:
        title: Announcement title
        content: Announcement content
        
    Returns:
        True if successful, False otherwise
    """
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
        message = f"<b>📢 YENİ DUYURU</b>\n\n<b>{title}</b>\n\n{content}"
        
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Telegram notification sent: {title}")
            return True
        else:
            logger.error(f"Telegram error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending notification: {e}")
        return False
def get_webdriver():
    """Initialize WebDriver with appropriate browser."""
    try:
        options = ChromeOptions()
        if HEADLESS:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
        
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        driver = webdriver.Chrome(options=options)
        logger.info("Chrome WebDriver initialized")
        return driver
        
    except Exception as e:
        logger.warning(f"Chrome initialization failed, trying Firefox: {e}")
        try:
            options = FirefoxOptions()
            if HEADLESS:
                options.add_argument("--headless")
            
            driver = webdriver.Firefox(options=options)
            logger.info("Firefox WebDriver initialized")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to initialize any WebDriver: {e}")
            raise


def extract_content_from_link(driver, href: str) -> str:
    """
    Open link in new tab and extract content.
    
    Args:
        driver: Selenium WebDriver instance
        href: URL to fetch content from
        
    Returns:
        Extracted content as string
    """
    content = ""
    original_window = None
    
    try:
        original_window = driver.current_window_handle
        driver.execute_script('window.open(arguments[0]);', href)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(2)
        
        # Try various CSS selectors for content
        selectors = [
            '.announcementBody', '.announcement-content', '.msgBody',
            '#main', '.portletBody', '.sakai-content', '.content', 'article'
        ]
        
        for selector in selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text and len(text) > 20:
                    content = text
                    break
            except Exception:
                continue
        
        # Fallback: get body text but filter out navigation/menu items
        if not content:
            try:
                body = driver.find_element(By.TAG_NAME, 'body')
                full_text = body.text.strip()
                
                # Filter out common menu/navigation items
                filters = [
                    'Takvim', 'Kaynaklar', 'Duyurular', 'Ayarlar',
                    'External Tools', 'Yardım', 'Araç gezgini',
                    'Ders Listesi', 'Bağlantı', 'Sunucu Detayları',
                    'Copyright', 'Apereo', 'Ana Sayfa Destek',
                    'Profil', 'Genel Bakış', 'Ders Oluşturma'
                ]
                
                lines = [
                    line.strip() 
                    for line in full_text.split('\n') 
                    if line.strip() and not any(f in line for f in filters)
                ]
                
                content = '\n'.join(lines)
                
                # Limit length to first 1000 characters
                if len(content) > 1000:
                    content = content[:1000] + "..."
                    
            except Exception:
                pass
                
    except Exception as e:
        logger.warning(f"Error extracting content from {href}: {e}")
    finally:
        try:
            driver.close()
            if original_window:
                driver.switch_to.window(original_window)
        except Exception:
            pass
    
    return content

def fetch_announcements(driver) -> List[Dict[str, str]]:
    """
    Fetch announcements from Sakai LMS.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of announcement dictionaries
    """
    announcements = []
    
    try:
        logger.info("Fetching Sakai portal...")
        driver.get(SAKAI_URL)
        time.sleep(TIMEOUT_PAGE_LOAD)
        
        # Check if already logged in
        logged_in = False
        try:
            driver.find_element(By.ID, 'Mrphs-bullhorn')
            logged_in = True
            logger.info("Already logged in")
        except Exception:
            logged_in = False
        
        # Attempt auto-login if needed
        if not logged_in and SAKAI_USERNAME and SAKAI_PASSWORD:
            logger.info("Attempting automatic login...")
            if attempt_login(driver):
                logger.info("Login successful")
            else:
                logger.warning("Login attempt failed")
        
        # Try to fetch from notifications first
        announcements = fetch_from_notifications(driver)
        if announcements:
            return announcements
        
        # Fallback: search for announcements on page
        logger.info("Searching for announcements on page...")
        announcements = search_page_announcements(driver)
        
        return announcements
        
    except Exception as e:
        logger.error(f"Error fetching announcements: {e}")
        send_telegram_notification("BOT ERROR", f"Failed to fetch announcements:\n{str(e)}")
        return []


def attempt_login(driver) -> bool:
    """
    Attempt to log in to Sakai.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        True if login successful, False otherwise
    """
    try:
        username_selectors = [
            (By.NAME, 'eid'), (By.NAME, 'username'),
            (By.ID, 'eid'), (By.ID, 'username'),
            (By.NAME, 'j_username'), (By.ID, 'j_username')
        ]
        
        password_selectors = [
            (By.NAME, 'pw'), (By.NAME, 'password'),
            (By.ID, 'pw'), (By.ID, 'password'),
            (By.NAME, 'j_password'), (By.ID, 'j_password')
        ]
        
        username_elem = None
        password_elem = None
        
        for selector in username_selectors:
            try:
                username_elem = driver.find_element(*selector)
                break
            except Exception:
                continue
        
        for selector in password_selectors:
            try:
                password_elem = driver.find_element(*selector)
                break
            except Exception:
                continue
        
        if not username_elem or not password_elem:
            # Try in iframes
            for iframe in driver.find_elements(By.TAG_NAME, 'iframe'):
                try:
                    driver.switch_to.frame(iframe)
                    for selector in username_selectors:
                        try:
                            username_elem = driver.find_element(*selector)
                            break
                        except Exception:
                            continue
                    for selector in password_selectors:
                        try:
                            password_elem = driver.find_element(*selector)
                            break
                        except Exception:
                            continue
                    driver.switch_to.default_content()
                    if username_elem and password_elem:
                        break
                except Exception:
                    try:
                        driver.switch_to.default_content()
                    except Exception:
                        pass
        
        if not username_elem or not password_elem:
            return False
        
        username_elem.clear()
        username_elem.send_keys(SAKAI_USERNAME)
        password_elem.clear()
        password_elem.send_keys(SAKAI_PASSWORD)
        
        # Submit login
        submit_button = None
        for by, value in [
            (By.CSS_SELECTOR, "input[type='submit']"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(., 'Giriş') or contains(., 'Login')]")
        ]:
            try:
                submit_button = driver.find_element(by, value)
                break
            except Exception:
                continue
        
        if submit_button:
            driver.execute_script('arguments[0].click();', submit_button)
        else:
            password_elem.submit()
        
        # Wait for login completion
        try:
            WebDriverWait(driver, TIMEOUT_ELEMENT).until(
                EC.presence_of_element_located((By.ID, 'Mrphs-bullhorn'))
            )
            return True
        except Exception:
            return False
            
    except Exception as e:
        logger.warning(f"Login error: {e}")
        return False


def fetch_from_notifications(driver) -> List[Dict[str, str]]:
    """
    Fetch announcements from notification panel.
    Uses notification panel text directly when available.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of announcement dictionaries
    """
    announcements = []
    
    try:
        bullhorn = driver.find_element(By.ID, 'Mrphs-bullhorn')
        
        # Get notification count
        count = 0
        try:
            counter_elem = bullhorn.find_element(By.ID, 'bullhorn-counter')
            count = int(''.join(filter(str.isdigit, counter_elem.text or "0")))
        except Exception:
            try:
                counter_elem = bullhorn.find_element(By.CLASS_NAME, 'bullhorn-counter-red')
                count = int(''.join(filter(str.isdigit, counter_elem.text or "0")))
            except Exception:
                count = 0
        
        if count == 0:
            logger.info("No new notifications")
            return announcements
        
        logger.info(f"Found {count} new notifications")
        driver.execute_script('arguments[0].click();', bullhorn)
        time.sleep(2)
        
        # Find all notification items in the panel
        items = []
        for xpath in [
            "//ul[@id='notification-list']//li",
            "//div[contains(@class, 'notification-item')]",
            "//*[contains(@class, 'bullhorn')]//li",
            "//div[contains(@class, 'portal-bullhorn-list')]//li"
        ]:
            try:
                items = driver.find_elements(By.XPATH, xpath)
                if items:
                    logger.info(f"Found {len(items)} items via XPath")
                    break
            except Exception:
                continue
        
        # Fallback: find all links with announcement hrefs
        if not items:
            try:
                items = driver.find_elements(
                    By.XPATH,
                    "//a[contains(@href, '/announcement/msg/') or contains(@href, 'directtool')]"
                )
                logger.info(f"Found {len(items)} items via link search")
            except Exception:
                pass
        
        # Build a strict candidate list: prefer items with the bullhorn icon
        # or items with announcement-like hrefs. If neither exists, do not process
        # general page elements to avoid course lists/menus being captured.
        candidates = []

        # 1) items that contain the bullhorn icon
        for it in items:
            try:
                if it.find_elements(By.CSS_SELECTOR, '.icon-sakai--academic-bullhorn'):
                    candidates.append(it)
            except Exception:
                continue

        # 2) items that include a link to an announcement detail
        if not candidates:
            for it in items:
                try:
                    link = None
                    try:
                        link = it.find_element(By.TAG_NAME, 'a')
                    except Exception:
                        pass
                    href = None
                    if link:
                        href = link.get_attribute('href')
                    else:
                        try:
                            href = it.get_attribute('href')
                        except Exception:
                            href = None

                    if href and ('/announcement/msg/' in href or '/announcement' in href or 'directtool' in href):
                        candidates.append(it)
                except Exception:
                    continue

        # 3) try ancestor search for icon if still nothing
        if not candidates:
            try:
                icon_ancestors = driver.find_elements(By.XPATH, "//*[contains(@class,'icon-sakai--academic-bullhorn')]/ancestor::li[1] | //*[contains(@class,'icon-sakai--academic-bullhorn')]/ancestor::div[1]")
                if icon_ancestors:
                    logger.info(f"Found {len(icon_ancestors)} items via icon ancestor search")
                    candidates = icon_ancestors
            except Exception:
                pass

        # If still no candidates, stop early to avoid false positives
        if not candidates:
            logger.info("No announcement-like items found in notification panel; skipping")
            return announcements

        for item in candidates:
            try:
                # Get full text from item
                item_text = item.text.strip()
                if not item_text or len(item_text) < 5:
                    continue
                
                # Try to find link
                href = None
                try:
                    link_elem = item.find_element(By.TAG_NAME, 'a')
                    href = link_elem.get_attribute('href')
                except Exception:
                    try:
                        href = item.get_attribute('href')
                    except Exception:
                        pass
                
                # Split title and content from panel text
                lines = item_text.split('\n')
                title = lines[0].strip() if lines else item_text
                panel_content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
                
                # Use panel content if available and substantial
                content = panel_content if panel_content and len(panel_content) > 30 else ""
                
                # Only fetch detail page if:
                # 1. We have a link AND
                # 2. Panel content is too short/empty
                if href and (not content or len(content) < 50):
                    logger.info(f"Fetching detail content from: {href}")
                    detail_content = extract_content_from_link(driver, href)
                    if detail_content and len(detail_content) > len(content):
                        content = detail_content
                
                # Fallback: use item text if no content extracted
                if not content:
                    content = item_text
                
                announcements.append({
                    "title": title,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Added announcement: {title[:50]}...")
                
            except Exception as e:
                logger.warning(f"Error processing notification item: {e}")
                continue
        
        logger.info(f"Fetched {len(announcements)} announcement(s) from notifications")
        return announcements
        
    except Exception as e:
        logger.info(f"Notifications not available: {e}")
        return announcements


def search_page_announcements(driver) -> List[Dict[str, str]]:
    """
    Search for announcements on the current page.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of announcement dictionaries
    """
    announcements = []
    
    try:
        # Find potential announcement elements
        keywords = ['duyuru', 'announcement', 'başlık', 'title', 'subject']
        elements = []
        
        for elem in driver.find_elements(By.XPATH, "//div | //li | //article")[:100]:
            try:
                text = elem.text
                if text and len(text) > 10:
                    if any(kw in text.lower() for kw in keywords):
                        elements.append(elem)
            except Exception:
                continue
        
        logger.info(f"Found {len(elements)} potential announcement element(s)")
        
        for elem in elements[:MAX_ANNOUNCEMENTS]:
            try:
                text = elem.text.strip()
                if not text or len(text) < 5:
                    continue
                
                # Extract title (first line or heading)
                title = None
                for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b']:
                    try:
                        heading = elem.find_element(By.TAG_NAME, tag)
                        title = heading.text.strip()
                        if title:
                            break
                    except Exception:
                        continue
                
                if not title:
                    lines = text.split('\n')
                    title = lines[0] if lines else text
                
                # Extract content from link if available
                content = ""
                try:
                    link = elem.find_element(By.TAG_NAME, 'a')
                    href = link.get_attribute('href')
                    if href:
                        content = extract_content_from_link(driver, href)
                except Exception:
                    lines = text.split('\n')
                    content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
                
                announcements.append({
                    "title": title.strip(),
                    "content": content.strip(),
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.warning(f"Error processing announcement element: {e}")
                continue
        
        logger.info(f"Found {len(announcements)} announcement(s) on page")
        return announcements
        
    except Exception as e:
        logger.error(f"Error searching page announcements: {e}")
        return announcements


def load_saved_announcements() -> List[Dict[str, str]]:
    """Load previously saved announcements."""
    try:
        if os.path.exists(ANNOUNCEMENTS_FILE):
            with open(ANNOUNCEMENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading announcements file: {e}")
    
    return []


def save_announcements(announcements: List[Dict[str, str]]) -> None:
    """Save announcements to file."""
    try:
        with open(ANNOUNCEMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(announcements, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(announcements)} announcement(s)")
    except Exception as e:
        logger.error(f"Error saving announcements: {e}")


def find_new_announcements(
    current: List[Dict[str, str]],
    previous: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """
    Find new announcements by comparing current and previous.
    Handles both old and new JSON formats for backward compatibility.
    
    Args:
        current: Current announcements
        previous: Previously saved announcements
        
    Returns:
        List of new announcements
    """
    previous_titles = set()
    
    # Handle both old format (baslik) and new format (title)
    for ann in previous:
        title = ann.get("title") or ann.get("baslik")
        if title:
            previous_titles.add(title)
    
    new = [ann for ann in current if (ann.get("title") or ann.get("baslik")) not in previous_titles]
    
    logger.info(f"Found {len(new)} new announcement(s)")
    return new


def main():
    """Main bot function."""
    logger.info("=" * 60)
    logger.info(f"SAKAI ANNOUNCEMENT BOT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Validate configuration
    if not validate_configuration():
        logger.error("Configuration validation failed. Exiting.")
        return False
    
    driver = None
    
    try:
        # Initialize WebDriver
        driver = get_webdriver()
        
        # Fetch announcements
        current_announcements = fetch_announcements(driver)
        
        if not current_announcements:
            logger.info("No announcements found")
            return True
        
        # Load previous announcements
        previous_announcements = load_saved_announcements()
        
        # Save current announcements
        save_announcements(current_announcements)
        
        # Find new announcements
        new_announcements = find_new_announcements(current_announcements, previous_announcements)
        
        # Send notifications for new announcements
        if new_announcements:
            logger.info(f"Sending {len(new_announcements)} notification(s)")
            for announcement in new_announcements:
                send_telegram_notification(
                    announcement["title"],
                    announcement["content"]
                )
                time.sleep(TELEGRAM_RATE_LIMIT)
        else:
            logger.info("No new announcements")
        
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        send_telegram_notification("BOT ERROR", f"Unexpected error:\n{str(e)}")
        return False
        
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
