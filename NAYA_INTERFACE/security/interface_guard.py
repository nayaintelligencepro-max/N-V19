"""NAYA V19 - Interface Guard - Garde de securite de l interface."""
import time, logging, hashlib
from typing import Dict, List, Optional
log = logging.getLogger("NAYA.IFACE.GUARD")

class InterfaceGuard:
    """Protege l interface contre les acces non autorises."""

    def __init__(self):
        self._blocked_ips: set = set()
        self._request_log: List[Dict] = []
        self._suspicious_patterns: List[str] = [
            "DROP TABLE", "SELECT *", "<script>", "../", "eval(", "exec(",
        ]

    def check_request(self, request: Dict) -> Dict:
        ip = request.get("ip", "unknown")
        path = request.get("path", "")
        body = request.get("body", "")

        if ip in self._blocked_ips:
            return {"allowed": False, "reason": "ip_blocked"}

        # Check for injection
        for pattern in self._suspicious_patterns:
            if pattern.lower() in body.lower() or pattern.lower() in path.lower():
                self._blocked_ips.add(ip)
                log.warning(f"[GUARD] Suspicious request blocked from {ip}: {pattern}")
                return {"allowed": False, "reason": f"suspicious_pattern: {pattern}"}

        self._request_log.append({"ip": ip, "path": path, "ts": time.time()})
        if len(self._request_log) > 1000:
            self._request_log = self._request_log[-500:]
        return {"allowed": True}

    def block_ip(self, ip: str) -> None:
        self._blocked_ips.add(ip)

    def unblock_ip(self, ip: str) -> None:
        self._blocked_ips.discard(ip)

    def get_stats(self) -> Dict:
        return {
            "blocked_ips": len(self._blocked_ips),
            "total_requests": len(self._request_log),
            "patterns_monitored": len(self._suspicious_patterns)
        }
