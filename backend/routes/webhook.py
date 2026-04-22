"""
Webhook Routes
Receives GitHub Actions failure events and triggers self-healing
"""
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request

from models.pipeline import (
    FailureType,
    GitHubWorkflowPayload,
    HealingAction,
    PipelineRun,
    PipelineStatus,
)
from services import healing_engine, log_analyzer, pipeline_service
from services.ml_predictor import get_predictor

router = APIRouter()
logger = logging.getLogger("autoheal.webhook")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


def _verify_signature(payload: bytes, signature: str) -> bool:
    if not WEBHOOK_SECRET:
        return True  # Skip verification if secret not configured
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")


@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(default=""),
    x_github_event: str = Header(default=""),
):
    """Receive native GitHub Actions webhook events"""
    body = await request.body()

    if WEBHOOK_SECRET and not _verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = x_github_event
    action = payload.get("action", "")

    logger.info(f"Received GitHub event: {event_type} action={action}")

    # Handle workflow_run completed with failure
    if event_type == "workflow_run" and action == "completed":
        workflow_run = payload.get("workflow_run", {})
        conclusion = workflow_run.get("conclusion", "")
        if conclusion == "failure":
            background_tasks.add_task(_process_github_workflow_failure, payload)
            return {"status": "accepted", "message": "Healing process initiated"}

    # Handle workflow_job failed
    if event_type == "workflow_job" and action in ("completed",):
        job = payload.get("workflow_job", {})
        if job.get("conclusion") == "failure":
            background_tasks.add_task(_process_github_job_failure, payload)
            return {"status": "accepted", "message": "Job failure processing initiated"}

    return {"status": "ignored", "event": event_type, "action": action}


@router.post("/pipeline-failure")
async def pipeline_failure_webhook(
    payload: GitHubWorkflowPayload,
    background_tasks: BackgroundTasks,
):
    """
    Generic webhook endpoint for custom pipeline failure events.
    Can be called from GitHub Actions steps directly.
    """
    logger.info(f"Pipeline failure received: {payload.repo} run={payload.run_id}")
    background_tasks.add_task(_process_generic_failure, payload)
    return {
        "status": "accepted",
        "run_id": payload.run_id,
        "message": "Self-healing process initiated",
    }


@router.post("/test-failure")
async def test_failure_endpoint(background_tasks: BackgroundTasks):
    """Test endpoint to simulate a pipeline failure for demo purposes"""
    from models.pipeline import GitHubWorkflowPayload

    sample_logs = """
Run python -m pytest tests/
============= test session starts ==============
collected 12 items

tests/test_api.py::test_health PASSED
tests/test_api.py::test_create_user FAILED
tests/test_api.py::test_get_user FAILED

============= FAILURES =============
FAILED tests/test_api.py::test_create_user - AssertionError: assert 422 == 201
FAILED tests/test_api.py::test_get_user - AssertionError: assert 404 == 200
============= 2 failed, 1 passed in 3.14s =============
"""
    payload = GitHubWorkflowPayload(
        run_id=f"demo-{int(datetime.utcnow().timestamp())}",
        repo="demo-org/autoheal-demo",
        branch="main",
        commit_sha="abc123def456",
        workflow_name="CI",
        job_name="test",
        status="failure",
        logs=sample_logs,
        actor="demo-user",
    )
    background_tasks.add_task(_process_generic_failure, payload)
    return {"status": "accepted", "run_id": payload.run_id, "message": "Demo failure triggered"}


# ── Background task processors ────────────────────────────────────────────────

async def _process_github_workflow_failure(payload: dict):
    """Process a native GitHub workflow_run failure event"""
    try:
        wr = payload.get("workflow_run", {})
        repo_data = payload.get("repository", {})

        generic = GitHubWorkflowPayload(
            run_id=str(wr.get("id", "")),
            repo=repo_data.get("full_name", "unknown/repo"),
            branch=wr.get("head_branch", "main"),
            commit_sha=wr.get("head_sha", ""),
            workflow_name=wr.get("name", "CI"),
            status="failure",
            actor=wr.get("triggering_actor", {}).get("login", "unknown"),
        )
        await _process_generic_failure(generic)
    except Exception as e:
        logger.error(f"Error processing GitHub workflow failure: {e}", exc_info=True)


async def _process_github_job_failure(payload: dict):
    """Process a native GitHub workflow_job failure event"""
    try:
        job = payload.get("workflow_job", {})
        repo_data = payload.get("repository", {})
        wr = payload.get("workflow_run", {})

        generic = GitHubWorkflowPayload(
            run_id=str(job.get("run_id", job.get("id", ""))),
            repo=repo_data.get("full_name", "unknown/repo"),
            branch=wr.get("head_branch", "main") if wr else "main",
            commit_sha=job.get("head_sha", ""),
            workflow_name=job.get("workflow_name", "CI"),
            job_name=job.get("name"),
            status="failure",
        )
        await _process_generic_failure(generic)
    except Exception as e:
        logger.error(f"Error processing GitHub job failure: {e}", exc_info=True)


async def _process_generic_failure(payload: GitHubWorkflowPayload):
    """Core healing pipeline"""
    try:
        # Check if already processed
        existing = await pipeline_service.get_pipeline_run(payload.run_id)
        if existing and existing.get("status") in (
            PipelineStatus.HEALING,
            PipelineStatus.HEALED,
        ):
            logger.info(f"Run {payload.run_id} already being healed, skipping")
            return

        # 1. Store initial run record
        run = PipelineRun(
            run_id=payload.run_id,
            repo=payload.repo,
            branch=payload.branch,
            commit_sha=payload.commit_sha,
            workflow_name=payload.workflow_name,
            job_name=payload.job_name,
            status=PipelineStatus.FAILURE,
            raw_logs=payload.logs,
            actor=payload.actor,
        )
        await pipeline_service.create_pipeline_run(run)

        # 2. Analyze logs
        failure_type = FailureType.UNKNOWN
        failure_message = "No logs provided"

        if payload.logs:
            # Try ML prediction first
            predictor = get_predictor()
            if predictor.is_ready:
                ml_label, ml_confidence = predictor.predict(payload.logs)
                if ml_confidence > 0.6:
                    try:
                        failure_type = FailureType(ml_label)
                        failure_message = f"ML predicted: {ml_label} ({ml_confidence:.0%} confidence)"
                        logger.info(f"ML prediction used: {ml_label} @ {ml_confidence:.2f}")
                    except ValueError:
                        pass

            # Fall back to rule-based analyzer
            if failure_type == FailureType.UNKNOWN:
                ft, msg, conf = log_analyzer.analyze_logs(payload.logs)
                failure_type = ft
                failure_message = msg

        await pipeline_service.update_pipeline_run(
            payload.run_id,
            {
                "failure_type": failure_type,
                "failure_message": failure_message,
                "status": PipelineStatus.HEALING,
            },
        )

        logger.info(f"[{payload.repo}] Failure detected: {failure_type} — starting healing")

        # 3. Execute healing
        actions, healed = await healing_engine.execute_healing(
            repo=payload.repo,
            run_id=payload.run_id,
            failure_type=failure_type,
            failure_message=failure_message,
            job_name=payload.job_name,
        )

        # 4. Persist actions and update status
        for action in actions:
            await pipeline_service.append_healing_action(payload.run_id, action)

        final_status = PipelineStatus.HEALED if healed else PipelineStatus.FAILED_HEALING
        await pipeline_service.update_pipeline_run(
            payload.run_id,
            {
                "status": final_status,
                "healed": healed,
                "updated_at": datetime.utcnow(),
            },
        )

        logger.info(
            f"[{payload.repo}#{payload.run_id}] Healing complete: "
            f"{'SUCCESS' if healed else 'FAILED'} — "
            f"{len(actions)} actions taken"
        )

    except Exception as e:
        logger.error(f"Healing pipeline error: {e}", exc_info=True)
        try:
            await pipeline_service.update_pipeline_run(
                payload.run_id,
                {"status": PipelineStatus.FAILED_HEALING, "failure_message": str(e)},
            )
        except Exception:
            pass
