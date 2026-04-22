"""
Pydantic models for AutoHeal pipeline system
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    HEALING = "healing"
    HEALED = "healed"
    FAILED_HEALING = "failed_healing"


class FailureType(str, Enum):
    DEPENDENCY_ERROR = "dependency_error"
    TEST_FAILURE = "test_failure"
    BUILD_ERROR = "build_error"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN = "unknown"


class HealingActionType(str, Enum):
    INSTALL_DEPENDENCIES = "install_dependencies"
    RETRY_PIPELINE = "retry_pipeline"
    CLEAR_CACHE = "clear_cache"
    RERUN_FAILED_JOB = "rerun_failed_job"
    UPDATE_DEPENDENCIES = "update_dependencies"
    FIX_CONFIGURATION = "fix_configuration"
    NO_ACTION = "no_action"


class HealingAction(BaseModel):
    action_type: HealingActionType
    description: str
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    success: bool = False
    output: Optional[str] = None
    retry_count: int = 0


class PipelineRun(BaseModel):
    run_id: str
    repo: str
    branch: str
    commit_sha: str
    workflow_name: str
    status: PipelineStatus
    failure_type: Optional[FailureType] = None
    failure_message: Optional[str] = None
    raw_logs: Optional[str] = None
    healing_actions: List[HealingAction] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    healed: bool = False
    retry_count: int = 0
    triggered_by: str = "github_actions"
    job_name: Optional[str] = None
    actor: Optional[str] = None
    metadata: Dict[str, Any] = {}


class WebhookPayload(BaseModel):
    action: str
    workflow_run: Optional[Dict[str, Any]] = None
    workflow_job: Optional[Dict[str, Any]] = None
    repository: Optional[Dict[str, Any]] = None
    sender: Optional[Dict[str, Any]] = None


class GitHubWorkflowPayload(BaseModel):
    """Incoming webhook payload from GitHub Actions"""
    run_id: str
    repo: str
    branch: str
    commit_sha: str
    workflow_name: str
    job_name: Optional[str] = None
    status: str
    logs: Optional[str] = None
    actor: Optional[str] = None
    metadata: Dict[str, Any] = {}


class AnalyticsSummary(BaseModel):
    total_runs: int
    successful_heals: int
    failed_heals: int
    heal_success_rate: float
    failure_type_breakdown: Dict[str, int]
    healing_action_breakdown: Dict[str, int]
    recent_runs: List[Dict[str, Any]]
