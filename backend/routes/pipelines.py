"""
Pipeline REST API Routes
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from services import pipeline_service

router = APIRouter()
logger = logging.getLogger("autoheal.routes.pipelines")


@router.get("/")
async def list_pipelines(
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    repo: Optional[str] = None,
    status: Optional[str] = None,
):
    """List pipeline runs with optional filtering"""
    runs = await pipeline_service.list_pipeline_runs(
        limit=limit, skip=skip, repo=repo, status=status
    )
    return {"runs": runs, "count": len(runs)}


@router.get("/{run_id}")
async def get_pipeline(run_id: str):
    """Get details for a specific pipeline run"""
    run = await pipeline_service.get_pipeline_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found")
    return run


@router.get("/{run_id}/logs")
async def get_pipeline_logs(run_id: str):
    """Get raw logs for a pipeline run"""
    run = await pipeline_service.get_pipeline_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found")
    return {
        "run_id": run_id,
        "logs": run.get("raw_logs", "No logs available"),
        "failure_type": run.get("failure_type"),
        "failure_message": run.get("failure_message"),
    }


@router.get("/{run_id}/healing")
async def get_healing_actions(run_id: str):
    """Get healing actions taken for a pipeline run"""
    run = await pipeline_service.get_pipeline_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found")
    return {
        "run_id": run_id,
        "healed": run.get("healed", False),
        "status": run.get("status"),
        "healing_actions": run.get("healing_actions", []),
    }
