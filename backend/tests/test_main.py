"""
Backend Tests — pytest
Run: cd backend && pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture(scope="module")
def client():
    from main import app
    with TestClient(app) as c:
        yield c


class TestHealth:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["service"] == "AutoHeal CI/CD Pipeline System"

    def test_health_endpoint(self, client):
        r = client.get("/api/health/")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert "timestamp" in data


class TestWebhook:
    def test_test_failure_endpoint(self, client):
        r = client.post("/api/webhook/test-failure")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "accepted"
        assert "run_id" in data

    def test_pipeline_failure_webhook(self, client):
        payload = {
            "run_id": "test-run-001",
            "repo": "test-org/test-repo",
            "branch": "main",
            "commit_sha": "abc123",
            "workflow_name": "CI",
            "status": "failure",
            "logs": "ModuleNotFoundError: No module named 'requests'",
            "actor": "test-user",
            "metadata": {},
        }
        r = client.post("/api/webhook/pipeline-failure", json=payload)
        assert r.status_code == 200
        assert r.json()["status"] == "accepted"

    def test_github_webhook_ignored_event(self, client):
        r = client.post(
            "/api/webhook/github",
            json={"action": "requested"},
            headers={"x-github-event": "push"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "ignored"


class TestLogAnalyzer:
    def test_detect_dependency_error(self):
        from services.log_analyzer import analyze_logs
        from models.pipeline import FailureType

        logs = "ModuleNotFoundError: No module named 'requests'"
        ft, msg, conf = analyze_logs(logs)
        assert ft == FailureType.DEPENDENCY_ERROR
        assert conf > 0.0

    def test_detect_test_failure(self):
        from services.log_analyzer import analyze_logs
        from models.pipeline import FailureType

        logs = "FAILED tests/test_api.py::test_create - AssertionError: assert 422 == 201\n2 failed, 1 passed"
        ft, msg, conf = analyze_logs(logs)
        assert ft == FailureType.TEST_FAILURE

    def test_detect_build_error(self):
        from services.log_analyzer import analyze_logs
        from models.pipeline import FailureType

        logs = "Build failed\nSyntaxError: invalid syntax at line 5\nCompilation failed"
        ft, msg, conf = analyze_logs(logs)
        assert ft == FailureType.BUILD_ERROR

    def test_detect_timeout(self):
        from services.log_analyzer import analyze_logs
        from models.pipeline import FailureType

        logs = "Error: Job was cancelled after timeout of 6 hours\nSIGTERM received"
        ft, msg, conf = analyze_logs(logs)
        assert ft == FailureType.TIMEOUT

    def test_empty_logs(self):
        from services.log_analyzer import analyze_logs
        from models.pipeline import FailureType

        ft, msg, conf = analyze_logs("")
        assert ft == FailureType.UNKNOWN

    def test_log_stats(self):
        from services.log_analyzer import get_log_stats

        logs = "line 1\nERROR: something failed\nWARN: deprecated\nTraceback (most recent call last):"
        stats = get_log_stats(logs)
        assert stats["total_lines"] == 4
        assert stats["error_lines"] >= 1
        assert stats["warning_lines"] >= 1
        assert stats["has_stack_trace"] is True


class TestMLPredictor:
    def test_predictor_loads(self):
        from services.ml_predictor import get_predictor
        predictor = get_predictor()
        assert predictor is not None

    def test_predict_dependency(self):
        from services.ml_predictor import get_predictor
        predictor = get_predictor()
        if predictor.is_ready:
            label, conf = predictor.predict("ModuleNotFoundError: No module named requests")
            assert label in ["dependency_error", "build_error", "unknown"]

    def test_predict_test_failure(self):
        from services.ml_predictor import get_predictor
        predictor = get_predictor()
        if predictor.is_ready:
            label, conf = predictor.predict("FAILED tests/test_api.py - AssertionError 2 failed")
            assert conf >= 0.0


class TestAnalyticsAPI:
    def test_analytics_summary(self, client):
        r = client.get("/api/analytics/summary")
        assert r.status_code == 200
        data = r.json()
        assert "total_runs" in data
        assert "heal_success_rate" in data
        assert "failure_type_breakdown" in data
        assert "daily_stats" in data


class TestPipelinesAPI:
    def test_list_pipelines(self, client):
        r = client.get("/api/pipelines/")
        assert r.status_code == 200
        data = r.json()
        assert "runs" in data
        assert "count" in data

    def test_get_nonexistent_pipeline(self, client):
        r = client.get("/api/pipelines/nonexistent-run-99999")
        assert r.status_code == 404
