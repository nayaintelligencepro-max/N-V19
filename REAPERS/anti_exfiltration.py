"""NAYA REAPERS — Anti-Exfiltration Guard"""
import re
import logging
import hashlib
from typing import Dict, Any, List, Optional

log = logging.getLogger("NAYA.REAPERS.ANTI_EXFIL")

FORBIDDEN_PATTERNS = [
    r"SECRET[_\s]?KEY",
    r"API[_\s]?KEY",
    r"PASSWORD",
    r"PRIVATE[_\s]?KEY",
    r"-----BEGIN\s+(RSA\s+)?PRIVATE",
    # Token assigned to a variable: catches key=<40+ hex> but NOT hash mentions in reports
    r"(?i)(?:token|secret|key|password)\s*[=:]\s*['\"]?[0-9a-fA-F]{40,}['\"]?",
]

class AntiExfiltrationGuard:
    """Bloque toute tentative d'exfiltration de données sensibles hors du système."""

    def __init__(self):
        self._blocked_count = 0
        self._patterns = [re.compile(p, re.IGNORECASE) for p in FORBIDDEN_PATTERNS]
        self._allowed_hashes: set = set()

    def validate(self, payload: Any) -> bool:
        """
        Validate payload for exfiltration risk.
        Returns True if payload is safe, False if it should be blocked.
        """
        if payload is None:
            return False
        payload_str = str(payload)

        # Check length — block massive payloads
        if len(payload_str) > 50000:
            log.warning(f"[ANTI_EXFIL] Blocked oversized payload: {len(payload_str)} chars")
            self._blocked_count += 1
            return False

        # Check for sensitive patterns
        for pattern in self._patterns:
            if pattern.search(payload_str):
                # Allow if whitelisted hash
                ph = hashlib.sha256(payload_str.encode()).hexdigest()
                if ph not in self._allowed_hashes:
                    log.warning(f"[ANTI_EXFIL] Blocked sensitive pattern match: {pattern.pattern}")
                    self._blocked_count += 1
                    return False

        return True

    def validate_dict(self, data: Dict[str, Any], sensitive_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """Sanitize a dict — remove or mask sensitive keys."""
        sensitive_keys = sensitive_keys or ["password", "secret", "key", "token", "api_key"]
        result = {}
        for k, v in data.items():
            if any(s in k.lower() for s in sensitive_keys):
                result[k] = "***REDACTED***"
                log.debug(f"[ANTI_EXFIL] Redacted key: {k}")
            elif isinstance(v, dict):
                result[k] = self.validate_dict(v, sensitive_keys)
            else:
                result[k] = v
        return result

    def whitelist_payload(self, payload: str) -> None:
        """Explicitly whitelist a payload hash (for known-safe system outputs)."""
        ph = hashlib.sha256(payload.encode()).hexdigest()
        self._allowed_hashes.add(ph)

    @property
    def stats(self) -> Dict:
        return {"blocked_count": self._blocked_count, "whitelisted": len(self._allowed_hashes)}
