"""
Pydantic models for data validation and serialization.
"""
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional, List, Dict, Any, Union
from enum import Enum


class TaskStatus(str, Enum):
    """Enum for task status values."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class ScraperInput(BaseModel):
    """Input model for the scraper endpoint."""
    username: str
    password: str
    captcha_api_key: str
    discord_webhook: Optional[str] = None


class LogMessage(BaseModel):
    """Model for log messages."""
    timestamp: str
    level: str
    message: str


class AssignmentData(BaseModel):
    """Model for assignment data."""
    id: str
    title: str
    course: str
    deadline: str
    days_remaining: int
    status: str
    url: str


class QuizData(BaseModel):
    """Model for quiz data."""
    id: str
    title: str
    course: str
    deadline: str
    days_remaining: int
    status: str
    url: str


class TaskResult(BaseModel):
    """Model for task result."""
    task_id: str
    status: TaskStatus
    message: Optional[str] = None
    assignments: Optional[List[AssignmentData]] = None
    quizzes: Optional[List[QuizData]] = None
    error: Optional[str] = None


class ServerSentEvent(BaseModel):
    """Model for server-sent events."""
    event: Optional[str] = None
    data: str
    id: Optional[str] = None
    retry: Optional[int] = None
