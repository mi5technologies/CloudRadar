"""CloudFront distribution discovery (AWS — global service, us-east-1)."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str = "us-east-1") -> list[dict[str, Any]]:
    """Discover CloudFront distributions and their security configuration."""
    assets: list[dict[str, Any]] = []
    try:
        # CloudFront is a global service — must use us-east-1
        cf = get_client("cloudfront", "us-east-1")
        paginator = cf.get_paginator("list_distributions")
        for page in paginator.paginate():
            dist_list = page.get("DistributionList", {})
            for item in dist_list.get("Items", []):
                dist_id = item.get("Id")
                dist_config = {}
                try:
                    detail = cf.get_distribution_config(Id=dist_id)
                    dist_config = detail.get("DistributionConfig", {})
                except Exception:
                    pass

                # Check WAF (WebACLId set means WAF v1; WebACLId empty and no WAFv2 = no WAF)
                web_acl_id = dist_config.get("WebACLId", "") or item.get("WebACLId", "")
                waf_attached = bool(web_acl_id)

                # Viewer protocol policy across all cache behaviours
                viewer_protocols = []
                default_cb = dist_config.get("DefaultCacheBehavior", {})
                if default_cb:
                    viewer_protocols.append(default_cb.get("ViewerProtocolPolicy", "allow-all"))
                for cb in (dist_config.get("CacheBehaviors", {}) or {}).get("Items", []):
                    viewer_protocols.append(cb.get("ViewerProtocolPolicy", "allow-all"))

                http_allowed = any(p == "allow-all" for p in viewer_protocols)
                https_only = all(p in ("https-only", "redirect-to-https") for p in viewer_protocols) if viewer_protocols else False

                # TLS minimum version
                viewer_cert = dist_config.get("ViewerCertificate", {})
                tls_min = viewer_cert.get("MinimumProtocolVersion", "")
                tls_outdated = tls_min not in ("TLSv1.2_2021", "TLSv1.2_2019", "TLSv1.2_2018", "") if tls_min else False

                # Security headers (via Response Headers Policy)
                default_headers_policy_id = default_cb.get("ResponseHeadersPolicyId", "")
                has_security_headers_policy = bool(default_headers_policy_id)

                headers_config = {}
                if default_headers_policy_id:
                    try:
                        policy = cf.get_response_headers_policy(Id=default_headers_policy_id)
                        policy_config = policy.get("ResponseHeadersPolicy", {}).get("ResponseHeadersPolicyConfig", {})
                        sh = policy_config.get("SecurityHeadersConfig", {})
                        headers_config = {
                            "hsts_enabled": bool(sh.get("StrictTransportSecurity", {}).get("AccessControlMaxAgeSec")),
                            "x_frame_options": bool(sh.get("FrameOptions", {})),
                            "content_type_options": bool(sh.get("ContentTypeOptions", {})),
                            "xss_protection": bool(sh.get("XSSProtection", {})),
                            "referrer_policy": bool(sh.get("ReferrerPolicy", {})),
                        }
                    except Exception:
                        headers_config = {}

                hsts_enabled = headers_config.get("hsts_enabled", False)
                security_headers_configured = has_security_headers_policy and hsts_enabled

                # Origin access (S3 origins should use OAC or OAI)
                origins = dist_config.get("Origins", {}).get("Items", [])
                s3_origins_without_oac = []
                for origin in origins:
                    domain = origin.get("DomainName", "")
                    if ".s3." in domain or domain.endswith(".s3.amazonaws.com"):
                        oac = origin.get("OriginAccessControlId", "")
                        oai = (origin.get("S3OriginConfig") or {}).get("OriginAccessIdentity", "")
                        if not oac and not oai:
                            s3_origins_without_oac.append(origin.get("Id", domain))

                # Geo restriction
                geo_restriction = dist_config.get("Restrictions", {}).get("GeoRestriction", {})
                geo_restriction_enabled = geo_restriction.get("RestrictionType", "none") != "none"

                # Access logging
                logging_cfg = dist_config.get("Logging", {})
                access_logging_enabled = bool(logging_cfg.get("Bucket"))

                # Origins count
                origin_count = len(origins)

                assets.append({
                    "id": dist_id,
                    "name": item.get("DomainName", dist_id),
                    "type": "cloudfront",
                    "region": "global",
                    "domain_name": item.get("DomainName"),
                    "aliases": item.get("Aliases", {}).get("Items", []),
                    "enabled": item.get("Enabled", True),
                    "status": item.get("Status"),
                    "waf_attached": waf_attached,
                    "web_acl_id": web_acl_id,
                    "http_allowed": http_allowed,
                    "https_only": https_only,
                    "viewer_protocols": viewer_protocols,
                    "tls_min_version": tls_min,
                    "tls_outdated": tls_outdated,
                    "security_headers_configured": security_headers_configured,
                    "hsts_enabled": hsts_enabled,
                    "has_security_headers_policy": has_security_headers_policy,
                    "headers_config": headers_config,
                    "s3_origins_without_oac": s3_origins_without_oac,
                    "origin_direct_access": len(s3_origins_without_oac) > 0,
                    "geo_restriction_enabled": geo_restriction_enabled,
                    "access_logging_enabled": access_logging_enabled,
                    "origin_count": origin_count,
                    "price_class": dist_config.get("PriceClass", ""),
                    "comment": dist_config.get("Comment", ""),
                })
    except Exception:
        pass
    return assets
