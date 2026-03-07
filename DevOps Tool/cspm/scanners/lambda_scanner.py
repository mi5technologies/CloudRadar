"""Lambda scanner: timeout and environment variable secret detection."""
import re
from typing import Any

_SECRET_KEY_PATTERNS = re.compile(
    r"(password|secret|token|key|passwd|pwd|api_key|apikey|access_key|auth)",
    re.IGNORECASE,
)
_AWS_KEY_PREFIXES = ("AKIA", "ASIA")
_MIN_SECRET_VALUE_LEN = 20


def _has_secrets_in_env(env: dict) -> bool:
    if not env:
        return False
    for k, v in env.items():
        if isinstance(v, str):
            if any(v.startswith(prefix) for prefix in _AWS_KEY_PREFIXES):
                return True
            if _SECRET_KEY_PATTERNS.search(k) and len(v) > _MIN_SECRET_VALUE_LEN:
                return True
    return False


def scan_lambda(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for a in assets:
        a = dict(a)
        timeout = a.get("timeout") or 0
        a["timeout_high"] = timeout > 300
        env = a.get("env_vars") or a.get("environment") or {}
        a["env_secrets_detected"] = _has_secrets_in_env(env)
        enriched.append(a)
    return enriched
