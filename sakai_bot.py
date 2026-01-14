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
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG for detailed troubleshooting
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
    Ensures proper HTML entity escaping for Telegram parse mode.
    
    Args:
        title: Announcement title (should already be HTML-escaped)
        content: Announcement content (should already be HTML-escaped)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
        # Additional safety: ensure HTML entities are properly escaped
        # The content should already be escaped in fetch_announcements, but double-check
        safe_title = title.replace('<', '&lt;').replace('>', '&gt;')
        safe_content = content.replace('<', '&lt;').replace('>', '&gt;')
        
        message = f"<b>📢 YENİ DUYURU</b>\n\n<b>{safe_title}</b>\n\n{safe_content}"
        
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Telegram notification sent: {title[:50]}")
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
        
        # Use webdriver_manager to automatically install/update driver
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("Chrome WebDriver initialized")
        return driver
        
    except Exception as e:
        logger.warning(f"Chrome initialization failed, trying Firefox: {e}")
        try:
            options = FirefoxOptions()
            if HEADLESS:
                options.add_argument("--headless")
            
            service = FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)
            logger.info("Firefox WebDriver initialized")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to initialize any WebDriver: {e}")
            raise


def extract_content_from_link(driver, href: str) -> Dict[str, any]:
    """
    Open link in new tab and extract content, title, and attachments.
    Extracts ONLY the message body between "Mesaj" and "Ekler" labels.
    Also extracts attachment links from the "Ekler" section.
    
    Args:
        driver: Selenium WebDriver instance
        href: URL to fetch content from
        
    Returns:
        Dictionary with 'content', 'title', and 'attachments' keys
    """
    result = {
        "content": "",
        "title": "",
        "attachments": []
    }
    original_window = None
    
    try:
        original_window = driver.current_window_handle
        driver.execute_script('window.open(arguments[0]);', href)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(2)
        
        # Try to extract title from page
        try:
            # Try multiple title selectors
            title_selectors = [
                "//h1", "//h2", "//div[@class='announcementTitle']",
                "//div[@class='portletTitle']", "//div[@class='title']",
                "//span[@class='title']", "//*[contains(text(), 'Sınav')]//ancestor::div[1]"
            ]
            for selector in title_selectors:
                try:
                    title_elem = driver.find_element(By.XPATH, selector)
                    text = title_elem.text.strip()
                    if text and len(text) > 3:
                        result["title"] = text
                        logger.debug(f"Found page title via {selector}: {result['title'][:80]}")
                        break
                except Exception:
                    continue
        except Exception:
            pass
        
        # Try various CSS selectors for content
        selectors = [
            '.announcementBody', '.announcement-content', '.msgBody',
            '#main', '.portletBody', '.sakai-content', '.content', 'article'
        ]
        
        content = ""
        for selector in selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text and len(text) > 20:
                    content = text
                    logger.debug(f"Found content via {selector}: {len(text)} chars")
                    break
            except Exception:
                continue
        
        # Extract ONLY the message body (between "Mesaj" and "Ekler" labels)
        if content:
            lines = content.split('\n')
            filtered_lines = []
            in_message_section = False
            in_attachments_section = False
            
            logger.debug(f"Total lines before filtering: {len(lines)}")
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                # Start capturing when we hit "Mesaj" label
                if line_stripped == 'Mesaj':
                    in_message_section = True
                    in_attachments_section = False
                    logger.debug(f"Found 'Mesaj' marker at line {i}")
                    continue
                
                # When we hit "Ekler", switch to attachments section
                if line_stripped in ['Ekler', 'Dosyalar', 'Attachments', 'Eklentiler']:
                    in_attachments_section = True
                    in_message_section = False
                    logger.debug(f"Found attachments marker '{line_stripped}' at line {i}")
                    continue
                
                # Capture lines in the message section
                if in_message_section and line_stripped:
                    filtered_lines.append(line_stripped)
                
                # Capture attachment lines (name and size)
                if in_attachments_section and line_stripped:
                    # Skip metadata lines
                    if not any(skip in line_stripped.lower() for skip in ['ekleyen', 'tarih', 'düzenleme']):
                        result["attachments"].append(line_stripped)
                        logger.debug(f"Found attachment: {line_stripped}")
            
            if filtered_lines:
                content = '\n'.join(filtered_lines)
                result["content"] = content
                logger.debug(f"After boundary extraction: {len(content)} chars, {len(filtered_lines)} lines")
            else:
                # Fallback: filter metadata
                logger.debug(f"Boundary extraction failed, using fallback")
                metadata_starts = ['Ekleyen', 'Düzenlenme', 'Gruplar', 'Ekler', 'Dosyalar']
                filtered = '\n'.join(
                    line.strip() for line in lines 
                    if line.strip() and not any(line.strip().startswith(m) for m in metadata_starts)
                )
                result["content"] = filtered
                logger.debug(f"After fallback filter: {len(filtered)} chars")
            
            # Limit content length
            if len(result["content"]) > 1500:
                result["content"] = result["content"][:1500] + "..."
        
        # If no content found, try body text
        if not result["content"] or len(result["content"]) < 10:
            logger.debug("Fallback to full body text extraction")
            try:
                body = driver.find_element(By.TAG_NAME, 'body')
                full_text = body.text.strip()
                
                lines = full_text.split('\n')
                filtered_lines = []
                in_message_section = False
                
                for line in lines:
                    line_stripped = line.strip()
                    
                    if line_stripped == 'Mesaj':
                        in_message_section = True
                        continue
                    
                    if line_stripped in ['Ekler', 'Dosyalar', 'Attachments', 'Eklentiler']:
                        break
                    
                    if in_message_section and line_stripped:
                        filtered_lines.append(line_stripped)
                
                if filtered_lines:
                    result["content"] = '\n'.join(filtered_lines)
                    logger.debug(f"Fallback extraction: {len(result['content'])} chars")
                    if len(result["content"]) > 1500:
                        result["content"] = result["content"][:1500] + "..."
                else:
                    # Last resort
                    metadata_starts = ['Ekleyen', 'Düzenlenme', 'Gruplar', 'Ekler', 'Dosyalar']
                    filtered = '\n'.join(
                        line.strip() for line in lines 
                        if line.strip() and not any(line.strip().startswith(m) for m in metadata_starts)
                    )
                    result["content"] = filtered
                        
            except Exception as e:
                logger.debug(f"Body fallback failed: {e}")
        
        # Try to extract attachment links from the page
        if not result["attachments"]:
            try:
                # Look for links in attachments section
                attachment_section = driver.find_element(By.XPATH, "//*[contains(text(), 'Ekler') or contains(text(), 'Dosyalar')]/..")
                links = attachment_section.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href_attr = link.get_attribute('href')
                    text = link.text.strip()
                    if href_attr and text:
                        result["attachments"].append(f"{text} ({href_attr})")
                        logger.debug(f"Found attachment: {text}")
            except Exception as e:
                logger.debug(f"Attachment section not found: {e}")
                
    except Exception as e:
        logger.warning(f"Error extracting content from {href}: {e}")
    finally:
        try:
            driver.close()
            if original_window:
                driver.switch_to.window(original_window)
        except Exception:
            pass
    
    return result

def fetch_announcements(driver) -> List[Dict[str, str]]:
    """
    Fetch announcements from Sakai LMS.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of announcement dictionaries with title, content, href, and timestamp
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

        # By default we DO NOT fallback to scanning the whole page because
        # that produces false positives (course lists / menus). If you want
        # the old behavior, set environment variable `ALLOW_PAGE_SEARCH=1`.
        allow_page_search = os.getenv("ALLOW_PAGE_SEARCH", "0").lower() in ("1", "true", "yes")
        if allow_page_search:
            logger.info("No panel notifications found — falling back to page search (ALLOW_PAGE_SEARCH=1)")
            announcements = search_page_announcements(driver)
            return announcements

        logger.info("No notifications in panel and page search disabled — skipping")
        return []
        
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
        logger.debug(f"Bullhorn element found: {bullhorn}")
        
        # Get notification count - multiple strategies
        count = 0
        count_text = ""
        
        # Strategy 1: Try ID-based counter
        try:
            counter_elem = bullhorn.find_element(By.ID, 'bullhorn-counter')
            count_text = counter_elem.text.strip()
            count = int(''.join(filter(str.isdigit, count_text or "0")))
            logger.debug(f"Counter via ID: '{count_text}' -> {count}")
        except Exception as e:
            logger.debug(f"ID counter failed: {e}")
        
        # Strategy 2: Try class-based counter
        if count == 0:
            try:
                counter_elem = bullhorn.find_element(By.CLASS_NAME, 'bullhorn-counter-red')
                count_text = counter_elem.text.strip()
                count = int(''.join(filter(str.isdigit, count_text or "0")))
                logger.debug(f"Counter via class: '{count_text}' -> {count}")
            except Exception as e:
                logger.debug(f"Class counter failed: {e}")
        
        # Strategy 3: Try any span/div with numbers
        if count == 0:
            try:
                spans = bullhorn.find_elements(By.TAG_NAME, 'span')
                for span in spans:
                    text = span.text.strip()
                    nums = ''.join(filter(str.isdigit, text))
                    if nums:
                        count = int(nums)
                        logger.debug(f"Counter via span scan: '{text}' -> {count}")
                        break
            except Exception as e:
                logger.debug(f"Span scan failed: {e}")
        
        # Always try to open notification panel regardless of count
        logger.info(f"Notification count: {count} (opening panel to scan)")
        try:
            driver.execute_script('arguments[0].click();', bullhorn)
        except Exception:
            bullhorn.click()
        time.sleep(2)
        
        # Find all notification items - use portal-bullhorn-alert containers
        # This is the actual Sakai structure based on DOM inspection
        items = []
        
        # Primary: portal-bullhorn-alert containers (Sakai 12.x+ structure)
        try:
            alerts = driver.find_elements(By.XPATH, "//div[@class='portal-bullhorn-alert']")
            if alerts:
                logger.debug(f"Found {len(alerts)} alert containers via portal-bullhorn-alert")
                items.extend(alerts)
        except Exception as e:
            logger.debug(f"portal-bullhorn-alert search failed: {e}")
        
        # Fallback: Try other structures if no alerts found
        if not items:
            xpaths = [
                "//ul[@id='notification-list']//li",
                "//div[contains(@class, 'notification-item')]",
                "//div[contains(@class, 'portal-bullhorn-message')]",
                "//a[contains(@href, '/announcement/')]"
            ]
            
            for xpath in xpaths:
                try:
                    found = driver.find_elements(By.XPATH, xpath)
                    if found:
                        logger.debug(f"Found {len(found)} items via: {xpath}")
                        items.extend(found)
                except Exception as e:
                    logger.debug(f"XPath failed ({xpath}): {e}")
        
        # Remove duplicates by keeping unique elements
        items = list(dict.fromkeys(items))
        logger.info(f"Total unique items found: {len(items)}")
        
        if not items:
            logger.warning("No notification items found in panel")
            return announcements
        
        # Process items
        for idx, item in enumerate(items):
            try:
                # For portal-bullhorn-alert containers, extract structured data
                href = None
                title = None
                time_str = None
                item_text = ""
                attachments = []  # Track attachment links and their text
                
                # Check if this is a portal-bullhorn-alert container
                if 'portal-bullhorn-alert' in (item.get_attribute('class') or ''):
                    logger.debug(f"Processing portal-bullhorn-alert item {idx}")
                    
                    # Get link
                    try:
                        link = item.find_element(By.XPATH, ".//a[contains(@href, '/announcement/')]")
                        href = link.get_attribute('href')
                        item_text = link.text.strip()
                    except Exception:
                        pass
                    
                    # Get message text (from portal-bullhorn-message div)
                    # Use innerHTML parsing because .text sometimes returns empty for AJAX-loaded content
                    try:
                        msg_div = item.find_element(By.XPATH, ".//div[@class='portal-bullhorn-message']")
                        logger.debug(f"Item {idx}: Found portal-bullhorn-message div")
                        
                        # DEBUG: Check the actual HTML structure
                        html_content = msg_div.get_attribute('innerHTML')
                        logger.debug(f"Item {idx} innerHTML length: {len(html_content)} chars")
                        logger.debug(f"Item {idx} innerHTML preview: {html_content[:200]}...")
                        logger.debug(f"Item {idx} .text: '{msg_div.text}'")
                        logger.debug(f"Item {idx} .textContent: '{msg_div.get_attribute('textContent')}'")
                        
                        # Try .text first
                        item_text = msg_div.text.strip()
                        
                        # If empty, try multiple extraction methods
                        if not item_text:
                            # Method 1: Use Selenium's built-in text extraction with wait
                            try:
                                WebDriverWait(driver, 2).until(
                                    lambda d: d.execute_script("return arguments[0].textContent.trim();", msg_div)
                                )
                                item_text = driver.execute_script("return arguments[0].textContent.trim();", msg_div)
                                logger.debug(f"Item {idx} extracted via JavaScript: '{item_text[:50]}...'")
                            except Exception as e:
                                logger.debug(f"JavaScript extraction failed: {e}")
                        
                        # Method 2: Parse innerHTML manually if still empty
                        if not item_text:
                            logger.debug(f"Item {idx}: Trying innerHTML parsing")
                            # Extract all text from HTML, including text nodes
                            from html.parser import HTMLParser
                            class TextExtractor(HTMLParser):
                                def __init__(self):
                                    super().__init__()
                                    self.text = []
                                def handle_data(self, data):
                                    text = data.strip()
                                    if text:
                                        self.text.append(text)
                            parser = TextExtractor()
                            parser.feed(html_content)
                            item_text = ' '.join(parser.text)
                            logger.debug(f"Item {idx} parsed text: '{item_text[:50]}...' (len={len(item_text)})")
                        
                        # Method 3: If still empty, try to get text from the entire container
                        if not item_text:
                            logger.debug(f"Item {idx}: All methods failed, trying container .text")
                            item_text = item.text.strip()
                            logger.debug(f"Item {idx} container .text: '{item_text[:50]}...'")
                            
                    except Exception as e:
                        logger.debug(f"Item {idx}: Message div not found or error: {e}")
                        pass
                    
                    # Get time
                    try:
                        time_div = item.find_element(By.XPATH, ".//div[@class='portal-bullhorn-time']")
                        time_str = time_div.text.strip()
                    except Exception:
                        pass
                    
                else:
                    # For other item types, use standard extraction
                    item_text = item.text.strip()
                    try:
                        link = item.find_element(By.TAG_NAME, 'a')
                        href = link.get_attribute('href')
                    except Exception:
                        pass
                
                # Skip empty items
                if not item_text or len(item_text) < 10:
                    logger.debug(f"Item {idx} too short ({len(item_text)} chars), skipping")
                    continue
                
                # Check if this looks like an announcement
                has_announcement_href = href and ('/announcement' in href or 'directtool' in href)
                looks_like_announcement = any(kw in item_text.lower() for kw in ['duyuru', 'announcement', 'notice', 'yeni', 'eklendi'])
                
                # Include item if it has announcement href OR looks like announcement
                should_process = has_announcement_href or looks_like_announcement
                
                if not should_process:
                    logger.debug(f"Item {idx} doesn't look like announcement: {item_text[:50]}")
                    continue
                
                logger.debug(f"Item {idx} ACCEPTED (href={bool(has_announcement_href)}, text={looks_like_announcement})")
                logger.debug(f"  Full text: {item_text[:120]}")
                logger.debug(f"  Href: {href}")
                logger.debug(f"  Time: {time_str}")
                
                # Extract title (first line or first 100 chars)
                lines = item_text.split('\n')
                title = lines[0].strip() if lines else item_text[:100]
                
                # Parse title to extract actual announcement title
                # Format: "INSTRUCTOR_NAME ... "COURSE"'de "ANNOUNCEMENT_TITLE" ... eklendi"
                # Extract the announcement title (text between last quotes before "eklendi")
                actual_title = title
                if "\"" in title and "eklendi" in title.lower():
                    # Try to extract announcement title from pattern
                    import re
                    # Match last quoted string before "eklendi"
                    matches = re.findall(r'"([^"]*)"', title)
                    if matches and len(matches) >= 2:
                        # If we have at least 2 quotes, the last one is usually the announcement title
                        actual_title = matches[-1]  # Get the last quoted string (announcement title)
                        logger.debug(f"Extracted title from pattern: {actual_title}")
                
                # Use full text as content initially
                content = item_text
                
                # Skip if title is generic menu item
                if any(skip in actual_title.lower() for skip in ['takvim', 'kaynaklar', 'ayarlar', 'profil', 'ders listesi', 'ana sayfa', 'temizle']):
                    logger.debug(f"Skipping generic menu item: {actual_title}")
                    continue
                
                # Try to fetch detail if we have a link
                detail_fetched = False
                page_title = ""
                attachments = []
                
                if href:
                    try:
                        logger.debug(f"Fetching detail content from: {href[:80]}")
                        detail_result = extract_content_from_link(driver, href)
                        
                        if detail_result.get("content") and len(detail_result["content"]) > 20:
                            content = detail_result["content"]
                            detail_fetched = True
                            page_title = detail_result.get("title", "")
                            attachments = detail_result.get("attachments", [])
                            logger.debug(f"Got detail content ({len(content)} chars), title: '{page_title}', attachments: {len(attachments)}")
                        else:
                            logger.debug(f"Detail content too short or empty: {len(detail_result.get('content', ''))}")
                    except Exception as e:
                        logger.debug(f"Detail fetch failed: {e}")
                
                # If no detail content fetched, use the notification text
                if not detail_fetched:
                    content = actual_title  # Just use the clean title
                    logger.debug(f"Using notification text as content (no detail page)")
                
                # Build final message with title and attachments
                final_message = ""
                
                # Add page title if available
                if page_title:
                    final_message = f"📌 {page_title}\n\n"
                
                # Add content
                final_message += content
                
                # Add attachments section if available
                if attachments:
                    final_message += f"\n\n📎 Ekler ({len(attachments)}):\n"
                    for i, att in enumerate(attachments[:5], 1):  # Limit to 5 attachments
                        # Clean up attachment line
                        att_clean = att.strip()
                        if att_clean:
                            final_message += f"{i}. {att_clean}\n"
                    final_message = final_message.rstrip()  # Remove trailing newline
                
                logger.debug(f"Final message length: {len(final_message)} chars")
                
                # HTML escape content for Telegram (convert special chars to entities)
                # This prevents "Unsupported start tag" and parsing errors
                # Escape & first (to avoid double-escaping), then < and >
                final_message = final_message.replace('&', '&amp;')
                final_message = final_message.replace('<', '&lt;')
                final_message = final_message.replace('>', '&gt;')
                
                # Escape ampersand and other special chars in title too
                title_escaped = actual_title[:100]
                title_escaped = title_escaped.replace('&', '&amp;')
                title_escaped = title_escaped.replace('<', '&lt;')
                title_escaped = title_escaped.replace('>', '&gt;')
                
                announcements.append({
                    "title": title_escaped,  # Use extracted announcement title (escaped)
                    "content": final_message[:2000],  # Limit content length
                    "href": href,  # Store href as unique identifier
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"✓ Added announcement: {actual_title[:60]}")
                
            except Exception as e:
                logger.warning(f"Error processing item {idx}: {e}")
                continue
        
        logger.info(f"Fetched {len(announcements)} announcement(s) from notifications")
        return announcements
        
    except Exception as e:
        logger.error(f"Notifications panel error: {e}", exc_info=True)
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
        
        logger.info(f"Saved {len(announcements)} announcement(s) to {ANNOUNCEMENTS_FILE}")
        
        # Verify what we saved
        if os.path.exists(ANNOUNCEMENTS_FILE):
            file_size = os.path.getsize(ANNOUNCEMENTS_FILE)
            logger.info(f"File size: {file_size} bytes")
            logger.debug(f"Saved announcements details:")
            for i, ann in enumerate(announcements):
                logger.debug(f"  [{i}] title='{ann.get('title', '')[:50]}...' href='{ann.get('href', 'NO HREF')}'")
        else:
            logger.error(f"File was not created!")
    except Exception as e:
        logger.error(f"Error saving announcements: {e}")


def find_new_announcements(
    current: List[Dict[str, str]],
    previous: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """
    Find new announcements by comparing current and previous.
    Uses 'href' as unique identifier to prevent duplicates (same-title but different announcements).
    
    Args:
        current: Current announcements
        previous: Previously saved announcements
        
    Returns:
        List of new announcements
    """
    previous_hrefs = set()
    
    logger.debug(f"Previous announcements count: {len(previous)}")
    for i, ann in enumerate(previous):
        href = ann.get("href")
        logger.debug(f"  [{i}] title='{ann.get('title', '')[:50]}...' href='{href}'")
        if href:
            previous_hrefs.add(href)
    
    logger.debug(f"Current announcements count: {len(current)}")
    for i, ann in enumerate(current):
        href = ann.get("href")
        logger.debug(f"  [{i}] title='{ann.get('title', '')[:50]}...' href='{href}'")
    
    # Find announcements whose href is not in previous set
    new = [ann for ann in current if ann.get("href") not in previous_hrefs]
    
    logger.info(f"Found {len(new)} new announcement(s) (using href-based deduplication)")
    logger.info(f"  Previous hrefs count: {len(previous_hrefs)}")
    logger.info(f"  New announcements details:")
    for i, ann in enumerate(new):
        logger.info(f"    [{i}] title='{ann.get('title', '')[:60]}...'")
    
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
        
        # Load previous announcements (BEFORE fetching current)
        previous_announcements = load_saved_announcements()
        logger.info(f"Loaded {len(previous_announcements)} previously saved announcement(s)")
        
        # Fetch announcements
        current_announcements = fetch_announcements(driver)
        
        if not current_announcements:
            logger.info("No announcements found")
            return True
        
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
            
            # Save announcements AFTER sending (append new to previous)
            all_announcements = previous_announcements + new_announcements
            save_announcements(all_announcements)
            logger.info(f"Saved {len(all_announcements)} total announcement(s) to {ANNOUNCEMENTS_FILE}")
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
