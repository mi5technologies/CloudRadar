"""GuardDuty detector discovery (checks if enabled in the region)."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        gd = get_client("guardduty", region)
        resp = gd.list_detectors()
        detector_ids = resp.get("DetectorIds", [])
        if not detector_ids:
            # Not enabled at all in this region
            assets.append({
                "id": f"guardduty-{region}",
                "type": "guardduty",
                "region": region,
                "enabled": False,
                "status": "NOT_CONFIGURED",
                "finding_publishing_frequency": None,
                "data_sources": {},
            })
        else:
            for det_id in detector_ids:
                try:
                    det = gd.get_detector(DetectorId=det_id)
                    assets.append({
                        "id": det_id,
                        "type": "guardduty",
                        "region": region,
                        "enabled": det.get("Status") == "ENABLED",
                        "status": det.get("Status"),
                        "finding_publishing_frequency": det.get("FindingPublishingFrequency"),
                        "data_sources": det.get("DataSources", {}),
                    })
                except Exception:
                    pass
    except Exception:
        # GuardDuty not available / no permission — treat as not enabled
        assets.append({
            "id": f"guardduty-{region}",
            "type": "guardduty",
            "region": region,
            "enabled": False,
            "status": "UNKNOWN",
            "finding_publishing_frequency": None,
            "data_sources": {},
        })
    return assets
