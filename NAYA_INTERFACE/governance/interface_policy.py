"""NAYA V19 - Interface Policy - Politiques de l interface."""
import logging, time
from typing import Dict, List

log = logging.getLogger("NAYA.INTERFACE.POLICY")

class InterfacePolicy:
    """Politiques de securite et de gouvernance de l interface."""

    RATE_LIMITS = {
        "founder": {"requests_per_min": 1000, "unlimited": True},
        "tori": {"requests_per_min": 200, "unlimited": False},
        "system": {"requests_per_min": 500, "unlimited": False},
        "external": {"requests_per_min": 30, "unlimited": False},
    }

    CONTENT_POLICIES = {
        "max_payload_bytes": 10_000_000,  # 10MB
        "allowed_content_types": ["application/json", "text/plain", "multipart/form-data"],
        "require_authentication": True,
        "cors_origins": ["*"],  # Configurable via env
    }

    def __init__(self):
        self._request_counts: Dict[str, List[float]] = {}

    def check_rate_limit(self, actor: str) -> Dict:
        config = self.RATE_LIMITS.get(actor, self.RATE_LIMITS["external"])
        if config["unlimited"]:
            return {"allowed": True, "remaining": -1}
        now = time.time()
        if actor not in self._request_counts:
            self._request_counts[actor] = []
        # Clean old entries
        self._request_counts[actor] = [t for t in self._request_counts[actor] if now - t < 60]
        count = len(self._request_counts[actor])
        limit = config["requests_per_min"]
        if count >= limit:
            return {"allowed": False, "remaining": 0, "retry_after_s": 60}
        self._request_counts[actor].append(now)
        return {"allowed": True, "remaining": limit - count - 1}

    def validate_payload(self, size_bytes: int, content_type: str) -> Dict:
        if size_bytes > self.CONTENT_POLICIES["max_payload_bytes"]:
            return {"valid": False, "reason": "Payload too large"}
        if content_type not in self.CONTENT_POLICIES["allowed_content_types"]:
            return {"valid": False, "reason": f"Content type {content_type} not allowed"}
        return {"valid": True}

    def get_stats(self) -> Dict:
        return {
            "actors_tracked": len(self._request_counts),
            "total_requests": sum(len(v) for v in self._request_counts.values())
        }
