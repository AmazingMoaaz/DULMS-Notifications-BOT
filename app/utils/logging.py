"""
Logging utility functions.
"""
import logging
import queue
import sys
from pathlib import Path
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler

from app.config import settings


def setup_logging():
    """
    Configure basic logging for the application.
    """
    # Create logs directory if it doesn't exist
    settings.LOG_DIR.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove any existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        settings.LOG_FILE, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] - %(message)s')
    file_handler.setFormatter(file_format)
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def setup_task_queue_logging(task_id):
    """
    Set up a queue-based logging system for a specific task.
    Returns both the logger and the queue for the consumer to use.
    """
    # Create a queue for log messages
    log_queue = queue.Queue()
    
    # Create a logger for this task
    task_logger = logging.getLogger(f"task.{task_id}")
    task_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove any existing handlers to avoid duplicates
    for handler in task_logger.handlers[:]:
        task_logger.removeHandler(handler)
    
    # Add a queue handler to the logger
    queue_handler = QueueHandler(log_queue)
    task_logger.addHandler(queue_handler)
    
    return task_logger, log_queue
