"""API Gateway (REST and HTTP) discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        agw = get_client("apigateway", region)
        agwv2 = get_client("apigatewayv2", region)

        # REST APIs (v1)
        try:
            paginator = agw.get_paginator("get_rest_apis")
            for page in paginator.paginate():
                for api in page.get("items", []):
                    api_id = api.get("id")
                    stages = []
                    try:
                        stages_resp = agw.get_stages(restApiId=api_id)
                        stages = stages_resp.get("item", [])
                    except Exception:
                        pass
                    logging_enabled = any(
                        s.get("defaultRouteSettings", {}).get("loggingLevel") != "OFF"
                        or s.get("accessLogSettings")
                        for s in stages
                    )
                    waf_arns = [s.get("webAclArn") for s in stages if s.get("webAclArn")]
                    assets.append({
                        "id": api_id,
                        "name": api.get("name"),
                        "type": "api_gateway",
                        "api_version": "REST",
                        "region": region,
                        "logging_enabled": logging_enabled,
                        "waf_attached": len(waf_arns) > 0,
                        "stage_count": len(stages),
                    })
        except Exception:
            pass

        # HTTP/WebSocket APIs (v2)
        try:
            resp = agwv2.get_apis()
            for api in resp.get("Items", []):
                api_id = api.get("ApiId")
                stages: list[dict] = []
                try:
                    s_resp = agwv2.get_stages(ApiId=api_id)
                    stages = s_resp.get("Items", [])
                except Exception:
                    pass
                logging_enabled = any(
                    s.get("DefaultRouteSettings", {}).get("LoggingLevel") not in (None, "OFF")
                    or s.get("AccessLogSettings")
                    for s in stages
                )
                assets.append({
                    "id": api_id,
                    "name": api.get("Name"),
                    "type": "api_gateway",
                    "api_version": "HTTP",
                    "region": region,
                    "logging_enabled": logging_enabled,
                    "waf_attached": False,
                    "stage_count": len(stages),
                })
        except Exception:
            pass
    except Exception:
        pass
    return assets
