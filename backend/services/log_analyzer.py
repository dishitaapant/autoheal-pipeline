"""
Log Analyzer Service
Parses CI/CD logs to detect failure causes with rule-based and ML-backed classification
"""
import re
import logging
from typing import Tuple, Optional
from models.pipeline import FailureType

logger = logging.getLogger("autoheal.analyzer")

# ── Rule patterns (ordered by specificity) ───────────────────────────────────
FAILURE_PATTERNS = {
    FailureType.DEPENDENCY_ERROR: [
        r"ModuleNotFoundError",
        r"ImportError",
        r"No module named",
        r"Cannot find module",
        r"npm ERR! 404",
        r"npm WARN.*not found",
        r"pip.*not found",
        r"Package.*not found",
        r"Unable to locate package",
        r"Could not find a version",
        r"ERROR: Could not find a version that satisfies",
        r"yarn add.*error",
        r"error TS2307.*Cannot find module",
        r"ENOENT.*node_modules",
        r"requirements.*not found",
        r"dependency.*resolution.*failed",
        r"gem.*could not find",
        r"bundler.*could not find",
    ],
    FailureType.BUILD_ERROR: [
        r"Build failed",
        r"Compilation failed",
        r"SyntaxError",
        r"error\[E\d+\]",          # Rust errors
        r"error CS\d+",            # C# errors
        r"error:.*undefined reference",
        r"linker.*error",
        r"make.*Error",
        r"gradle.*BUILD FAILED",
        r"maven.*BUILD FAILURE",
        r"TypeError.*build",
        r"ReferenceError",
        r"FAILED.*compile",
        r"webpack.*error",
        r"tsc.*error",
        r"eslint.*error",
        r"error TS\d+",
    ],
    FailureType.TEST_FAILURE: [
        r"FAIL\b",
        r"Tests.*failed",
        r"test.*FAILED",
        r"AssertionError",
        r"assert.*failed",
        r"Expected.*received",
        r"FAILED.*test",
        r"\d+ failed",
        r"pytest.*failed",
        r"jest.*failed",
        r"mocha.*failing",
        r"Test suite failed",
        r"FAILURES:",
        r"failures=\d+",
        r"errors=\d+",
        r"FAILED \(.*failures",
    ],
    FailureType.TIMEOUT: [
        r"timeout",
        r"timed out",
        r"Timeout exceeded",
        r"exceeded.*time limit",
        r"SIGTERM",
        r"Job was cancelled.*timeout",
        r"canceling statement due to",
        r"deadline exceeded",
        r"504 Gateway",
        r"Request Timeout",
    ],
    FailureType.NETWORK_ERROR: [
        r"ECONNREFUSED",
        r"ENOTFOUND",
        r"Network error",
        r"Connection refused",
        r"Could not connect",
        r"SSL.*error",
        r"certificate.*error",
        r"DNS.*failed",
        r"getaddrinfo.*failed",
        r"curl.*failed",
        r"wget.*failed",
        r"Unable to connect",
        r"Connection reset",
    ],
    FailureType.CONFIGURATION_ERROR: [
        r"YAML.*error",
        r"Invalid configuration",
        r"config.*not found",
        r"\.env.*missing",
        r"environment variable.*not set",
        r"SECRET.*not found",
        r"permission denied",
        r"access denied",
        r"Forbidden",
        r"Unauthorized",
        r"invalid.*token",
        r"authentication.*failed",
    ],
}

SEVERITY_KEYWORDS = {
    "critical": ["fatal", "critical", "panic", "killed", "oom"],
    "high": ["error", "failed", "failure", "exception"],
    "medium": ["warn", "warning", "deprecated"],
    "low": ["info", "debug", "notice"],
}


def analyze_logs(logs: str) -> Tuple[FailureType, str, float]:
    """
    Analyze log text and return (failure_type, extracted_message, confidence).
    Uses a weighted scoring approach across all pattern groups.
    """
    if not logs:
        return FailureType.UNKNOWN, "No logs provided", 0.0

    logs_lower = logs.lower()
    lines = logs.splitlines()

    scores: dict[FailureType, float] = {ft: 0.0 for ft in FailureType}
    matched_messages: dict[FailureType, list[str]] = {ft: [] for ft in FailureType}

    # Score each failure type
    for failure_type, patterns in FAILURE_PATTERNS.items():
        for pattern in patterns:
            for line in lines:
                if re.search(pattern, line, re.IGNORECASE):
                    scores[failure_type] += 1.0
                    matched_messages[failure_type].append(line.strip())

    # Boost score for lines containing severity keywords
    for line in lines:
        line_lower = line.lower()
        if any(k in line_lower for k in SEVERITY_KEYWORDS["critical"]):
            for ft in FailureType:
                if matched_messages[ft]:
                    scores[ft] *= 1.5

    # Find best match
    best_type = max(scores, key=lambda k: scores[k])
    best_score = scores[best_type]

    if best_score == 0:
        return FailureType.UNKNOWN, _extract_last_error(lines), 0.1

    # Build human-readable message from first few matched lines
    messages = matched_messages[best_type][:3]
    extracted_message = " | ".join(m[:120] for m in messages) if messages else "Unknown error"

    # Normalize confidence to [0, 1]
    total = sum(scores.values()) or 1
    confidence = min(best_score / total + 0.3, 1.0)

    logger.info(
        f"Log analysis: type={best_type}, score={best_score:.1f}, confidence={confidence:.2f}"
    )
    return best_type, extracted_message, confidence


def _extract_last_error(lines: list[str]) -> str:
    """Extract the last meaningful error line from logs"""
    for line in reversed(lines):
        stripped = line.strip()
        if stripped and any(
            kw in stripped.lower() for kw in ["error", "fail", "exception", "fatal"]
        ):
            return stripped[:200]
    return lines[-1].strip()[:200] if lines else "Unknown error"


def extract_failing_step(logs: str) -> Optional[str]:
    """Try to identify the specific failing step or test name"""
    patterns = [
        r"##\[error\](.*)",
        r"FAILED\s+([\w/.:_-]+)",
        r"Error in\s+([\w/.:_-]+)",
        r"at\s+([\w.]+)\s+\(",
        r"Running\s+(.*)\s+\.\.\.\s+FAILED",
    ]
    for pattern in patterns:
        match = re.search(pattern, logs, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()[:100]
    return None


def get_log_stats(logs: str) -> dict:
    """Extract statistical metadata from logs"""
    lines = logs.splitlines()
    return {
        "total_lines": len(lines),
        "error_lines": sum(1 for l in lines if "error" in l.lower()),
        "warning_lines": sum(1 for l in lines if "warn" in l.lower()),
        "has_stack_trace": bool(re.search(r"Traceback|stack trace|at .*\(.*:\d+\)", logs, re.IGNORECASE)),
        "log_size_bytes": len(logs.encode("utf-8")),
    }
