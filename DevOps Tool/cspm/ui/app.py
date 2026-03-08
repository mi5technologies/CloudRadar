"""Web UI: FastAPI JSON API + Vue frontend.

- API under /api (status, setup, jobs/scan with SSE progress, audit, compliance, etc.)
- Vue SPA served from frontend/dist (build with: cd frontend && npm run build).
- In development run: backend (uvicorn) + frontend (npm run dev) with Vite proxy to /api.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional
import json

import boto3
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

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
from cspm.remediation.remediation_engine import apply_fix
from cspm.attack_path.attack_path_engine import find_attack_paths
from cspm.ui.scheduler import scheduler_manager

from cspm.ui.state import app_state, CONFIG_PATH_DEFAULT
from cspm.ui import jobs as jobs_module
from cspm.ui import test_runner


UI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = UI_DIR.parent.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"


app = FastAPI(title="CloudRadar API")


@app.on_event("startup")
def _load_state() -> None:
    app_state.load_from_config(CONFIG_PATH_DEFAULT)
    scheduler_manager.start()


@app.on_event("shutdown")
def _shutdown() -> None:
    scheduler_manager.stop()


# ---------- API ----------

@app.get("/api/health")
def api_health() -> dict[str, Any]:
    return {"status": "ok"}


@app.get("/api/status")
def api_status() -> dict[str, Any]:
    return {
        "config_path": str(CONFIG_PATH_DEFAULT),
        "aws": app_state.aws.masked(),
        "gcp": app_state.gcp.masked(),
        "azure": app_state.azure.masked(),
    }


@app.post("/api/setup/aws")
async def api_setup_aws(request: Request) -> dict[str, Any]:
    body = await request.json()
    region = (body.get("region") or "us-east-1").strip()
    access_key_id = (body.get("access_key_id") or "").strip()
    secret_access_key = (body.get("secret_access_key") or "").strip()
    persist = body.get("persist", True)
    if not access_key_id or not secret_access_key:
        return JSONResponse(
            status_code=400,
            content={"error": "access_key_id and secret_access_key required"},
        )
    app_state.set_aws_keys(access_key_id, secret_access_key, None, region)
    if persist:
        app_state.persist_to_config(CONFIG_PATH_DEFAULT)
    return {"ok": True}


@app.post("/api/setup/gcp")
async def api_setup_gcp(request: Request) -> dict[str, Any]:
    body = await request.json() or {}
    project_id = (body.get("project_id") or "").strip()
    credentials_path = (body.get("credentials_path") or "").strip() or None
    persist = body.get("persist", True)
    if not project_id:
        return JSONResponse(status_code=400, content={"error": "project_id required"})
    app_state.set_gcp(project_id, credentials_path=credentials_path, persist=persist)
    return {"ok": True}


@app.post("/api/setup/azure")
async def api_setup_azure(request: Request) -> dict[str, Any]:
    body = await request.json() or {}
    subscription_id = (body.get("subscription_id") or "").strip()
    tenant_id = (body.get("tenant_id") or "").strip()
    client_id = (body.get("client_id") or "").strip()
    client_secret = (body.get("client_secret") or "").strip()
    persist = body.get("persist", True)
    if not subscription_id or not client_id or not client_secret:
        return JSONResponse(
            status_code=400,
            content={"error": "subscription_id, client_id, and client_secret required"},
        )
    app_state.set_azure(subscription_id, tenant_id, client_id, client_secret, persist=persist)
    return {"ok": True}


@app.post("/api/jobs/scan")
async def api_jobs_scan(request: Request) -> dict[str, Any]:
    body = await request.json() or {}
    cloud = (body.get("cloud") or "aws").strip().lower()
    if cloud not in ("aws", "gcp", "azure"):
        cloud = "aws"
    region = (body.get("region") or "").strip() or None
    only = body.get("only")
    if isinstance(only, str):
        only = [x.strip() for x in only.split(",") if x.strip()] or None
    save_snapshot = body.get("save_snapshot", True)
    job_id = jobs_module.start_scan_job(cloud=cloud, region=region, only=only, save_snapshot=save_snapshot)
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def api_job_status(job_id: str) -> dict[str, Any]:
    """Return job state (status, steps, result, error) for polling fallback."""
    job = jobs_module.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "status": job.get("status", "running"),
        "steps": job.get("steps", []),
        "result": job.get("result"),
        "error": job.get("error"),
    }


@app.get("/api/jobs/{job_id}/events")
def api_jobs_events(job_id: str) -> Response:
    job = jobs_module.get_job(job_id)
    if not job:
        return Response(status_code=404)
    return StreamingResponse(
        jobs_module.event_stream(job_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/api/download/{token}")
def api_download(token: str) -> Response:
    item = app_state.outputs.get(token)
    if not item:
        return Response(content="Not found", status_code=404, media_type="text/plain")
    return Response(
        content=item["content"],
        media_type=item["media_type"],
        headers={"Content-Disposition": f"attachment; filename={item['filename']}"},
    )


# ---------- Sync API (no progress stream) for other pages ----------

@app.post("/api/vulnerabilities")
async def api_vulnerabilities(request: Request) -> dict[str, Any]:
    body = await request.json() or {}
    region = (body.get("region") or "us-east-1").strip() or None
    cfg = Config()
    ctrl = ScanController(cfg)
    scan = ctrl.run_scan(cloud="aws", region=region)
    if scan.get("error"):
        return JSONResponse(status_code=400, content={"error": scan.get("error")})
    vulns = run_vulnerability_scan(assets=scan.get("assets"), region=scan.get("region") or region)
    return {"vulnerabilities": vulns, "count": len(vulns)}


@app.get("/api/audit/snapshots")
def api_audit_snapshots() -> list[str]:
    cfg = Config()
    ctrl = ScanController(cfg)
    snapshots = ctrl.snapshot_manager.list_snapshots(cloud="aws")
    return snapshots


@app.post("/api/audit/assets")
async def api_audit_assets(request: Request) -> Any:
    body = await request.json() or {}
    output = body.get("output", "json")
    snapshot_id = (body.get("snapshot_id") or "").strip() or None
    resource_type = (body.get("resource_type") or "").strip() or None
    cfg = Config()
    ctrl = ScanController(cfg)
    catalog = ctrl.get_catalog(cloud="aws", resource_type=resource_type, snapshot_id=snapshot_id)
    if not catalog and not snapshot_id:
        scan = ctrl.run_scan(cloud="aws")
        if scan.get("error"):
            return JSONResponse(status_code=400, content={"error": scan.get("error")})
        catalog = scan.get("catalog", [])
    if output == "csv":
        return Response(content=export_audit_csv(catalog), media_type="text/csv")
    out = {"catalog": catalog, "count": len(catalog)}
    if snapshot_id:
        out["snapshot_id"] = snapshot_id
    return out


@app.post("/api/audit/changes")
async def api_audit_changes(request: Request) -> Any:
    body = await request.json() or {}
    output = body.get("output", "json")
    cfg = Config()
    ctrl = ScanController(cfg)
    scan = ctrl.run_scan(cloud="aws")
    if scan.get("error"):
        return JSONResponse(status_code=400, content={"error": scan.get("error")})
    diff = ctrl.change_detector.changes_since_last(
        cloud="aws",
        account_id=scan.get("account_id"),
        region=scan.get("region"),
        current_assets=scan.get("assets"),
        current_findings=scan.get("findings"),
        current_catalog=scan.get("catalog"),
    )
    if diff is None:
        return JSONResponse(status_code=400, content={"error": "No previous snapshot. Run a scan with save snapshot first."})
    output = body.get("output", "json")
    if output == "html":
        out = generate_change_report(diff, format="html")
        return Response(content=out, media_type="text/html")
    return diff


@app.post("/api/audit/diff")
async def api_audit_diff(request: Request) -> Any:
    body = await request.json() or {}
    before = (body.get("snapshot_before") or "").strip()
    after = (body.get("snapshot_after") or "").strip()
    if not before or not after:
        return JSONResponse(status_code=400, content={"error": "snapshot_before and snapshot_after required"})
    cfg = Config()
    ctrl = ScanController(cfg)
    diff = ctrl.change_detector.diff(before, after)
    if diff.get("error"):
        return JSONResponse(status_code=400, content={"error": diff.get("error")})
    return diff


@app.post("/api/compliance")
async def api_compliance(request: Request) -> Any:
    body = await request.json() or {}
    framework = body.get("framework", "cis")
    output = body.get("output", "json")
    cfg = Config()
    ctrl = ScanController(cfg)
    scan = ctrl.run_scan(cloud="aws")
    if scan.get("error"):
        return JSONResponse(status_code=400, content={"error": scan.get("error")})
    out = generate_compliance_report(scan.get("findings", []), framework=framework, output_format=output)
    if output == "html":
        return Response(content=out, media_type="text/html")
    return json.loads(out) if isinstance(out, str) else out


@app.post("/api/governance")
async def api_governance(request: Request) -> Any:
    body = await request.json() or {}
    output = body.get("output", "json")
    cfg = Config()
    ctrl = ScanController(cfg)
    scan = ctrl.run_scan(cloud="aws")
    if scan.get("error"):
        return JSONResponse(status_code=400, content={"error": scan.get("error")})
    out = generate_governance_report(scan.get("catalog", []), output_format=output)
    if output == "html":
        return Response(content=out, media_type="text/html")
    return json.loads(out) if isinstance(out, str) else out


@app.post("/api/pentest")
async def api_pentest(request: Request) -> dict[str, Any]:
    body = await request.json() or {}
    repo_path = (body.get("repo_path") or "").strip() or None
    cfg = Config()
    ctrl = ScanController(cfg)
    scan = ctrl.run_scan(cloud="aws")
    if scan.get("error"):
        return JSONResponse(status_code=400, content={"error": scan.get("error")})
    assets = scan.get("assets", {})
    findings = scan.get("findings", [])
    out = {}
    out["exposed_services"] = find_exposed_services(assets)
    out["secrets"] = scan_secrets(assets, repo_path=repo_path)
    out["exploit_scenarios"] = map_findings_to_exploits(findings)
    return out


@app.get("/api/summary")
def api_summary() -> dict[str, Any]:
    """Return last successful scan summary for dashboard (risk_score, findings_count, etc.)."""
    last = jobs_module.get_last_scan_result()
    if not last:
        return {"summary": None, "findings_count": 0}
    s = last.get("summary") or {}
    return {
        "summary": s,
        "findings_count": len(last.get("findings", [])),
        "cloud": last.get("cloud"),
    }


@app.get("/api/findings")
def api_findings() -> dict[str, Any]:
    """Return findings from the last successful scan."""
    last = jobs_module.get_last_scan_result()
    if not last:
        return {"findings": [], "summary": None}
    return {
        "findings": last.get("findings", []),
        "summary": last.get("summary"),
    }


# ---------- Remediation ----------

@app.post("/api/remediate")
async def api_remediate(request: Request) -> dict[str, Any]:
    body = await request.json() or {}
    finding = body.get("finding")
    if not finding or not isinstance(finding, dict):
        return JSONResponse(status_code=400, content={"error": "finding object required"})
    dry_run = bool(body.get("dry_run", True))
    region = (body.get("region") or "us-east-1").strip() or "us-east-1"
    result = apply_fix(finding=finding, dry_run=dry_run, region=region)
    return result


# ---------- Attack paths ----------

@app.get("/api/attack-paths")
def api_attack_paths() -> dict[str, Any]:
    """Return attack paths derived from the last scan result."""
    last = jobs_module.get_last_scan_result()
    if not last:
        return {"paths": [], "count": 0}
    findings = last.get("findings", [])
    assets = last.get("assets", {})
    paths = find_attack_paths(graph=assets, findings=findings)
    return {"paths": paths, "count": len(paths)}


class AttackPathRunRequest(BaseModel):
    modules: list[str] = []


@app.post("/api/attack-paths/run")
def api_attack_paths_run(req: AttackPathRunRequest) -> dict[str, Any]:
    """Re-run attack path analysis on latest scan data, optionally filtered by module."""
    last = jobs_module.get_last_scan_result()
    if not last:
        return {"paths": [], "count": 0, "message": "No scan data found. Run a Security Scan first."}
    findings = last.get("findings", [])
    assets = last.get("assets", {})
    paths = find_attack_paths(graph=assets, findings=findings)
    # Filter by requested modules if provided
    if req.modules:
        module_map = {
            "network_chains":   ["sg", "ec2", "alb", "rds"],
            "iam_escalation":   ["iam"],
            "data_exfiltration":["s3", "rds", "dynamodb"],
            "container_escape": ["ecs", "eks"],
            "lateral_movement": ["sg", "lambda", "sqs"],
        }
        allowed_types = set()
        for m in req.modules:
            allowed_types.update(module_map.get(m, []))
        if allowed_types:
            paths = [
                p for p in paths
                if any(
                    hop.get("resource_type", "").lower() in allowed_types
                    for hop in p.get("hops", [])
                )
            ] or paths  # fall back to all paths if filter removes everything
    return {"paths": paths, "count": len(paths)}


# ---------- Scheduler ----------

@app.get("/api/scheduler/jobs")
def api_scheduler_list() -> dict[str, Any]:
    return {"jobs": scheduler_manager.list_jobs()}


@app.post("/api/scheduler/jobs")
async def api_scheduler_add(request: Request) -> dict[str, Any]:
    body = await request.json() or {}
    cloud = (body.get("cloud") or "aws").strip().lower()
    region = (body.get("region") or "us-east-1").strip() or "us-east-1"
    cron_expr = (body.get("cron_expr") or "").strip()
    if not cron_expr:
        return JSONResponse(status_code=400, content={"error": "cron_expr required"})
    job_id = scheduler_manager.add_job(cloud=cloud, region=region, cron_expr=cron_expr)
    return {"job_id": job_id}


@app.delete("/api/scheduler/jobs/{job_id}")
def api_scheduler_remove(job_id: str) -> dict[str, Any]:
    removed = scheduler_manager.remove_job(job_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"removed": True, "job_id": job_id}


# ---------- Notifications ----------

@app.get("/api/notifications/config")
def api_notifications_get() -> dict[str, Any]:
    return app_state.get_notifications_masked()


@app.post("/api/notifications/config")
async def api_notifications_set(request: Request) -> dict[str, Any]:
    body = await request.json() or {}
    allowed_keys = {
        "slack_webhook_url",
        "smtp_host",
        "smtp_port",
        "smtp_user",
        "smtp_password",
        "alert_email_to",
        "alert_email_from",
        "min_severity",
    }
    config = {k: v for k, v in body.items() if k in allowed_keys}
    app_state.set_notifications(config)
    return {"ok": True}


# ---------- Prometheus metrics ----------

@app.get("/api/metrics")
def api_metrics() -> Response:
    """Expose Prometheus-compatible text metrics from the last scan result."""
    last = jobs_module.get_last_scan_result()
    counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    last_scan_ts = 0.0
    compliance_score = -1.0

    if last:
        for finding in last.get("findings", []):
            sev = (finding.get("severity") or "low").lower()
            if sev in counts:
                counts[sev] += 1
        summary = last.get("summary") or {}
        if summary.get("risk_score") is not None:
            try:
                compliance_score = float(summary["risk_score"])
            except (TypeError, ValueError):
                pass

    # Approximate last scan timestamp from the job store
    for job in jobs_module._jobs.values():
        if job.get("status") == "completed":
            last_scan_ts = time.time()
            break

    lines = []
    for sev in ("critical", "high", "medium", "low"):
        lines.append(f'cloudradar_findings_total{{severity="{sev}"}} {counts[sev]}')
    lines.append(f"cloudradar_last_scan_timestamp {int(last_scan_ts)}")
    lines.append(f'cloudradar_compliance_score{{framework="cis"}} {compliance_score}')

    return Response(content="\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


# ---------- Available regions ----------

@app.post("/api/scan/regions")
async def api_scan_regions(request: Request) -> dict[str, Any]:
    body = await request.json() or {}
    cloud = (body.get("cloud") or "aws").strip().lower()
    if cloud != "aws":
        return {"regions": [], "cloud": cloud}
    try:
        ec2 = boto3.client("ec2", region_name="us-east-1")
        resp = ec2.describe_regions(AllRegions=False)
        regions = sorted(r["RegionName"] for r in resp.get("Regions", []))
        return {"regions": regions, "cloud": "aws"}
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=500,
            content={"error": f"Could not list regions: {exc}", "regions": []},
        )


# ---------- Tests (completely isolated from scans) ----------

@app.get("/api/tests/list")
def api_tests_list() -> dict[str, Any]:
    """Return all available test files and whether they exist on disk."""
    return {"tests": test_runner.list_available_tests()}


@app.post("/api/tests/run")
async def api_tests_run(request: Request) -> dict[str, Any]:
    """Start an isolated test run job. Never shares state with scan jobs.

    Body (optional JSON):
        test_files: list[str]  – e.g. ["test_rule_engine", "test_compliance"]
                                  Omit or pass [] to run all tests.
    """
    try:
        body = await request.json() or {}
    except Exception:
        body = {}
    test_files = body.get("test_files") or []
    if not isinstance(test_files, list):
        test_files = []
    job_id = test_runner.start_test_job(test_files=test_files or None)
    return {"job_id": job_id, "test_files": test_files}


@app.get("/api/tests/{job_id}")
def api_tests_status(job_id: str) -> dict[str, Any]:
    """Poll a test job status (polling fallback for SSE)."""
    job = test_runner.get_test_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Test job not found")
    return {
        "status": job.get("status", "running"),
        "lines": job.get("lines", []),
        "summary": job.get("summary"),
        "error": job.get("error"),
    }


@app.get("/api/tests/{job_id}/events")
def api_tests_events(job_id: str) -> Response:
    """SSE stream for a test job — independent of scan SSE."""
    job = test_runner.get_test_job(job_id)
    if not job:
        return Response(status_code=404)
    return StreamingResponse(
        test_runner.test_event_stream(job_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


# ---------- Serve Vue SPA ----------

def _serve_spa(path: str) -> Response:
    """Serve index.html for SPA routes; otherwise try file from dist."""
    if path and path != "index.html":
        file_path = FRONTEND_DIST / path
        if file_path.is_file():
            return FileResponse(file_path)
    index_path = FRONTEND_DIST / "index.html"
    if index_path.is_file():
        return FileResponse(index_path)
    return Response(
        content="<h1>Frontend not built</h1><p>Run: <code>cd frontend && npm install && npm run build</code></p>",
        status_code=503,
        media_type="text/html",
    )


@app.get("/")
def index() -> Response:
    return _serve_spa("")


@app.get("/{path:path}")
def catch_all(path: str) -> Response:
    if path.startswith("api/"):
        return Response(status_code=404)
    return _serve_spa(path)
