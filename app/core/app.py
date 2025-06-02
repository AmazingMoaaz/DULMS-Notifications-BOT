"""
Core application setup.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.config import settings
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Setup and teardown for the application.
    """
    # Setup
    setup_logging()
    logger.info("Application starting...")
    
    yield
    
    # Teardown
    logger.info("Application shutting down...")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json"
    )
    
    # Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Mount static files if frontend directory exists
    try:
        app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")
        logger.info(f"Mounted static files from {settings.STATIC_DIR}")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")
    
    return app
