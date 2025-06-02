"""
Configuration settings for the DULMS Notifications Bot.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent  # Project root
APP_DIR = BASE_DIR / "app"
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

# Log settings
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Driver settings
DRIVER_PATH = os.getenv("DRIVER_PATH", str(BASE_DIR / "msedgedriver.exe"))
HEADLESS_MODE = os.getenv("HEADLESS_MODE", "True").lower() == "true"

# DULMS URLs
LOGIN_URL = "https://dulms.deltauniv.edu.eg/Login.aspx"
QUIZZES_URL = "https://dulms.deltauniv.edu.eg/Quizzes/StudentQuizzes"
ASSIGNMENTS_URL = "https://dulms.deltauniv.edu.eg/Assignment/AssignmentStudentList"
LOGIN_SUCCESS_URL_PART = "Profile/StudentProfile"

# Scraper settings
DEADLINE_THRESHOLD_DAYS = int(os.getenv("DEADLINE_THRESHOLD_DAYS", "3"))
MAX_LOGIN_RETRIES = int(os.getenv("MAX_LOGIN_RETRIES", "3"))
CAPTCHA_SOLVE_RETRIES = int(os.getenv("CAPTCHA_SOLVE_RETRIES", "3"))
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "20"))
POLL_FREQUENCY = float(os.getenv("POLL_FREQUENCY", "0.2"))

# API settings
API_V1_STR = "/api/v1"
PROJECT_NAME = "DULMS Notifications Bot"

# Create necessary directories if they don't exist
LOG_DIR.mkdir(exist_ok=True)
