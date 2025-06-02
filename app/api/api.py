"""
API router that includes all endpoints.
"""
from fastapi import APIRouter
from app.api.endpoints import scraper

api_router = APIRouter()

# Include the scraper endpoints
api_router.include_router(scraper.router, prefix="/scraper", tags=["scraper"])
