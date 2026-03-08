# Web API Reference

The CloudRadar Web UI is backed by a FastAPI application. All API routes are under the `/api` prefix.

**Base URL:** `http://<host>:8000/api` (or same origin when the Vue app is served from the same server).

**Interactive API docs (OpenAPI/Swagger):** When the backend is running, open **http://&lt;host&gt;:8000/docs** for Swagger UI. Use this in development or in production (optionally behind authentication) to explore and test endpoints.

---

## Health and status

### `GET /api/health`

Returns service health (for load balancers or monitoring).

**Response:** `200 OK`  
```json
{ "status": "ok" }
```

### `GET /api/status`

Returns current configuration status for all clouds (masked credentials).

**Response:** `200 OK`

```json
{
  "config_path": "/path/to/config.yaml",
  "aws": {
    "mode": "keys",
    "access_key_id": "AKI***xyz",
    "region": "us-east-1",
    "updated_at": 1234567890
  },
  "gcp": { "mode": "project", "project_id": "my-project", "credentials_path": null },
  "azure": { "mode": "none", "subscription_id": null }
}
```

---

## Setup

### `POST /api/setup/aws`

Save AWS credentials (and optionally persist to config).

**Body:**

```json
{
  "region": "us-east-1",
  "access_key_id": "AKIA...",
  "secret_access_key": "...",
  "session_token": null,
  "persist": true
}
```

**Response:** `200 OK` `{ "ok": true }`  
**Error:** `400` `{ "error": "access_key_id and secret_access_key required" }`

### `POST /api/setup/gcp`

Save GCP project and optional credentials path.

**Body:**

```json
{
  "project_id": "my-gcp-project",
  "credentials_path": "/path/to/sa.json",
  "persist": true
}
```

**Response:** `200 OK` `{ "ok": true }`  
**Error:** `400` `{ "error": "project_id required" }`

### `POST /api/setup/azure`

Save Azure service principal credentials.

**Body:**

```json
{
  "subscription_id": "uuid",
  "tenant_id": "uuid",
  "client_id": "uuid",
  "client_secret": "...",
  "persist": true
}
```

**Response:** `200 OK` `{ "ok": true }`  
**Error:** `400` `{ "error": "subscription_id, client_id, and client_secret required" }`

### `GET /api/summary`

Returns the last successful scan summary for the dashboard (cloud, region, findings count, risk score). Empty if no scan has completed yet.

**Response:** `200 OK`  
```json
{
  "summary": { "cloud": "aws", "region": "us-east-1", "findings_count": 12, "risk_score": 45, "snapshot_id": "..." },
  "findings_count": 12,
  "cloud": "aws"
}
```

If no previous scan: `{ "summary": null, "findings_count": 0 }`

### `GET /api/findings`

Returns findings from the last successful scan. Use the **Findings** page in the UI to browse them.

**Response:** `200 OK`  
```json
{
  "findings": [ { "severity": "high", "rule_id": "...", "resource_type": "...", "resource_id": "...", "title": "..." } ],
  "summary": { "cloud": "aws", "region": "us-east-1", "findings_count": 12, "risk_score": 45 }
}
```

---

## Jobs (scan with progress)

### `POST /api/jobs/scan`

Start a security scan job. Returns a job ID; use SSE or polling to get progress.

**Body:**

```json
{
  "cloud": "aws",
  "region": "us-east-1",
  "only": ["ec2", "s3"],
  "save_snapshot": true
}
```

- `cloud`: `"aws"` | `"gcp"` | `"azure"`
- `region`: optional; used for AWS
- `only`: optional list of asset types (e.g. ec2, s3)
- `save_snapshot`: optional, default `true`

**Response:** `200 OK`

```json
{ "job_id": "abc123def456" }
```

### `GET /api/jobs/{job_id}`

Get job state (for polling fallback).

**Response:** `200 OK`

```json
{
  "status": "running",
  "steps": [
    { "type": "step", "step": "Authenticating", "status": "success", "detail": null },
    { "type": "step", "step": "Discovering EC2 instances", "status": "running", "detail": null }
  ],
  "result": null,
  "error": null
}
```

When `status` is `"completed"`, `result` contains `summary` and `downloads`. When `"failed"`, `error` is set.

### `GET /api/jobs/{job_id}/events`

Server-Sent Events (SSE) stream of job progress. Events are JSON objects:

- `{ "type": "step", "step": "...", "status": "running"|"success"|"failed", "detail": "..." }`
- `{ "type": "done", "success": true|false, "summary": {...}, "downloads": [...], "error": "..." }`
- `{ "type": "close" }`

**Response:** `200 OK`, `Content-Type: text/event-stream`

---

## Downloads

### `GET /api/download/{token}`

Download a previously generated report (e.g. from a scan result). Token is returned in job `result.downloads[].url` (path segment only).

**Response:** `200 OK` with appropriate `Content-Type` and `Content-Disposition`  
**Error:** `404` if token not found

---

## Synchronous endpoints (no job)

These run the operation in the request and return the result directly. Suitable for smaller operations.

| Method | Path | Body (JSON) | Description |
|--------|------|-------------|-------------|
| POST | `/api/vulnerabilities` | `{ "region": "us-east-1" }` | Run vulnerability scan (ECR, AMI) |
| GET | `/api/audit/snapshots` | — | List snapshot IDs |
| POST | `/api/audit/assets` | `{ "output": "json", "snapshot_id": null }` | Export asset catalog (JSON or CSV) |
| POST | `/api/audit/changes` | `{ "output": "json" }` | Changes since last snapshot |
| POST | `/api/audit/diff` | `{ "snapshot_before": "id1", "snapshot_after": "id2" }` | Diff two snapshots |
| POST | `/api/compliance` | `{ "framework": "cis", "output": "json" }` | Compliance report |
| POST | `/api/governance` | `{ "output": "json" }` | Governance report |
| POST | `/api/pentest` | `{ "repo_path": null }` | Pentest (exposed, secrets, exploit map) |
| POST | `/api/serverless-scan` | `{ "cloud": "aws", "region": "us-east-1", "skip_rules": [] }` | Serverless security (Lambda, Step Functions, API GW, SQS, DynamoDB; GCP: Cloud Run, Cloud Functions; Azure: Function Apps) |
| POST | `/api/usage-scan` | `{ "cloud": "aws", "days_lookback": 14, "skip_rules": [] }` | Usage findings (AWS Lambda idle, errors, throttles from CloudWatch) |

All POST bodies are optional; defaults are as shown. Errors return `400` with `{ "error": "..." }`.
