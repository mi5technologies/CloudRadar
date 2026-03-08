"""Background jobs and progress streaming for the API.

Jobs run in a thread; progress events are pushed to a queue and consumed by SSE.
"""

from __future__ import annotations

import json
import threading
import uuid
from collections import deque
from queue import Empty, Queue
from typing import Any, Callable, Optional

from cspm.config import Config
from cspm.core.scan_controller import ScanController
from cspm.reporting.json_report import generate_json_report
from cspm.reporting.html_report import generate_html_report
from cspm.reporting.audit_export import export_audit_csv, export_audit_json
from cspm.reporting.change_report import generate_change_report
from cspm.compliance.compliance_report import generate_compliance_report
from cspm.governance.governance_report import generate_governance_report
from cspm.pentest import find_exposed_services, scan_secrets, map_findings_to_exploits
from cspm.vulnerability import run_vulnerability_scan

from cspm.ui.state import app_state, CONFIG_PATH_DEFAULT


# In-memory job store: job_id -> { "status", "steps", "result", "error", "downloads" }
_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.RLock()

# Queues for SSE: job_id -> Queue of event dicts
_job_queues: dict[str, Queue] = {}
_queues_lock = threading.RLock()

# Last successful scan result (summary + findings) for dashboard and findings page
_last_scan_result: Optional[dict[str, Any]] = None
_last_scan_lock = threading.RLock()


def _emit(job_id: str, event: dict[str, Any]) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is not None and "steps" in job:
            job["steps"].append(event)
    with _queues_lock:
        q = _job_queues.get(job_id)
    if q is not None:
        try:
            q.put_nowait(event)
        except Exception:
            pass


def _progress_callback(job_id: str) -> Callable[[str, str, Optional[str]], None]:
    def on_progress(step: str, status: str, detail: Optional[str] = None) -> None:
        _emit(job_id, {"type": "step", "step": step, "status": status, "detail": detail})

    return on_progress


def _run_scan_job(job_id: str, params: dict[str, Any]) -> None:
    try:
        cloud = (params.get("cloud") or "aws").lower()
        if cloud not in ("aws", "gcp", "azure"):
            cloud = "aws"
        _emit(job_id, {"type": "step", "step": f"Starting {cloud.upper()} security scan", "status": "running", "detail": None})
        cfg = Config(config_path=CONFIG_PATH_DEFAULT)
        ctrl = ScanController(cfg)
        only_list = params.get("only")
        if only_list:
            only_list = [x.strip() for x in only_list if x.strip()] or None
        region = (params.get("region") or "").strip() or None
        result = ctrl.run_scan(
            cloud=cloud,
            region=region,
            only=only_list,
            save_snapshot=params.get("save_snapshot", True),
            on_progress=_progress_callback(job_id),
        )
        if result.get("error"):
            _emit(job_id, {"type": "done", "success": False, "error": result.get("error")})
            with _jobs_lock:
                if job_id in _jobs:
                    _jobs[job_id]["status"] = "failed"
                    _jobs[job_id]["error"] = result.get("error")
            return

        json_out = generate_json_report(result)
        html_out = generate_html_report(result)
        token_json = app_state.outputs.put(json_out, "application/json", "scan_report.json")
        token_html = app_state.outputs.put(html_out, "text/html", "scan_report.html")
        summary = {
            "cloud": result.get("cloud"),
            "account_id": result.get("account_id"),
            "region": result.get("region"),
            "snapshot_id": result.get("snapshot_id"),
            "risk_score": result.get("risk_score"),
            "findings_count": len(result.get("findings", [])),
        }
        _emit(
            job_id,
            {
                "type": "done",
                "success": True,
                "summary": summary,
                "downloads": [
                    {"label": "Download JSON report", "url": f"/api/download/{token_json}"},
                    {"label": "Download HTML report", "url": f"/api/download/{token_html}"},
                ],
            },
        )
        with _jobs_lock:
            if job_id in _jobs:
                _jobs[job_id]["status"] = "completed"
                _jobs[job_id]["result"] = {
                    "summary": summary,
                    "downloads": [
                        {"label": "Download JSON report", "url": f"/api/download/{token_json}"},
                        {"label": "Download HTML report", "url": f"/api/download/{token_html}"},
                    ],
                }
        with _last_scan_lock:
            global _last_scan_result
            _last_scan_result = {
                "summary": summary,
                "findings": result.get("findings", []),
                "cloud": result.get("cloud"),
            }
    except Exception as e:
        _emit(job_id, {"type": "done", "success": False, "error": str(e)})
        with _jobs_lock:
            if job_id in _jobs:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["error"] = str(e)
    finally:
        with _queues_lock:
            q = _job_queues.pop(job_id, None)
            if q is not None:
                try:
                    q.put_nowait({"type": "close"})
                except Exception:
                    pass


def start_scan_job(
    cloud: str = "aws",
    region: Optional[str] = None,
    only: Optional[list] = None,
    save_snapshot: bool = True,
) -> str:
    job_id = uuid.uuid4().hex
    if isinstance(only, str):
        only = [x.strip() for x in only.split(",") if x.strip()] or None
    with _jobs_lock:
        _jobs[job_id] = {
            "status": "running",
            "steps": [],
            "result": None,
            "error": None,
            "downloads": [],
        }
    with _queues_lock:
        _job_queues[job_id] = Queue()
    thread = threading.Thread(
        target=_run_scan_job,
        args=(job_id, {"cloud": cloud, "region": region, "only": only, "save_snapshot": save_snapshot}),
        daemon=True,
    )
    thread.start()
    return job_id


def get_job(job_id: str) -> Optional[dict[str, Any]]:
    with _jobs_lock:
        return _jobs.get(job_id)


def get_job_queue(job_id: str) -> Optional[Queue]:
    with _queues_lock:
        return _job_queues.get(job_id)


def get_last_scan_result() -> Optional[dict[str, Any]]:
    with _last_scan_lock:
        return _last_scan_result


def event_stream(job_id: str):
    """Generator yielding SSE events for a job. Blocks until job completes or closes."""
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        for ev in job.get("steps", []):
            yield f"data: {json.dumps(ev)}\n\n"
        if job.get("status") in ("completed", "failed"):
            result = job.get("result") or {}
            err = job.get("error")
            yield f"data: {json.dumps({'type': 'done', 'success': job['status'] == 'completed', 'summary': result.get('summary'), 'downloads': result.get('downloads', []), 'error': err})}\n\n"
            return
    with _queues_lock:
        q = _job_queues.get(job_id)
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
