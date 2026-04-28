"""NAYA V19 - Health Server - Serveur de sante minimal pour Docker/K8s."""
import logging, time
from typing import Dict
log = logging.getLogger("NAYA.HEALTH")

class HealthServer:
    def __init__(self):
        self._start_time = time.time()
        self._checks: Dict[str, bool] = {}

    def register_check(self, name: str, healthy: bool = True) -> None:
        self._checks[name] = healthy

    def is_healthy(self) -> bool:
        return all(self._checks.values()) if self._checks else True

    def get_health(self) -> Dict:
        return {
            "status": "healthy" if self.is_healthy() else "unhealthy",
            "uptime_s": round(time.time() - self._start_time, 1),
            "checks": self._checks
        }
