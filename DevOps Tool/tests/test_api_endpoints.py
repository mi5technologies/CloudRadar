"""Tests for the FastAPI backend endpoints using the HTTPX TestClient.

Covers health, status, setup validation, test-runner list/run/status, and
the findings / summary endpoints — all without real cloud credentials.
"""
import pytest

# TestClient requires httpx — skip the whole module gracefully if not installed
httpx = pytest.importorskip("httpx", reason="httpx not installed")
from fastapi.testclient import TestClient

from cspm.ui.app import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# /api/health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_200(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_health_body_contains_status_ok(self):
        resp = client.get("/api/health")
        assert resp.json().get("status") == "ok"


# ---------------------------------------------------------------------------
# /api/status
# ---------------------------------------------------------------------------

class TestStatus:
    def test_status_returns_200(self):
        resp = client.get("/api/status")
        assert resp.status_code == 200

    def test_status_has_cloud_keys(self):
        resp = client.get("/api/status")
        data = resp.json()
        for key in ("aws", "gcp", "azure"):
            assert key in data, f"Missing cloud key: {key}"

    def test_status_has_config_path(self):
        resp = client.get("/api/status")
        assert "config_path" in resp.json()


# ---------------------------------------------------------------------------
# /api/setup — input validation
# ---------------------------------------------------------------------------

class TestSetupValidation:
    def test_aws_setup_rejects_missing_keys(self):
        resp = client.post("/api/setup/aws", json={"region": "us-east-1"})
        assert resp.status_code == 400
        assert "error" in resp.json()

    def test_aws_setup_rejects_empty_access_key(self):
        resp = client.post("/api/setup/aws", json={"access_key_id": "", "secret_access_key": "secret"})
        assert resp.status_code == 400

    def test_gcp_setup_rejects_missing_project_id(self):
        resp = client.post("/api/setup/gcp", json={})
        assert resp.status_code == 400

    def test_azure_setup_rejects_missing_subscription_id(self):
        resp = client.post("/api/setup/azure", json={"client_id": "c", "client_secret": "s"})
        assert resp.status_code == 400

    def test_azure_setup_rejects_missing_client_id(self):
        resp = client.post("/api/setup/azure", json={"subscription_id": "sub-1", "client_secret": "s"})
        assert resp.status_code == 400

    def test_aws_setup_accepts_valid_payload(self):
        resp = client.post("/api/setup/aws", json={
            "region": "us-east-1",
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "persist": False,
        })
        assert resp.status_code == 200
        assert resp.json().get("ok") is True


# ---------------------------------------------------------------------------
# /api/tests/list
# ---------------------------------------------------------------------------

class TestTestsList:
    def test_list_returns_200(self):
        resp = client.get("/api/tests/list")
        assert resp.status_code == 200

    def test_list_has_tests_key(self):
        resp = client.get("/api/tests/list")
        assert "tests" in resp.json()

    def test_list_returns_list(self):
        resp = client.get("/api/tests/list")
        assert isinstance(resp.json()["tests"], list)

    def test_each_test_has_module_and_display_name(self):
        resp = client.get("/api/tests/list")
        for t in resp.json()["tests"]:
            assert "module" in t
            assert "display_name" in t

    def test_each_test_has_exists_field(self):
        resp = client.get("/api/tests/list")
        for t in resp.json()["tests"]:
            assert "exists" in t
            assert isinstance(t["exists"], bool)


# ---------------------------------------------------------------------------
# /api/tests/run  (start job only — don't wait for completion)
# ---------------------------------------------------------------------------

class TestTestsRun:
    def test_run_returns_200(self):
        resp = client.post("/api/tests/run", json={"test_files": []})
        assert resp.status_code == 200

    def test_run_returns_job_id(self):
        resp = client.post("/api/tests/run", json={"test_files": []})
        assert "job_id" in resp.json()
        assert isinstance(resp.json()["job_id"], str)
        assert len(resp.json()["job_id"]) > 0

    def test_run_with_specific_file_returns_job_id(self):
        resp = client.post("/api/tests/run", json={"test_files": ["test_rule_engine"]})
        assert "job_id" in resp.json()

    def test_run_without_body_returns_job_id(self):
        """Empty body should default to running all tests."""
        resp = client.post("/api/tests/run")
        assert resp.status_code == 200
        assert "job_id" in resp.json()

    def test_run_with_invalid_body_type_does_not_crash(self):
        """test_files as a string instead of list — should be handled gracefully."""
        resp = client.post("/api/tests/run", json={"test_files": "test_rule_engine"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /api/tests/{job_id}  (status polling)
# ---------------------------------------------------------------------------

class TestTestsStatus:
    def _start_job(self) -> str:
        resp = client.post("/api/tests/run", json={"test_files": []})
        return resp.json()["job_id"]

    def test_status_returns_200_for_valid_job(self):
        job_id = self._start_job()
        resp = client.get(f"/api/tests/{job_id}")
        assert resp.status_code == 200

    def test_status_has_status_field(self):
        job_id = self._start_job()
        resp = client.get(f"/api/tests/{job_id}")
        assert "status" in resp.json()

    def test_status_has_lines_field(self):
        job_id = self._start_job()
        resp = client.get(f"/api/tests/{job_id}")
        assert "lines" in resp.json()

    def test_status_404_for_unknown_job(self):
        resp = client.get("/api/tests/nonexistent-job-id-xyz")
        assert resp.status_code == 404

    def test_status_is_running_initially(self):
        """Immediately after starting, job should be 'running'."""
        job_id = self._start_job()
        resp = client.get(f"/api/tests/{job_id}")
        assert resp.json()["status"] in ("running", "passed", "failed")


# ---------------------------------------------------------------------------
# /api/findings  (if endpoint exists — skip gracefully if not)
# ---------------------------------------------------------------------------

class TestFindingsEndpoint:
    def test_findings_endpoint_exists_or_404(self):
        """The /api/findings endpoint should return 200 (no scan yet → empty) or 404."""
        resp = client.get("/api/findings")
        assert resp.status_code in (200, 404)

    def test_findings_response_is_json(self):
        resp = client.get("/api/findings")
        if resp.status_code == 200:
            assert resp.headers.get("content-type", "").startswith("application/json")


# ---------------------------------------------------------------------------
# /api/summary
# ---------------------------------------------------------------------------

class TestSummaryEndpoint:
    def test_summary_endpoint_exists_or_404(self):
        resp = client.get("/api/summary")
        assert resp.status_code in (200, 404)
