"""
DULMS scraper core functionality.
"""
import selenium
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
import re
from PIL import Image
import base64
import io
import time
import requests
import os
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
import queue
import json

from app.config import settings
from app.utils.notifications import send_discord_webhook, format_discord_embeds_for_assignments, format_discord_embeds_for_quizzes

# --- Module Level Logger ---
logger = logging.getLogger(__name__)

# --- Selenium Driver Initialization ---
def initialize_driver(headless=True):
    """
    Initializes and returns a Selenium WebDriver instance.
    
    Args:
        headless: Whether to run the browser in headless mode
        
    Returns:
        WebDriver instance
    """
    logger.info("Initializing the Selenium driver...")
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--log-level=3")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.page_load_strategy = 'normal'

    try:
        # Ensure the driver path exists before attempting to use it
        driver_executable_path = Path(settings.DRIVER_PATH)
        if not driver_executable_path.is_file():
            logger.error(f"WebDriver executable not found at specified path: {settings.DRIVER_PATH}")
            raise FileNotFoundError(f"WebDriver executable not found at: {settings.DRIVER_PATH}")

        service = Service(executable_path=str(driver_executable_path))
        driver = webdriver.Edge(service=service, options=options)
        logger.info("Driver initialized successfully.")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {e}")
        logger.error(f"Ensure '{settings.DRIVER_PATH}' is in your PATH or the correct path is specified.")
        raise

# --- Utility Functions ---
def wait_for_element(driver, by, value, timeout=settings.DEFAULT_TIMEOUT):
    """
    Waits for an element to be present and visible.
    
    Args:
        driver: WebDriver instance
        by: Locator strategy
        value: Locator value
        timeout: Time to wait for the element
        
    Returns:
        The element if found, None otherwise
    """
    try:
        return WebDriverWait(driver, timeout, poll_frequency=settings.POLL_FREQUENCY).until(
            EC.visibility_of_element_located((by, value))
        )
    except TimeoutException:
        logger.warning(f"Timeout waiting for element: {by}={value}")
        return None
    except Exception as e:
        logger.error(f"Error waiting for element {by}={value}: {e}")
        return None

def safe_find_element(parent, by, value):
    """
    Safely finds an element, returning None if not found.
    
    Args:
        parent: Parent element or driver
        by: Locator strategy
        value: Locator value
        
    Returns:
        The element if found, None otherwise
    """
    try:
        return parent.find_element(by, value)
    except NoSuchElementException:
        return None
    except Exception as e:
        logger.error(f"Error finding element {by}={value}: {e}")
        return None

def get_captcha_image(driver):
    """
    Extract the CAPTCHA image from the page.
    
    Args:
        driver: WebDriver instance
        
    Returns:
        PIL Image object of the captcha
    """
    try:
        # Find the captcha image element
        img_element = driver.find_element(By.ID, 'imgCaptcha')
        
        # Get the base64 image data
        img_src = img_element.get_attribute('src')
        if not img_src or not img_src.startswith('data:image'):
            logger.error("CAPTCHA image source is not a data URL")
            return None
        
        # Extract the base64 data and convert to image
        img_data = img_src.split(',')[1]
        img_binary = base64.b64decode(img_data)
        return Image.open(io.BytesIO(img_binary))
    except Exception as e:
        logger.error(f"Failed to extract CAPTCHA image: {e}")
        return None

def solve_captcha(img, api_key):
    """
    Submit CAPTCHA to solving service and return the solution.
    
    Args:
        img: PIL Image object of the captcha
        api_key: API key for the captcha solving service
        
    Returns:
        The captcha solution text if successful, None otherwise
    """
    if not img:
        logger.error("No CAPTCHA image provided")
        return None
    
    try:
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Prepare the payload for the solving service API
        # NOTE: This is a placeholder. Replace with your actual captcha-solving service API.
        payload = {
            'key': api_key,
            'method': 'base64',
            'body': base64.b64encode(img_byte_arr).decode(),
            'json': 1
        }
        
        logger.info("Submitting CAPTCHA to solving service...")
        response = requests.post('https://api.anti-captcha.com/createTask', json=payload)
        response.raise_for_status()
        
        result = response.json()
        if 'solution' in result and 'text' in result['solution']:
            captcha_text = result['solution']['text']
            logger.info(f"CAPTCHA solution received: {captcha_text}")
            return captcha_text
        else:
            logger.error(f"Unexpected response format: {result}")
            return None
    except Exception as e:
        logger.error(f"Failed to solve CAPTCHA: {e}")
        return None

def login_to_dulms(driver, username, password, captcha_api_key):
    """
    Log in to DULMS with credentials and solved CAPTCHA.
    
    Args:
        driver: WebDriver instance
        username: DULMS username
        password: DULMS password
        captcha_api_key: API key for captcha solving service
        
    Returns:
        True if login successful, False otherwise
    """
    logger.info(f"Attempting to log in as {username}...")
    
    try:
        # Navigate to the login page
        driver.get(settings.LOGIN_URL)
        
        # Wait for the login page to load
        wait_for_element(driver, By.ID, "username")
        
        # Enter username and password
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        
        username_field.clear()
        username_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(password)
        
        # Solve and enter CAPTCHA
        for attempt in range(settings.CAPTCHA_SOLVE_RETRIES):
            logger.info(f"CAPTCHA solving attempt {attempt + 1}/{settings.CAPTCHA_SOLVE_RETRIES}")
            
            # Get the CAPTCHA image
            captcha_img = get_captcha_image(driver)
            if not captcha_img:
                logger.error("Failed to obtain CAPTCHA image")
                continue
            
            # Send to solving service
            captcha_solution = solve_captcha(captcha_img, captcha_api_key)
            if not captcha_solution:
                logger.error("Failed to solve CAPTCHA")
                continue
            
            # Enter the solution
            captcha_field = driver.find_element(By.ID, "txtCaptcha")
            captcha_field.clear()
            captcha_field.send_keys(captcha_solution)
            
            # Click login
            login_button = driver.find_element(By.ID, "btnLogin")
            login_button.click()
            
            # Wait for redirect or error
            time.sleep(3)
            
            # Check if login was successful by looking for the dashboard or profile page
            if settings.LOGIN_SUCCESS_URL_PART in driver.current_url:
                logger.info("Login successful!")
                return True
            
            # Check for error message
            error_msg = safe_find_element(driver, By.ID, "lblMessage")
            if error_msg and error_msg.is_displayed():
                logger.warning(f"Login failed: {error_msg.text}")
                # If it's a CAPTCHA error, try again, otherwise break
                if "CAPTCHA" in error_msg.text:
                    continue
                break
        
        logger.error("Failed to login after multiple attempts")
        return False
    
    except Exception as e:
        logger.error(f"Login process failed with error: {e}")
        traceback.print_exc()
        return False

def scrape_assignments(driver):
    """
    Scrape assignment information from DULMS.
    
    Args:
        driver: Logged-in WebDriver instance
        
    Returns:
        List of assignment data dictionaries
    """
    assignments = []
    now = datetime.now()
    
    try:
        logger.info("Navigating to assignments page...")
        driver.get(settings.ASSIGNMENTS_URL)
        
        # Wait for the assignments table to load
        assignment_table = wait_for_element(driver, By.ID, "gvAssignment")
        if not assignment_table:
            logger.error("Assignments table not found")
            return assignments
        
        # Find all rows except the header
        rows = assignment_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
        
        logger.info(f"Found {len(rows)} assignment entries")
        
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 6:  # Ensure we have enough cells
                    continue
                
                # Extract data from cells
                assign_id = cells[0].text.strip()
                title_cell = cells[1]
                title_link = safe_find_element(title_cell, By.TAG_NAME, "a")
                
                # Get title and URL
                if title_link:
                    title = title_link.text.strip()
                    url = title_link.get_attribute("href")
                else:
                    title = cells[1].text.strip()
                    url = settings.ASSIGNMENTS_URL
                
                course = cells[2].text.strip()
                deadline_str = cells[3].text.strip()
                status = cells[5].text.strip()
                
                # Parse deadline date
                try:
                    deadline = datetime.strptime(deadline_str, "%d/%m/%Y")
                    days_remaining = (deadline - now).days
                except Exception as e:
                    logger.warning(f"Failed to parse deadline date '{deadline_str}': {e}")
                    deadline = None
                    days_remaining = None
                
                # Create assignment data dictionary
                assignment_data = {
                    "id": assign_id,
                    "title": title,
                    "course": course,
                    "deadline": deadline_str,
                    "days_remaining": days_remaining,
                    "status": status,
                    "url": url
                }
                
                assignments.append(assignment_data)
                
            except Exception as e:
                logger.error(f"Error processing assignment row: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(assignments)} assignments")
        return assignments
        
    except Exception as e:
        logger.error(f"Failed to scrape assignments: {e}")
        traceback.print_exc()
        return assignments

def scrape_quizzes(driver):
    """
    Scrape quiz information from DULMS.
    
    Args:
        driver: Logged-in WebDriver instance
        
    Returns:
        List of quiz data dictionaries
    """
    quizzes = []
    now = datetime.now()
    
    try:
        logger.info("Navigating to quizzes page...")
        driver.get(settings.QUIZZES_URL)
        
        # Wait for the quizzes table to load
        quiz_table = wait_for_element(driver, By.ID, "gvQuiz")
        if not quiz_table:
            logger.error("Quizzes table not found")
            return quizzes
        
        # Find all rows except the header
        rows = quiz_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
        
        logger.info(f"Found {len(rows)} quiz entries")
        
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 6:  # Ensure we have enough cells
                    continue
                
                # Extract data from cells
                quiz_id = cells[0].text.strip()
                title_cell = cells[1]
                title_link = safe_find_element(title_cell, By.TAG_NAME, "a")
                
                # Get title and URL
                if title_link:
                    title = title_link.text.strip()
                    url = title_link.get_attribute("href")
                else:
                    title = cells[1].text.strip()
                    url = settings.QUIZZES_URL
                
                course = cells[2].text.strip()
                deadline_str = cells[3].text.strip()
                status = cells[5].text.strip()
                
                # Parse deadline date
                try:
                    deadline = datetime.strptime(deadline_str, "%d/%m/%Y")
                    days_remaining = (deadline - now).days
                except Exception as e:
                    logger.warning(f"Failed to parse deadline date '{deadline_str}': {e}")
                    deadline = None
                    days_remaining = None
                
                # Create quiz data dictionary
                quiz_data = {
                    "id": quiz_id,
                    "title": title,
                    "course": course,
                    "deadline": deadline_str,
                    "days_remaining": days_remaining,
                    "status": status,
                    "url": url
                }
                
                quizzes.append(quiz_data)
                
            except Exception as e:
                logger.error(f"Error processing quiz row: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(quizzes)} quizzes")
        return quizzes
        
    except Exception as e:
        logger.error(f"Failed to scrape quizzes: {e}")
        traceback.print_exc()
        return quizzes

def run_dulms_scraper(
    username,
    password,
    captcha_api_key,
    discord_webhook=None,
    log_queue=None,
    headless=True
):
    """
    Main scraper function that extracts assignments and quizzes from DULMS.
    
    Args:
        username: DULMS username
        password: DULMS password
        captcha_api_key: API key for captcha solving service
        discord_webhook: Optional Discord webhook URL for notifications
        log_queue: Optional queue for logging messages
        headless: Whether to run the browser in headless mode
        
    Returns:
        Dictionary with scraped assignments and quizzes data
    """
    driver = None
    result = {
        "assignments": [],
        "quizzes": [],
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "message": ""
    }
    
    try:
        # Initialize the driver
        driver = initialize_driver(headless=headless)
        
        # Login to DULMS
        login_success = login_to_dulms(driver, username, password, captcha_api_key)
        if not login_success:
            result["message"] = "Failed to login to DULMS"
            return result
        
        # Scrape assignments
        result["assignments"] = scrape_assignments(driver)
        
        # Scrape quizzes
        result["quizzes"] = scrape_quizzes(driver)
        
        # Mark as successful
        result["success"] = True
        result["message"] = "Scraping completed successfully"
        
        # Send Discord notification if webhook is provided
        if discord_webhook:
            # Filter for upcoming deadlines
            deadline_threshold = settings.DEADLINE_THRESHOLD_DAYS
            
            upcoming_assignments = [
                a for a in result["assignments"]
                if a.get("days_remaining") is not None and a.get("days_remaining") <= deadline_threshold
            ]
            
            upcoming_quizzes = [
                q for q in result["quizzes"]
                if q.get("days_remaining") is not None and q.get("days_remaining") <= deadline_threshold
            ]
            
            # Only send notification if there are upcoming deadlines
            if upcoming_assignments or upcoming_quizzes:
                content = "🚨 **DULMS Upcoming Deadlines Alert** 🚨"
                
                # Create embeds for assignments and quizzes
                embeds = []
                
                if upcoming_assignments:
                    embeds.extend(format_discord_embeds_for_assignments(upcoming_assignments))
                    
                if upcoming_quizzes:
                    embeds.extend(format_discord_embeds_for_quizzes(upcoming_quizzes))
                
                # Send the notification
                send_discord_webhook(discord_webhook, content, embeds)
        
        return result
        
    except Exception as e:
        error_msg = f"Scraper failed with error: {str(e)}"
        logger.error(error_msg)
        traceback.print_exc()
        
        result["success"] = False
        result["message"] = error_msg
        return result
        
    finally:
        # Clean up the driver
        if driver:
            try:
                driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
