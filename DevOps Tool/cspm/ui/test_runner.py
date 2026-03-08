"""Isolated test runner — executes pytest as a subprocess and streams output.

Completely independent of scans: uses its own job store, its own SSE queues,
and can only be triggered explicitly via POST /api/tests/run.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Optional

from cspm.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Independent job store — isolated from scan jobs
# ---------------------------------------------------------------------------

_test_jobs: dict[str, dict[str, Any]] = {}
_test_jobs_lock = threading.RLock()

_test_queues: dict[str, Queue] = {}
_test_queues_lock = threading.RLock()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"

# All available test files, mapped to a display name
_ALL_TEST_FILES = {
    "test_rule_engine":         "Rule Engine",
    "test_s3_scanner":          "S3 Scanner",
    "test_compliance":          "Compliance Frameworks",
    "test_remediation":         "Remediation Engine",
    "test_attack_paths":        "Attack Paths",
    "test_scanners":            "All Scanners",
    "test_cloudfront_scanner":  "CloudFront Scanner",
    "test_risk_engine":         "Risk Engine",
    "test_api_endpoints":       "API Endpoints",
    "test_cost_scanner":        "Cost Scanner",
}

# Regex patterns for parsing pytest -v output
_RE_PASSED = re.compile(r"^(.+?)\s+PASSED")
_RE_FAILED = re.compile(r"^(.+?)\s+FAILED")
_RE_ERROR = re.compile(r"^(.+?)\s+ERROR")
_RE_SKIPPED = re.compile(r"^(.+?)\s+SKIPPED")
_RE_SUMMARY = re.compile(
    r"=+\s*([\d]+ passed)?[,\s]*([\d]+ failed)?[,\s]*([\d]+ error)?[,\s]*([\d]+ warning)?"
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _emit(job_id: str, event: dict[str, Any]) -> None:
    """Append event to job steps list and push to SSE queue."""
    with _test_jobs_lock:
        job = _test_jobs.get(job_id)
        if job is not None:
            job["lines"].append(event)
    with _test_queues_lock:
        q = _test_queues.get(job_id)
    if q is not None:
        try:
            q.put_nowait(event)
        except Exception:
            pass


def _parse_line(raw: str) -> dict[str, Any]:
    """Turn a raw pytest output line into a structured event."""
    line = raw.rstrip()
    if _RE_PASSED.match(line):
        return {"type": "test", "status": "passed", "name": line.split("PASSED")[0].strip(), "raw": line}
    if _RE_FAILED.match(line):
        return {"type": "test", "status": "failed", "name": line.split("FAILED")[0].strip(), "raw": line}
    if _RE_ERROR.match(line):
        return {"type": "test", "status": "error", "name": line.split("ERROR")[0].strip(), "raw": line}
    if _RE_SKIPPED.match(line):
        return {"type": "test", "status": "skipped", "name": line.split("SKIPPED")[0].strip(), "raw": line}
    return {"type": "output", "raw": line}


def _run_tests(job_id: str, test_files: list[str]) -> None:
    """Run pytest in a subprocess, stream output line by line, update job state."""
    try:
        # Build pytest command
        pytest_args = [sys.executable, "-m", "pytest", "-v", "--tb=short", "--no-header"]
        if test_files:
            for tf in test_files:
                # Accept either "test_rule_engine" or "tests/test_rule_engine.py"
                if not tf.endswith(".py"):
                    tf = tf + ".py"
                path = TESTS_DIR / tf
                if path.exists():
                    pytest_args.append(str(path))
                else:
                    _emit(job_id, {"type": "output", "raw": f"[WARN] Test file not found: {tf}"})
        else:
            pytest_args.append(str(TESTS_DIR))

        _emit(job_id, {
            "type": "output",
            "raw": f"$ {' '.join(pytest_args[2:])}",  # show "pytest ..." without python -m
        })

        env = os.environ.copy()
        # Inject dummy AWS credentials so moto-based tests work without real keys
        env.setdefault("AWS_ACCESS_KEY_ID", "testing")
        env.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
        env.setdefault("AWS_SECURITY_TOKEN", "testing")
        env.setdefault("AWS_SESSION_TOKEN", "testing")
        env.setdefault("AWS_DEFAULT_REGION", "us-east-1")

        process = subprocess.Popen(
            pytest_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(PROJECT_ROOT),
            env=env,
        )

        passed = failed = errors = skipped = 0

        for raw_line in iter(process.stdout.readline, ""):
            event = _parse_line(raw_line)
            if event["type"] == "test":
                if event["status"] == "passed":
                    passed += 1
                elif event["status"] == "failed":
                    failed += 1
                elif event["status"] == "error":
                    errors += 1
                elif event["status"] == "skipped":
                    skipped += 1
            _emit(job_id, event)

        process.wait()
        exit_code = process.returncode
        success = exit_code == 0

        summary = {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "total": passed + failed + errors + skipped,
            "exit_code": exit_code,
        }

        _emit(job_id, {"type": "done", "success": success, "summary": summary})

        with _test_jobs_lock:
            if job_id in _test_jobs:
                _test_jobs[job_id]["status"] = "passed" if success else "failed"
                _test_jobs[job_id]["summary"] = summary

    except Exception as exc:
        logger.error("Test runner job %s crashed: %s", job_id, exc)
        _emit(job_id, {"type": "done", "success": False, "error": str(exc), "summary": {}})
        with _test_jobs_lock:
            if job_id in _test_jobs:
                _test_jobs[job_id]["status"] = "failed"
                _test_jobs[job_id]["error"] = str(exc)
    finally:
        with _test_queues_lock:
            q = _test_queues.pop(job_id, None)
            if q is not None:
                try:
                    q.put_nowait({"type": "close"})
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_available_tests() -> list[dict[str, Any]]:
    """Return all test files that exist on disk."""
    result = []
    for module, display in _ALL_TEST_FILES.items():
        path = TESTS_DIR / f"{module}.py"
        result.append({
            "module": module,
            "display_name": display,
            "file": f"tests/{module}.py",
            "exists": path.exists(),
        })
    return result


def start_test_job(test_files: list[str] | None = None) -> str:
    """Launch a test run job and return its job_id."""
    job_id = uuid.uuid4().hex
    with _test_jobs_lock:
        _test_jobs[job_id] = {
            "status": "running",
            "lines": [],
            "summary": None,
            "error": None,
            "test_files": test_files or [],
        }
    with _test_queues_lock:
        _test_queues[job_id] = Queue()

    thread = threading.Thread(
        target=_run_tests,
        args=(job_id, test_files or []),
        daemon=True,
        name=f"test-runner-{job_id[:8]}",
    )
    thread.start()
    logger.info("Test job %s started (files=%s)", job_id, test_files)
    return job_id


def get_test_job(job_id: str) -> Optional[dict[str, Any]]:
    with _test_jobs_lock:
        return _test_jobs.get(job_id)


def test_event_stream(job_id: str):
    """SSE generator for a test job — completely independent of scan SSE."""
    with _test_jobs_lock:
        job = _test_jobs.get(job_id)
        if job is None:
            return
        # Replay history first
        for ev in job.get("lines", []):
            yield f"data: {json.dumps(ev)}\n\n"
        # If already done, send final event and close
        if job.get("status") in ("passed", "failed"):
            summary = job.get("summary") or {}
            err = job.get("error")
            yield f"data: {json.dumps({'type': 'done', 'success': job['status'] == 'passed', 'summary': summary, 'error': err})}\n\n"
            return

    with _test_queues_lock:
        q = _test_queues.get(job_id)
    if not q:
        return

    while True:
        try:
            ev = q.get(timeout=30)
            if ev.get("type") == "close":
                break
            yield f"data: {json.dumps(ev)}\n\n"
            if ev.get("type") == "done":
                break
        except Empty:
            yield ": keepalive\n\n"
        except Exception:
            break
