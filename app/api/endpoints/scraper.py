"""
Scraper API endpoints.
"""
import logging
import asyncio
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from typing import Optional, Dict, Any

from app.models.schemas import ScraperInput, TaskResult, TaskStatus
from app.services.task_manager import (
    create_scraper_task,
    run_scraper_task,
    get_task_status,
    get_task_result,
    get_task_logs
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/scrape", response_model=Dict[str, str])
async def start_scraper(
    input_data: ScraperInput,
    background_tasks: BackgroundTasks
):
    """
    Start a scraping task for DULMS.
    """
    try:
        # Create a new task
        task_id = create_scraper_task(
            username=input_data.username,
            password=input_data.password,
            captcha_api_key=input_data.captcha_api_key,
            discord_webhook=input_data.discord_webhook
        )
        
        # Run the task in the background
        background_tasks.add_task(
            run_scraper_task,
            task_id=task_id,
            username=input_data.username,
            password=input_data.password,
            captcha_api_key=input_data.captcha_api_key,
            discord_webhook=input_data.discord_webhook
        )
        
        return {"task_id": task_id, "status": "started"}
        
    except Exception as e:
        logger.error(f"Failed to start scraper task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start scraper task: {str(e)}")


@router.get("/status/{task_id}", response_model=TaskResult)
async def get_task_info(task_id: str):
    """
    Get the status and result of a task.
    """
    # Get the task status
    status = get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Create response
    response = {
        "task_id": task_id,
        "status": status
    }
    
    # Add result data if task is completed
    if status == TaskStatus.COMPLETED:
        result_data = get_task_result(task_id)
        if result_data:
            response["assignments"] = result_data.get("assignments", [])
            response["quizzes"] = result_data.get("quizzes", [])
            response["message"] = result_data.get("message", "Task completed")
    elif status == TaskStatus.ERROR:
        # Add error message if task failed
        result_data = get_task_result(task_id)
        if result_data:
            response["error"] = result_data.get("message", "Unknown error")
    
    return response


async def event_generator(request: Request, task_id: str):
    """
    Generate server-sent events for task logs.
    """
    while True:
        if await request.is_disconnected():
            logger.info(f"Client disconnected from SSE stream for task {task_id}")
            break
            
        # Get new logs
        logs = get_task_logs(task_id)
        
        # Send logs as events
        if logs:
            for log in logs:
                yield {
                    "event": "log",
                    "data": log
                }
                
        # Get current status
        status = get_task_status(task_id)
        
        # Check if task is finished
        if status in [TaskStatus.COMPLETED, TaskStatus.ERROR]:
            # Send completion event
            yield {
                "event": "status",
                "data": {"status": status}
            }
            
            # If completed, also send the result
            if status == TaskStatus.COMPLETED:
                result = get_task_result(task_id)
                if result:
                    yield {
                        "event": "result",
                        "data": result
                    }
                    
            break
        
        # Wait before polling again
        await asyncio.sleep(1)


@router.get("/logs/{task_id}")
async def stream_task_logs(request: Request, task_id: str):
    """
    Stream task logs as server-sent events.
    """
    status = get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    # Return Server-Sent Events response
    return EventSourceResponse(event_generator(request, task_id))
