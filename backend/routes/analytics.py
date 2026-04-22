"""
Analytics API Routes
"""
import logging
from fastapi import APIRouter
from services import pipeline_service

router = APIRouter()
logger = logging.getLogger("autoheal.routes.analytics")


@router.get("/summary")
async def get_analytics_summary():
    """Get aggregated analytics for the dashboard"""
    return await pipeline_service.get_analytics()
