"""Alert engine — Slack webhook + SMTP email notifications."""
from __future__ import annotations

import json
import smtplib
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from cspm.utils.logger import get_logger

logger = get_logger(__name__)

_SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def _severity_passes(finding_severity: str, min_severity: str) -> bool:
    finding_level = _SEVERITY_ORDER.get((finding_severity or "").lower(), 0)
    min_level = _SEVERITY_ORDER.get((min_severity or "").lower(), 0)
    return finding_level >= min_level


def _send_slack(message: str, webhook_url: str) -> None:
    payload = json.dumps({"text": message}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 204):
                logger.warning("Slack webhook returned status %s", resp.status)
    except urllib.error.URLError as exc:
        logger.error("Failed to send Slack alert: %s", exc)


def _send_email(subject: str, body: str, config: dict[str, Any]) -> None:
    smtp_host: str = config.get("smtp_host", "")
    smtp_port: int = int(config.get("smtp_port") or 587)
    smtp_user: str = config.get("smtp_user", "")
    smtp_password: str = config.get("smtp_password", "")
    to_addr: str = config.get("alert_email_to", "")
    from_addr: str = config.get("alert_email_from", smtp_user)

    if not smtp_host or not to_addr:
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.sendmail(from_addr, to_addr, msg.as_string())
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send email alert: %s", exc)


def send_alert(finding: dict[str, Any], config: dict[str, Any] | None = None) -> None:
    """Send an alert for a single finding.

    Sends to Slack if ``slack_webhook_url`` is present in *config*, and to
    email if ``smtp_host`` and ``alert_email_to`` are present.  Respects
    ``min_severity`` — findings below the threshold are silently dropped.
    """
    if not config:
        return

    severity = (finding.get("severity") or "").lower()
    min_sev = (config.get("min_severity") or "high").lower()
    if not _severity_passes(severity, min_sev):
        return

    resource = finding.get("resource_id") or finding.get("resource") or "unknown"
    rule = finding.get("rule_id") or finding.get("check") or "unknown"
    msg = (
        f"[CloudRadar] {severity.upper()} finding\n"
        f"Rule: {rule}\n"
        f"Resource: {resource}\n"
        f"Detail: {finding.get('message') or finding.get('detail') or ''}"
    )

    if config.get("slack_webhook_url"):
        _send_slack(msg, config["slack_webhook_url"])

    if config.get("smtp_host") and config.get("alert_email_to"):
        subject = f"[CloudRadar] {severity.upper()} — {rule} on {resource}"
        _send_email(subject, msg, config)


def send_scan_complete(summary: dict[str, Any], config: dict[str, Any] | None = None) -> None:
    """Fire a notification when a scan finishes."""
    if not config:
        return

    cloud = summary.get("cloud", "aws").upper()
    region = summary.get("region", "?")
    findings_count = summary.get("findings_count", 0)
    risk_score = summary.get("risk_score", "?")

    msg = (
        f"[CloudRadar] Scan complete — {cloud} {region}\n"
        f"Findings: {findings_count}  |  Risk score: {risk_score}"
    )

    if config.get("slack_webhook_url"):
        _send_slack(msg, config["slack_webhook_url"])

    if config.get("smtp_host") and config.get("alert_email_to"):
        subject = f"[CloudRadar] Scan complete — {cloud} {region}"
        _send_email(subject, msg, config)
