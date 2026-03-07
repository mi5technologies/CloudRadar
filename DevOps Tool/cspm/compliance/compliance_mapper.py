"""Map findings to compliance framework controls."""
from typing import Any

from cspm.compliance.cis_checks import CIS_MAP
from cspm.compliance.soc2_checks import SOC2_MAP
from cspm.compliance.hipaa_checks import HIPAA_MAP
from cspm.compliance.pci_checks import PCI_MAP
from cspm.compliance.iso27001_checks import ISO27001_MAP

_FRAMEWORK_MAPS: dict[str, dict[str, str]] = {
    "cis": CIS_MAP,
    "soc2": SOC2_MAP,
    "hipaa": HIPAA_MAP,
    "pci": PCI_MAP,
    "iso27001": ISO27001_MAP,
}


def map_findings_to_controls(
    findings: list[dict],
    framework: str,
) -> dict[str, list[dict]]:
    """Return control_id -> list of failing findings."""
    m = _FRAMEWORK_MAPS.get(framework.lower(), {})
    control_failures: dict[str, list[dict]] = {}
    for f in findings:
        rule_id = f.get("rule_id", "")
        ctrl = m.get(rule_id)
        if ctrl:
            control_failures.setdefault(ctrl, []).append(f)
    return control_failures
