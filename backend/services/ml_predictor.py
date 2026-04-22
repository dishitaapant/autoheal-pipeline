"""
ML-based Failure Type Predictor
Uses TF-IDF + LogisticRegression to predict failure type from log text.
Falls back to rule-based analyzer if model is not trained yet.
"""
import os
import pickle
import logging
import re
from typing import Tuple
from pathlib import Path

logger = logging.getLogger("autoheal.ml")

MODEL_PATH = Path(os.getenv("MODEL_PATH", "/tmp/autoheal_model.pkl"))

# Training examples: (log_snippet, failure_type_label)
TRAINING_DATA = [
    # DEPENDENCY_ERROR
    ("ModuleNotFoundError: No module named 'requests'", "dependency_error"),
    ("ImportError: cannot import name 'json'", "dependency_error"),
    ("npm ERR! 404 Not Found - GET https://registry.npmjs.org/react", "dependency_error"),
    ("ERROR: Could not find a version that satisfies the requirement tensorflow==2.0", "dependency_error"),
    ("Cannot find module '@babel/core'", "dependency_error"),
    ("Error: Cannot find module 'express'", "dependency_error"),
    ("pip install failed: could not find package", "dependency_error"),
    ("requirements.txt not satisfied", "dependency_error"),
    ("Package 'pandas' has no installation candidate", "dependency_error"),
    ("Unable to locate package python3-dev", "dependency_error"),
    # BUILD_ERROR
    ("Build failed with exit code 1", "build_error"),
    ("Compilation failed SyntaxError unexpected token", "build_error"),
    ("error[E0382]: use of moved value: `x`", "build_error"),
    ("webpack compilation error TypeError is not a function", "build_error"),
    ("tsc error TS2307: Cannot find module 'path'", "build_error"),
    ("gradle BUILD FAILED execution failed for task compileJava", "build_error"),
    ("make: *** [all] Error 2", "build_error"),
    ("linker error undefined reference to main", "build_error"),
    ("eslint error no-unused-vars", "build_error"),
    ("maven BUILD FAILURE plugin not found", "build_error"),
    # TEST_FAILURE
    ("FAILED tests/test_api.py::test_get_user - AssertionError", "test_failure"),
    ("Tests failed 5 errors 2 failures", "test_failure"),
    ("jest FAIL src/components/Button.test.js", "test_failure"),
    ("Expected 200 received 404", "test_failure"),
    ("pytest FAILURES test_login FAILED", "test_failure"),
    ("mocha failing 3 tests", "test_failure"),
    ("Test suite failed to run SyntaxError", "test_failure"),
    ("AssertionError assert False is not True", "test_failure"),
    ("FAILED (failures=3 errors=1)", "test_failure"),
    # TIMEOUT
    ("Error: Job was cancelled after timeout of 6 hours", "timeout"),
    ("Timeout exceeded waiting for response 30000ms", "timeout"),
    ("SIGTERM process killed timeout", "timeout"),
    ("deadline exceeded context deadline exceeded", "timeout"),
    ("504 Gateway Timeout upstream request timeout", "timeout"),
    ("canceling statement due to statement timeout", "timeout"),
    ("Build exceeded time limit 60 minutes", "timeout"),
    # NETWORK_ERROR
    ("ECONNREFUSED 127.0.0.1:5432 connection refused", "network_error"),
    ("ENOTFOUND registry.npmjs.org DNS lookup failed", "network_error"),
    ("SSL certificate error unable to verify", "network_error"),
    ("curl failed to connect Connection refused", "network_error"),
    ("getaddrinfo ENOTFOUND api.github.com", "network_error"),
    ("Connection reset by peer", "network_error"),
    # CONFIGURATION_ERROR
    ("Error: YAML parse error on line 5", "configuration_error"),
    ("environment variable DATABASE_URL not set", "configuration_error"),
    ("SECRET_KEY not found in environment", "configuration_error"),
    ("permission denied /etc/config.json", "configuration_error"),
    ("authentication failed invalid token", "configuration_error"),
    ("Invalid configuration file .github/workflows/ci.yml", "configuration_error"),
    ("Forbidden 403 access denied repository secrets", "configuration_error"),
]


class FailurePredictor:
    def __init__(self):
        self._model = None
        self._vectorizer = None
        self._trained = False
        self._load_or_train()

    def _load_or_train(self):
        if MODEL_PATH.exists():
            try:
                with open(MODEL_PATH, "rb") as f:
                    bundle = pickle.load(f)
                    self._vectorizer = bundle["vectorizer"]
                    self._model = bundle["model"]
                    self._trained = True
                    logger.info("ML model loaded from disk")
                    return
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")

        self._train()

    def _train(self):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import Pipeline as SKPipeline

            texts = [x[0] for x in TRAINING_DATA]
            labels = [x[1] for x in TRAINING_DATA]

            self._vectorizer = TfidfVectorizer(
                analyzer="word",
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True,
            )
            X = self._vectorizer.fit_transform(texts)

            self._model = LogisticRegression(
                max_iter=500,
                C=1.0,
                multi_class="multinomial",
                solver="lbfgs",
            )
            self._model.fit(X, labels)
            self._trained = True

            try:
                with open(MODEL_PATH, "wb") as f:
                    pickle.dump({"vectorizer": self._vectorizer, "model": self._model}, f)
                logger.info(f"ML model trained and saved to {MODEL_PATH}")
            except Exception as e:
                logger.warning(f"Could not save model: {e}")

        except ImportError:
            logger.warning("scikit-learn not installed — ML predictor disabled")
        except Exception as e:
            logger.error(f"Model training failed: {e}")

    def predict(self, log_text: str) -> Tuple[str, float]:
        """Predict failure type from log text. Returns (label, confidence)."""
        if not self._trained or self._model is None:
            return "unknown", 0.0

        try:
            # Use a summary of the log (first + last 1000 chars)
            summary = (log_text[:500] + log_text[-500:]).lower()
            # Remove timestamps and noise
            summary = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "", summary)
            summary = re.sub(r"\x1b\[[0-9;]*m", "", summary)

            X = self._vectorizer.transform([summary])
            label = self._model.predict(X)[0]
            proba = self._model.predict_proba(X)[0]
            confidence = float(max(proba))

            logger.info(f"ML prediction: {label} ({confidence:.2f})")
            return label, confidence
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return "unknown", 0.0

    @property
    def is_ready(self) -> bool:
        return self._trained


# Singleton instance
_predictor: FailurePredictor = None


def get_predictor() -> FailurePredictor:
    global _predictor
    if _predictor is None:
        _predictor = FailurePredictor()
    return _predictor
