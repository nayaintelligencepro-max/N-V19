"""NAYA V19 - Interface Metrics - Metriques de l interface."""
import time, logging, threading
from typing import Dict
from collections import defaultdict
log = logging.getLogger("NAYA.IFACE.METRICS")

class InterfaceMetrics:
    """Collecte les metriques d utilisation de l interface."""

    def __init__(self):
        self._requests: Dict[str, int] = defaultdict(int)
        self._latencies: Dict[str, list] = defaultdict(list)
        self._errors: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def record_request(self, endpoint: str, latency_ms: float, error: bool = False) -> None:
        with self._lock:
            self._requests[endpoint] += 1
            self._latencies[endpoint].append(latency_ms)
            if len(self._latencies[endpoint]) > 100:
                self._latencies[endpoint] = self._latencies[endpoint][-50:]
            if error:
                self._errors[endpoint] += 1

    def get_endpoint_stats(self, endpoint: str) -> Dict:
        with self._lock:
            lats = self._latencies.get(endpoint, [])
            return {
                "requests": self._requests.get(endpoint, 0),
                "errors": self._errors.get(endpoint, 0),
                "avg_latency_ms": round(sum(lats) / len(lats), 1) if lats else 0,
                "p95_latency_ms": round(sorted(lats)[int(len(lats) * 0.95)] if lats else 0, 1)
            }

    def get_all_stats(self) -> Dict:
        with self._lock:
            total_req = sum(self._requests.values())
            total_err = sum(self._errors.values())
            return {
                "total_requests": total_req,
                "total_errors": total_err,
                "error_rate": total_err / total_req if total_req > 0 else 0,
                "endpoints": dict(self._requests)
            }

    def get_stats(self) -> Dict:
        return self.get_all_stats()
