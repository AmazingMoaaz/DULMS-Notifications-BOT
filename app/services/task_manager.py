"""
Task management service for background tasks.
"""
import logging
import uuid
import queue
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.scraper import run_dulms_scraper
from app.models.schemas import TaskStatus

# Storage for tasks
task_queues = {}  # Dictionary to hold log queues for each task {task_id: queue.Queue}
task_results = {}  # Dictionary to hold results {task_id: result_data_or_error}
task_statuses = {}  # Dictionary to track status {task_id: TaskStatus}

logger = logging.getLogger(__name__)


def generate_task_id() -> str:
    """
    Generate a unique task ID.
    
    Returns:
        A unique task ID string
    """
    return str(uuid.uuid4())


def create_scraper_task(username: str, password: str, captcha_api_key: str, discord_webhook: Optional[str] = None) -> str:
    """
    Create a new scraper task and set up its logging queue.
    
    Args:
        username: DULMS username
        password: DULMS password
        captcha_api_key: API key for captcha solving service
        discord_webhook: Optional Discord webhook URL
        
    Returns:
        The task ID
    """
    task_id = generate_task_id()
    
    # Create log queue for this task
    task_queues[task_id] = queue.Queue()
    
    # Set initial task status
    task_statuses[task_id] = TaskStatus.PENDING
    
    logger.info(f"Created scraper task with ID: {task_id}")
    
    return task_id


def run_scraper_task(task_id: str, username: str, password: str, captcha_api_key: str, discord_webhook: Optional[str] = None):
    """
    Run the scraper task in a background thread.
    
    Args:
        task_id: The task ID
        username: DULMS username
        password: DULMS password
        captcha_api_key: API key for captcha solving service
        discord_webhook: Optional Discord webhook URL
    """
    log_queue = task_queues.get(task_id)
    if not log_queue:
        logger.error(f"Log queue not found for task {task_id}")
        task_statuses[task_id] = TaskStatus.ERROR
        task_results[task_id] = {"message": "Log queue not found"}
        return
    
    # Update task status
    task_statuses[task_id] = TaskStatus.RUNNING
    logger.info(f"Starting background task for task_id: {task_id}")
    
    try:
        # Run the actual scraper function
        result_data = run_dulms_scraper(
            username=username,
            password=password,
            captcha_api_key=captcha_api_key,
            discord_webhook=discord_webhook,
            log_queue=log_queue
        )
        
        # Store results
        task_results[task_id] = result_data
        
        # Update task status
        if result_data.get("success", False):
            task_statuses[task_id] = TaskStatus.COMPLETED
            log_queue.put({
                "level": "INFO",
                "message": "Scraping task completed successfully",
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"Scraping task {task_id} completed successfully")
        else:
            task_statuses[task_id] = TaskStatus.ERROR
            log_queue.put({
                "level": "ERROR",
                "message": f"Scraping task failed: {result_data.get('message', 'Unknown error')}",
                "timestamp": datetime.now().isoformat()
            })
            logger.error(f"Scraping task {task_id} failed: {result_data.get('message')}")
            
    except Exception as e:
        logger.error(f"Scraping task {task_id} failed with exception: {e}", exc_info=True)
        task_statuses[task_id] = TaskStatus.ERROR
        
        # Store error details
        task_results[task_id] = {"message": f"An error occurred: {str(e)}"}
        
        # Log the error
        log_queue.put({
            "level": "ERROR",
            "message": f"Scraping task failed with exception: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


def get_task_status(task_id: str) -> Optional[str]:
    """
    Get the current status of a task.
    
    Args:
        task_id: The task ID
        
    Returns:
        The task status, or None if task not found
    """
    return task_statuses.get(task_id)


def get_task_result(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the result of a completed task.
    
    Args:
        task_id: The task ID
        
    Returns:
        The task result data, or None if task not found or not completed
    """
    return task_results.get(task_id)


def get_task_logs(task_id: str, clear: bool = False) -> list:
    """
    Get all logs for a task.
    
    Args:
        task_id: The task ID
        clear: Whether to clear the log queue after retrieval
        
    Returns:
        List of log messages
    """
    log_queue = task_queues.get(task_id)
    if not log_queue:
        return []
        
    logs = []
    
    # Get all messages currently in the queue
    try:
        while not log_queue.empty():
            logs.append(log_queue.get_nowait())
    except queue.Empty:
        pass
        
    return logs


def cleanup_old_tasks():
    """
    Clean up old tasks to prevent memory leaks.
    Should be called periodically.
    """
    # Implement task cleanup logic here
    pass
