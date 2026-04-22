"""
Health Check Routes
"""
from datetime import datetime
from fastapi import APIRouter
from utils.database import get_db

router = APIRouter()


@router.get("/")
async def health_check():
    db_status = "unknown"
    try:
        db = get_db()
        await db.pipeline_runs.count_documents({})
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "service": "AutoHeal CI/CD Pipeline System",
    }
