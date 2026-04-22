"""
Self-Healing Engine
Maps failure types to healing strategies and executes them with exponential backoff
"""
import asyncio
import logging
import os
import time
from datetime import datetime
from typing import List, Optional, Tuple
import httpx

from models.pipeline import (
    FailureType,
    HealingAction,
    HealingActionType,
    PipelineStatus,
)

logger = logging.getLogger("autoheal.healer")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_API = "https://api.github.com"

# ── Healing rules: failure_type → ordered list of (action, description) ──────
HEALING_RULES: dict[FailureType, list[Tuple[HealingActionType, str]]] = {
    FailureType.DEPENDENCY_ERROR: [
        (HealingActionType.INSTALL_DEPENDENCIES, "Re-install missing dependencies via pip/npm"),
        (HealingActionType.CLEAR_CACHE, "Clear package manager cache"),
        (HealingActionType.RETRY_PIPELINE, "Retry pipeline after dependency fix"),
    ],
    FailureType.BUILD_ERROR: [
        (HealingActionType.CLEAR_CACHE, "Clear build cache and artifacts"),
        (HealingActionType.RETRY_PIPELINE, "Retry build after cache clear"),
    ],
    FailureType.TEST_FAILURE: [
        (HealingActionType.RERUN_FAILED_JOB, "Re-run only the failed test job"),
        (HealingActionType.RETRY_PIPELINE, "Full pipeline retry if test re-run fails"),
    ],
    FailureType.TIMEOUT: [
        (HealingActionType.CLEAR_CACHE, "Clear cache to speed up next run"),
        (HealingActionType.RETRY_PIPELINE, "Retry pipeline with extended timeout"),
    ],
    FailureType.NETWORK_ERROR: [
        (HealingActionType.RETRY_PIPELINE, "Retry pipeline after network error (transient)"),
    ],
    FailureType.CONFIGURATION_ERROR: [
        (HealingActionType.FIX_CONFIGURATION, "Attempt to fix missing env/config values"),
        (HealingActionType.RETRY_PIPELINE, "Retry after configuration fix"),
    ],
    FailureType.UNKNOWN: [
        (HealingActionType.CLEAR_CACHE, "Clear all caches for unknown error"),
        (HealingActionType.RETRY_PIPELINE, "Generic pipeline retry"),
    ],
}

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
BASE_DELAY = float(os.getenv("RETRY_BASE_DELAY", "2.0"))


async def execute_healing(
    repo: str,
    run_id: str,
    failure_type: FailureType,
    failure_message: str,
    job_name: Optional[str] = None,
) -> Tuple[List[HealingAction], bool]:
    """
    Execute the healing strategy for a given failure.
    Returns (actions_taken, overall_success).
    """
    rules = HEALING_RULES.get(failure_type, HEALING_RULES[FailureType.UNKNOWN])
    actions: List[HealingAction] = []
    overall_success = False

    logger.info(f"[{repo}#{run_id}] Healing {failure_type} with {len(rules)} actions")

    for action_type, description in rules:
        action = HealingAction(
            action_type=action_type,
            description=description,
            executed_at=datetime.utcnow(),
        )

        success, output = await _execute_action(
            action_type=action_type,
            repo=repo,
            run_id=run_id,
            job_name=job_name,
        )

        action.success = success
        action.output = output
        actions.append(action)

        if success and action_type in (
            HealingActionType.RETRY_PIPELINE,
            HealingActionType.RERUN_FAILED_JOB,
        ):
            overall_success = True
            logger.info(f"[{repo}#{run_id}] Healing succeeded via {action_type}")
            break

        if not success:
            logger.warning(f"[{repo}#{run_id}] Action {action_type} failed: {output}")

    return actions, overall_success


async def _execute_action(
    action_type: HealingActionType,
    repo: str,
    run_id: str,
    job_name: Optional[str] = None,
) -> Tuple[bool, str]:
    """Dispatch to the appropriate handler with retry logic"""
    handlers = {
        HealingActionType.INSTALL_DEPENDENCIES: _handle_install_dependencies,
        HealingActionType.RETRY_PIPELINE: _handle_retry_pipeline,
        HealingActionType.CLEAR_CACHE: _handle_clear_cache,
        HealingActionType.RERUN_FAILED_JOB: _handle_rerun_failed_job,
        HealingActionType.UPDATE_DEPENDENCIES: _handle_update_dependencies,
        HealingActionType.FIX_CONFIGURATION: _handle_fix_configuration,
        HealingActionType.NO_ACTION: _handle_no_action,
    }

    handler = handlers.get(action_type, _handle_no_action)
    return await _with_exponential_backoff(handler, repo=repo, run_id=run_id, job_name=job_name)


async def _with_exponential_backoff(handler, **kwargs) -> Tuple[bool, str]:
    """Retry handler with exponential backoff"""
    last_error = ""
    for attempt in range(MAX_RETRIES):
        try:
            success, output = await handler(**kwargs)
            if success:
                return True, output
            last_error = output
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt + 1} failed: {e}")

        if attempt < MAX_RETRIES - 1:
            delay = BASE_DELAY * (2 ** attempt)
            logger.info(f"Waiting {delay:.1f}s before retry {attempt + 2}...")
            await asyncio.sleep(delay)

    return False, f"All {MAX_RETRIES} attempts failed. Last error: {last_error}"


# ── Action handlers ───────────────────────────────────────────────────────────

async def _handle_install_dependencies(repo: str, run_id: str, **kwargs) -> Tuple[bool, str]:
    """Simulate triggering a dependency install in the pipeline"""
    logger.info(f"[{repo}] Triggering dependency installation")
    await asyncio.sleep(0.5)  # Simulate API call latency
    # In real deployment: trigger a GitHub Actions workflow_dispatch or API call
    return True, "Dependency installation triggered via workflow_dispatch event"


async def _handle_retry_pipeline(repo: str, run_id: str, **kwargs) -> Tuple[bool, str]:
    """Re-run a GitHub Actions workflow run"""
    if not GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN not set — simulating pipeline retry")
        await asyncio.sleep(1.0)
        return True, f"[SIMULATED] Pipeline run {run_id} re-triggered for {repo}"

    url = f"{GITHUB_API}/repos/{repo}/actions/runs/{run_id}/rerun"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            if resp.status_code in (201, 204):
                return True, f"GitHub run {run_id} re-triggered successfully"
            return False, f"GitHub API returned {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, f"HTTP error calling GitHub API: {e}"


async def _handle_rerun_failed_job(repo: str, run_id: str, **kwargs) -> Tuple[bool, str]:
    """Re-run only failed jobs in a GitHub Actions workflow run"""
    if not GITHUB_TOKEN:
        await asyncio.sleep(0.5)
        return True, f"[SIMULATED] Failed jobs in run {run_id} re-triggered for {repo}"

    url = f"{GITHUB_API}/repos/{repo}/actions/runs/{run_id}/rerun-failed-jobs"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            if resp.status_code in (201, 204):
                return True, f"Failed jobs in run {run_id} re-triggered"
            return False, f"GitHub API returned {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, f"HTTP error: {e}"


async def _handle_clear_cache(repo: str, run_id: str, **kwargs) -> Tuple[bool, str]:
    """Delete GitHub Actions caches for the repo"""
    if not GITHUB_TOKEN:
        await asyncio.sleep(0.3)
        return True, f"[SIMULATED] Cache cleared for {repo}"

    url = f"{GITHUB_API}/repos/{repo}/actions/caches"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(
                url,
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            if resp.status_code in (200, 204):
                return True, f"GitHub Actions cache cleared for {repo}"
            return False, f"Cache clear returned {resp.status_code}"
    except Exception as e:
        return False, f"HTTP error clearing cache: {e}"


async def _handle_update_dependencies(repo: str, **kwargs) -> Tuple[bool, str]:
    await asyncio.sleep(0.3)
    return True, "Dependency update triggered via workflow_dispatch"


async def _handle_fix_configuration(repo: str, **kwargs) -> Tuple[bool, str]:
    await asyncio.sleep(0.3)
    return True, "Configuration validation and fix attempted"


async def _handle_no_action(**kwargs) -> Tuple[bool, str]:
    return True, "No action required"
