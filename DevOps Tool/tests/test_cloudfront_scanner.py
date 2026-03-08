"""Tests for the CloudFront security scanner.

These tests exercise every rule in cloudfront_scanner.scan_cloudfront() using
synthetic asset dictionaries — no AWS credentials or moto required.
"""
import pytest
from cspm.scanners.cloudfront_scanner import scan_cloudfront


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dist(**overrides) -> dict:
    """Return a safe-by-default CloudFront distribution asset dict."""
    base = {
        "id": "EABC123XYZ",
        "name": "dxyz.cloudfront.net",
        "type": "cloudfront",
        "region": "global",
        "enabled": True,
        "status": "Deployed",
        "waf_attached": True,
        "web_acl_id": "arn:aws:wafv2:us-east-1:123456789:global/webacl/my-acl/abc",
        "http_allowed": False,
        "https_only": True,
        "viewer_protocols": ["redirect-to-https"],
        "tls_min_version": "TLSv1.2_2021",
        "tls_outdated": False,
        "security_headers_configured": True,
        "hsts_enabled": True,
        "has_security_headers_policy": True,
        "headers_config": {
            "hsts_enabled": True,
            "x_frame_options": True,
            "content_type_options": True,
            "xss_protection": True,
            "referrer_policy": True,
        },
        "s3_origins_without_oac": [],
        "origin_direct_access": False,
        "geo_restriction_enabled": True,
        "access_logging_enabled": True,
        "origin_count": 1,
        "price_class": "PriceClass_100",
        "comment": "",
    }
    base.update(overrides)
    return base


def _rule_ids(findings: list) -> list[str]:
    return [f["rule_id"] for f in findings]


# ---------------------------------------------------------------------------
# CF-01: HTTP allowed
# ---------------------------------------------------------------------------

def test_no_finding_when_https_only():
    findings = scan_cloudfront([_dist(http_allowed=False)])
    assert "cf.http_allowed" not in _rule_ids(findings)


def test_finding_when_http_allowed():
    findings = scan_cloudfront([_dist(http_allowed=True)])
    assert "cf.http_allowed" in _rule_ids(findings)


def test_http_allowed_finding_severity_is_high():
    findings = scan_cloudfront([_dist(http_allowed=True)])
    f = next(x for x in findings if x["rule_id"] == "cf.http_allowed")
    assert f["severity"] == "high"


# ---------------------------------------------------------------------------
# CF-02: No WAF
# ---------------------------------------------------------------------------

def test_no_finding_when_waf_attached():
    findings = scan_cloudfront([_dist(waf_attached=True)])
    assert "cf.no_waf" not in _rule_ids(findings)


def test_finding_when_no_waf():
    findings = scan_cloudfront([_dist(waf_attached=False, web_acl_id="")])
    assert "cf.no_waf" in _rule_ids(findings)


def test_no_waf_finding_severity_is_high():
    findings = scan_cloudfront([_dist(waf_attached=False, web_acl_id="")])
    f = next(x for x in findings if x["rule_id"] == "cf.no_waf")
    assert f["severity"] == "high"


# ---------------------------------------------------------------------------
# CF-03: Missing security headers
# ---------------------------------------------------------------------------

def test_no_finding_when_security_headers_configured():
    findings = scan_cloudfront([_dist(security_headers_configured=True)])
    assert "cf.missing_security_headers" not in _rule_ids(findings)


def test_finding_when_security_headers_missing():
    findings = scan_cloudfront([_dist(
        security_headers_configured=False,
        has_security_headers_policy=False,
        hsts_enabled=False,
        headers_config={},
    )])
    assert "cf.missing_security_headers" in _rule_ids(findings)


def test_missing_headers_finding_severity_is_medium():
    findings = scan_cloudfront([_dist(
        security_headers_configured=False,
        has_security_headers_policy=False,
        hsts_enabled=False,
        headers_config={},
    )])
    f = next(x for x in findings if x["rule_id"] == "cf.missing_security_headers")
    assert f["severity"] == "medium"


# ---------------------------------------------------------------------------
# CF-04: HSTS missing (policy exists but HSTS not enabled)
# ---------------------------------------------------------------------------

def test_no_hsts_finding_when_hsts_enabled():
    findings = scan_cloudfront([_dist(hsts_enabled=True, has_security_headers_policy=True)])
    assert "cf.no_hsts" not in _rule_ids(findings)


def test_hsts_finding_when_policy_present_but_hsts_off():
    findings = scan_cloudfront([_dist(
        security_headers_configured=False,
        has_security_headers_policy=True,
        hsts_enabled=False,
    )])
    assert "cf.no_hsts" in _rule_ids(findings)


# ---------------------------------------------------------------------------
# CF-05: Outdated TLS
# ---------------------------------------------------------------------------

def test_no_finding_when_tls_current():
    findings = scan_cloudfront([_dist(tls_outdated=False, tls_min_version="TLSv1.2_2021")])
    assert "cf.outdated_tls" not in _rule_ids(findings)


def test_finding_when_tls_outdated():
    findings = scan_cloudfront([_dist(tls_outdated=True, tls_min_version="TLSv1")])
    assert "cf.outdated_tls" in _rule_ids(findings)


def test_outdated_tls_finding_severity_is_high():
    findings = scan_cloudfront([_dist(tls_outdated=True, tls_min_version="TLSv1")])
    f = next(x for x in findings if x["rule_id"] == "cf.outdated_tls")
    assert f["severity"] == "high"


# ---------------------------------------------------------------------------
# CF-06: S3 origin without OAC
# ---------------------------------------------------------------------------

def test_no_finding_when_s3_origin_protected():
    findings = scan_cloudfront([_dist(origin_direct_access=False, s3_origins_without_oac=[])])
    assert "cf.s3_origin_no_oac" not in _rule_ids(findings)


def test_finding_when_s3_origin_unprotected():
    findings = scan_cloudfront([_dist(
        origin_direct_access=True,
        s3_origins_without_oac=["my-bucket.s3.amazonaws.com"],
    )])
    assert "cf.s3_origin_no_oac" in _rule_ids(findings)


def test_s3_no_oac_finding_severity_is_high():
    findings = scan_cloudfront([_dist(
        origin_direct_access=True,
        s3_origins_without_oac=["my-bucket.s3.amazonaws.com"],
    )])
    f = next(x for x in findings if x["rule_id"] == "cf.s3_origin_no_oac")
    assert f["severity"] == "high"


# ---------------------------------------------------------------------------
# CF-07: Logging disabled
# ---------------------------------------------------------------------------

def test_no_finding_when_logging_enabled():
    findings = scan_cloudfront([_dist(access_logging_enabled=True)])
    assert "cf.logging_disabled" not in _rule_ids(findings)


def test_finding_when_logging_disabled():
    findings = scan_cloudfront([_dist(access_logging_enabled=False)])
    assert "cf.logging_disabled" in _rule_ids(findings)


def test_logging_disabled_finding_severity_is_medium():
    findings = scan_cloudfront([_dist(access_logging_enabled=False)])
    f = next(x for x in findings if x["rule_id"] == "cf.logging_disabled")
    assert f["severity"] == "medium"


# ---------------------------------------------------------------------------
# CF-08: No geo restriction
# ---------------------------------------------------------------------------

def test_no_finding_when_geo_restriction_enabled():
    findings = scan_cloudfront([_dist(geo_restriction_enabled=True)])
    assert "cf.no_geo_restriction" not in _rule_ids(findings)


def test_finding_when_no_geo_restriction():
    findings = scan_cloudfront([_dist(geo_restriction_enabled=False, enabled=True)])
    assert "cf.no_geo_restriction" in _rule_ids(findings)


def test_geo_restriction_finding_severity_is_low():
    findings = scan_cloudfront([_dist(geo_restriction_enabled=False, enabled=True)])
    f = next(x for x in findings if x["rule_id"] == "cf.no_geo_restriction")
    assert f["severity"] == "low"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_asset_list_returns_no_findings():
    assert scan_cloudfront([]) == []


def test_perfectly_secure_dist_returns_no_findings():
    """A distribution with all best practices applied should generate zero findings."""
    findings = scan_cloudfront([_dist()])
    assert findings == [], f"Unexpected findings on secure dist: {[f['rule_id'] for f in findings]}"


def test_multiple_distributions_are_scanned_independently():
    """Findings from dist A must not affect dist B."""
    secure = _dist(id="SECURE1")
    insecure = _dist(
        id="INSECURE1",
        http_allowed=True,
        waf_attached=False,
        web_acl_id="",
        access_logging_enabled=False,
    )
    findings = scan_cloudfront([secure, insecure])
    for f in findings:
        assert f["resource_id"] == "INSECURE1", \
            f"Finding {f['rule_id']} incorrectly attributed to secure distribution"


def test_finding_contains_required_fields():
    findings = scan_cloudfront([_dist(http_allowed=True)])
    f = findings[0]
    for field in ("rule_id", "resource_type", "resource_id", "severity", "title", "detail", "remediation"):
        assert field in f, f"Finding missing required field: {field}"


def test_resource_type_is_cloudfront():
    findings = scan_cloudfront([_dist(http_allowed=True)])
    assert all(f["resource_type"] == "cloudfront" for f in findings)


def test_region_is_global():
    findings = scan_cloudfront([_dist(http_allowed=True)])
    assert all(f["region"] == "global" for f in findings)
