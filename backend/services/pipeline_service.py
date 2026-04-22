"""
Pipeline Service
CRUD operations and business logic for pipeline runs
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from bson import ObjectId

from utils.database import get_db
from models.pipeline import (
    PipelineRun,
    PipelineStatus,
    FailureType,
    HealingAction,
)

logger = logging.getLogger("autoheal.pipeline_service")


def _serialize(doc: dict) -> dict:
    """Convert MongoDB ObjectId fields to strings for JSON serialization"""
    if doc is None:
        return None
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def create_pipeline_run(run: PipelineRun) -> dict:
    db = get_db()
    doc = run.model_dump()
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()
    result = await db.pipeline_runs.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    logger.info(f"Created pipeline run {run.run_id} for {run.repo}")
    return doc


async def get_pipeline_run(run_id: str) -> Optional[dict]:
    db = get_db()
    doc = await db.pipeline_runs.find_one({"run_id": run_id})
    return _serialize(doc)


async def update_pipeline_run(run_id: str, updates: dict) -> bool:
    db = get_db()
    updates["updated_at"] = datetime.utcnow()
    result = await db.pipeline_runs.update_one(
        {"run_id": run_id},
        {"$set": updates}
    )
    return True


async def append_healing_action(run_id: str, action: HealingAction) -> bool:
    db = get_db()
    await db.pipeline_runs.update_one(
        {"run_id": run_id},
        {
            "$push": {"healing_actions": action.model_dump()},
            "$set": {"updated_at": datetime.utcnow()},
        }
    )
    return True


async def list_pipeline_runs(
    limit: int = 50,
    skip: int = 0,
    repo: Optional[str] = None,
    status: Optional[str] = None,
) -> List[dict]:
    db = get_db()
    query: Dict[str, Any] = {}
    if repo:
        query["repo"] = repo
    if status:
        query["status"] = status

    cursor = db.pipeline_runs.find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_serialize(d) for d in docs]


async def get_analytics() -> dict:
    db = get_db()

    total = await db.pipeline_runs.count_documents({})
    healed = await db.pipeline_runs.count_documents({"status": PipelineStatus.HEALED})
    failed_heal = await db.pipeline_runs.count_documents({"status": PipelineStatus.FAILED_HEALING})
    failures = await db.pipeline_runs.count_documents({"status": PipelineStatus.FAILURE})
    successes = await db.pipeline_runs.count_documents({"status": PipelineStatus.SUCCESS})

    heal_rate = round(healed / max(healed + failed_heal, 1) * 100, 1)

    # Failure type breakdown
    failure_breakdown: Dict[str, int] = {ft.value: 0 for ft in FailureType}
    recent = await db.pipeline_runs.find({}).sort("created_at", -1).to_list(length=200)
    action_breakdown: Dict[str, int] = {}

    for run in recent:
        ft = run.get("failure_type")
        if ft and ft in failure_breakdown:
            failure_breakdown[ft] += 1
        for action in run.get("healing_actions", []):
            at = action.get("action_type", "unknown")
            action_breakdown[at] = action_breakdown.get(at, 0) + 1

    # 7-day trend
    now = datetime.utcnow()
    daily_stats = []
    for i in range(6, -1, -1):
        day_start = now - timedelta(days=i + 1)
        day_end = now - timedelta(days=i)
        day_total = sum(
            1 for r in recent
            if r.get("created_at") and day_start <= r["created_at"] <= day_end
        )
        day_healed = sum(
            1 for r in recent
            if r.get("created_at")
            and day_start <= r["created_at"] <= day_end
            and r.get("status") == PipelineStatus.HEALED
        )
        daily_stats.append({
            "date": day_end.strftime("%m/%d"),
            "total": day_total,
            "healed": day_healed,
            "failed": day_total - day_healed,
        })

    recent_runs = [
        {
            "run_id": r.get("run_id"),
            "repo": r.get("repo"),
            "branch": r.get("branch"),
            "status": r.get("status"),
            "failure_type": r.get("failure_type"),
            "healed": r.get("healed", False),
            "created_at": r.get("created_at").isoformat() if r.get("created_at") else None,
            "healing_actions_count": len(r.get("healing_actions", [])),
        }
        for r in recent[:10]
    ]

    return {
        "total_runs": total,
        "successful_heals": healed,
        "failed_heals": failed_heal,
        "total_failures": failures + healed + failed_heal,
        "total_successes": successes,
        "heal_success_rate": heal_rate,
        "failure_type_breakdown": failure_breakdown,
        "healing_action_breakdown": action_breakdown,
        "daily_stats": daily_stats,
        "recent_runs": recent_runs,
    }
