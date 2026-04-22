"""
Seed Script — Populate AutoHeal with realistic demo data
Run: python seed.py
"""
import asyncio
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "autoheal"

REPOS = [
    "acme-corp/api-service",
    "acme-corp/frontend-app",
    "acme-corp/data-pipeline",
    "acme-corp/auth-service",
]
BRANCHES = ["main", "develop", "feature/user-auth", "feature/payments", "hotfix/memory-leak"]
WORKFLOWS = ["CI", "Deploy to Staging", "Run Tests", "Build & Publish"]
ACTORS = ["alice", "bob", "carol", "dave", "eve"]

FAILURE_TYPES = [
    "dependency_error",
    "test_failure",
    "build_error",
    "timeout",
    "network_error",
    "configuration_error",
    "unknown",
]
STATUSES_WEIGHTED = ["healed"] * 6 + ["failed_healing"] * 2 + ["failure"] * 1 + ["success"] * 3

ACTION_TYPES_BY_FAILURE = {
    "dependency_error": ["install_dependencies", "clear_cache", "retry_pipeline"],
    "test_failure": ["rerun_failed_job", "retry_pipeline"],
    "build_error": ["clear_cache", "retry_pipeline"],
    "timeout": ["clear_cache", "retry_pipeline"],
    "network_error": ["retry_pipeline"],
    "configuration_error": ["fix_configuration", "retry_pipeline"],
    "unknown": ["clear_cache", "retry_pipeline"],
}

SAMPLE_LOGS = {
    "dependency_error": """
Run pip install -r requirements.txt
Collecting requests==2.28.0
ERROR: Could not find a version that satisfies the requirement nonexistent-pkg==99.0 (from versions: none)
ERROR: No matching distribution found for nonexistent-pkg==99.0
ModuleNotFoundError: No module named 'nonexistent_pkg'
Process completed with exit code 1.
""",
    "test_failure": """
Run python -m pytest tests/ -v
collected 15 items
tests/test_api.py::test_health PASSED
tests/test_api.py::test_create_user FAILED
tests/test_api.py::test_get_user FAILED
FAILURES
FAILED tests/test_api.py::test_create_user - AssertionError: assert 422 == 201
FAILED tests/test_api.py::test_get_user - AssertionError: assert 404 == 200
2 failed, 13 passed in 4.21s
""",
    "build_error": """
Run npm run build
> react-scripts build
Creating an optimized production build...
Failed to compile.
SyntaxError: /src/components/App.js: Unexpected token (42:8)
TypeError: Cannot read properties of undefined (reading 'map')
Build failed with exit code 1.
""",
    "timeout": """
Run pytest tests/ --timeout=300
Test session starts
...running long integration tests...
ERROR: timeout exceeded (300s) — canceling statement due to statement timeout
Job was cancelled after 6 hours
Process completed with exit code 1.
""",
    "network_error": """
Run npm install
npm WARN saveError ENOENT: no such file or directory
npm ERR! code ECONNREFUSED
npm ERR! errno ECONNREFUSED
npm ERR! network request to https://registry.npmjs.org failed
ECONNREFUSED 127.0.0.1:4873
""",
}


def make_actions(failure_type: str, healed: bool):
    action_types = ACTION_TYPES_BY_FAILURE.get(failure_type, ["retry_pipeline"])
    actions = []
    for i, at in enumerate(action_types):
        is_last = i == len(action_types) - 1
        success = healed if is_last else True
        actions.append({
            "action_type": at,
            "description": f"Auto-healing: {at.replace('_', ' ')}",
            "executed_at": datetime.utcnow() - timedelta(seconds=len(action_types) - i),
            "success": success,
            "output": f"[SIMULATED] {at} executed successfully" if success else "Action failed after 3 retries",
            "retry_count": 0 if success else 3,
        })
    return actions


async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Clear existing data
    await db.pipeline_runs.delete_many({})
    print("Cleared existing pipeline_runs")

    runs = []
    now = datetime.utcnow()

    for i in range(60):
        created_at = now - timedelta(
            days=random.uniform(0, 7),
            hours=random.uniform(0, 23),
            minutes=random.uniform(0, 59),
        )
        status = random.choice(STATUSES_WEIGHTED)
        failure_type = None
        healing_actions = []
        healed = False
        failure_message = None

        if status in ("healed", "failed_healing", "failure"):
            failure_type = random.choice(FAILURE_TYPES)
            healed = status == "healed"
            failure_message = f"Detected: {failure_type.replace('_', ' ')}"
            if status in ("healed", "failed_healing"):
                healing_actions = make_actions(failure_type, healed)

        run = {
            "run_id": f"demo-{10000 + i}",
            "repo": random.choice(REPOS),
            "branch": random.choice(BRANCHES),
            "commit_sha": f"{random.randint(0, 0xFFFFFF):06x}{random.randint(0, 0xFFFFFF):06x}",
            "workflow_name": random.choice(WORKFLOWS),
            "job_name": random.choice(["build", "test", "lint", "deploy"]),
            "status": status,
            "failure_type": failure_type,
            "failure_message": failure_message,
            "raw_logs": SAMPLE_LOGS.get(failure_type, "No logs available.") if failure_type else "All steps passed.",
            "healing_actions": healing_actions,
            "created_at": created_at,
            "updated_at": created_at + timedelta(seconds=random.randint(30, 180)),
            "healed": healed,
            "retry_count": random.randint(0, 3) if healing_actions else 0,
            "triggered_by": "github_actions",
            "actor": random.choice(ACTORS),
            "metadata": {},
        }
        runs.append(run)

    await db.pipeline_runs.insert_many(runs)
    total = len(runs)
    healed_count = sum(1 for r in runs if r["healed"])
    print(f"Seeded {total} pipeline runs ({healed_count} healed, {total - healed_count} other)")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
