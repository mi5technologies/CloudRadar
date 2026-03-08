"""CloudFront security scanner."""
from typing import Any

SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"


def _finding(asset: dict, rule_id: str, title: str, severity: str, detail: str, remediation: str) -> dict:
    return {
        "rule_id": rule_id,
        "resource_type": "cloudfront",
        "resource_id": asset.get("id"),
        "resource_name": asset.get("name") or asset.get("id"),
        "severity": severity,
        "title": title,
        "detail": detail,
        "remediation": remediation,
        "region": "global",
        "passed": False,
    }


def scan_cloudfront(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    for asset in assets:
        dist_id = asset.get("id", "unknown")

        # CF-01: Distribution allows HTTP (no redirect / https-only)
        if asset.get("http_allowed"):
            findings.append(_finding(
                asset,
                "cf.http_allowed",
                "CloudFront distribution allows plain HTTP",
                SEVERITY_HIGH,
                f"Distribution {dist_id} has at least one cache behaviour with ViewerProtocolPolicy=allow-all, meaning traffic can be served over unencrypted HTTP.",
                "Set ViewerProtocolPolicy to 'redirect-to-https' or 'https-only' on all cache behaviours.",
            ))

        # CF-02: No WAF Web ACL attached
        if not asset.get("waf_attached"):
            findings.append(_finding(
                asset,
                "cf.no_waf",
                "CloudFront distribution has no WAF Web ACL",
                SEVERITY_HIGH,
                f"Distribution {dist_id} has no AWS WAF Web ACL associated, leaving it unprotected against common web exploits (SQLi, XSS, bad bots).",
                "Create an AWS WAFv2 Web ACL with managed rule groups (AWSManagedRulesCommonRuleSet) and associate it with the CloudFront distribution.",
            ))

        # CF-03: Missing security headers policy (HSTS, X-Frame-Options, etc.)
        if not asset.get("security_headers_configured"):
            headers = asset.get("headers_config", {})
            missing = []
            if not headers.get("hsts_enabled"):
                missing.append("HSTS (Strict-Transport-Security)")
            if not headers.get("x_frame_options"):
                missing.append("X-Frame-Options")
            if not headers.get("content_type_options"):
                missing.append("X-Content-Type-Options")
            if not headers.get("xss_protection"):
                missing.append("X-XSS-Protection")
            missing_str = ", ".join(missing) if missing else "all security headers"
            findings.append(_finding(
                asset,
                "cf.missing_security_headers",
                "CloudFront distribution missing security response headers",
                SEVERITY_MEDIUM,
                f"Distribution {dist_id} is not sending {missing_str}. Without these headers, browsers lack protection against clickjacking, MIME sniffing, and XSS.",
                "Create a CloudFront Response Headers Policy with SecurityHeadersConfig (HSTS, X-Frame-Options: DENY, X-Content-Type-Options: nosniff, X-XSS-Protection) and associate it with all cache behaviours.",
            ))

        # CF-04: HSTS specifically missing (separate from general headers)
        if not asset.get("hsts_enabled") and asset.get("has_security_headers_policy"):
            findings.append(_finding(
                asset,
                "cf.no_hsts",
                "CloudFront distribution missing HSTS header",
                SEVERITY_MEDIUM,
                f"Distribution {dist_id} has a response headers policy but Strict-Transport-Security (HSTS) is not enabled, allowing downgrade attacks.",
                "Edit the Response Headers Policy for this distribution and enable Strict-Transport-Security with a max-age of at least 31536000 (1 year) and includeSubDomains.",
            ))

        # CF-05: Outdated TLS version
        if asset.get("tls_outdated"):
            findings.append(_finding(
                asset,
                "cf.outdated_tls",
                "CloudFront distribution uses outdated TLS protocol",
                SEVERITY_HIGH,
                f"Distribution {dist_id} allows TLS version {asset.get('tls_min_version')}. TLS 1.0 and 1.1 are deprecated and vulnerable (POODLE, BEAST).",
                "Update the ViewerCertificate MinimumProtocolVersion to TLSv1.2_2021 in the distribution settings.",
            ))

        # CF-06: S3 origins without Origin Access Control (OAC)
        if asset.get("origin_direct_access"):
            bad_origins = ", ".join(asset.get("s3_origins_without_oac", []))
            findings.append(_finding(
                asset,
                "cf.s3_origin_no_oac",
                "CloudFront S3 origin accessible without Origin Access Control",
                SEVERITY_HIGH,
                f"Distribution {dist_id} has S3 origins ({bad_origins}) not protected by an OAC or OAI. The S3 bucket may be directly accessible, bypassing CloudFront policies.",
                "Create an Origin Access Control (OAC) in CloudFront, associate it with the S3 origins, and update the S3 bucket policy to only allow access from the OAC principal.",
            ))

        # CF-07: Access logging disabled
        if not asset.get("access_logging_enabled"):
            findings.append(_finding(
                asset,
                "cf.logging_disabled",
                "CloudFront access logging is disabled",
                SEVERITY_MEDIUM,
                f"Distribution {dist_id} has no access log destination configured. Without logs, investigation of attacks, abuse, and traffic anomalies is severely hindered.",
                "Enable CloudFront access logging by specifying an S3 bucket as the logging destination in the distribution settings.",
            ))

        # CF-08: No geo restriction (informational — flag only for public-facing distributions)
        if not asset.get("geo_restriction_enabled") and asset.get("enabled"):
            findings.append(_finding(
                asset,
                "cf.no_geo_restriction",
                "CloudFront distribution has no geo restriction",
                SEVERITY_LOW,
                f"Distribution {dist_id} serves content globally without geo-restriction. If the application is region-specific, blocking unexpected countries reduces the attack surface.",
                "Review whether the application needs to serve content globally. If not, configure a geo-restriction allowlist or blocklist for known threat-origin countries.",
            ))

    return findings
