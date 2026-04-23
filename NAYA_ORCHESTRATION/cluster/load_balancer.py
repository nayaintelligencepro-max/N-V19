"""NAYA V19 - Load Balancer - Distribue la charge entre executeurs."""
import time, logging, threading
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.LB")

class LoadBalancer:
    """Distribue la charge entre les executeurs disponibles."""

    def __init__(self):
        self._executors: Dict[str, Dict] = {}
        self._round_robin_idx = 0
        self._lock = threading.Lock()
        self._total_routed = 0

    def register_executor(self, name: str, capacity: int = 10, weight: float = 1.0) -> None:
        with self._lock:
            self._executors[name] = {
                "capacity": capacity, "current_load": 0,
                "weight": weight, "healthy": True, "total_handled": 0
            }

    def route(self, task_type: str = "general") -> Optional[str]:
        """Route une tache vers l executeur le moins charge."""
        with self._lock:
            available = [(n, e) for n, e in self._executors.items()
                        if e["healthy"] and e["current_load"] < e["capacity"]]
            if not available:
                return None
            # Weighted least connections
            best = min(available, key=lambda x: x[1]["current_load"] / x[1]["weight"])
            best[1]["current_load"] += 1
            best[1]["total_handled"] += 1
            self._total_routed += 1
            return best[0]

    def release(self, executor_name: str) -> None:
        with self._lock:
            ex = self._executors.get(executor_name)
            if ex and ex["current_load"] > 0:
                ex["current_load"] -= 1

    def set_health(self, executor_name: str, healthy: bool) -> None:
        with self._lock:
            if executor_name in self._executors:
                self._executors[executor_name]["healthy"] = healthy

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "executors": len(self._executors),
                "total_routed": self._total_routed,
                "load": {n: e["current_load"] for n, e in self._executors.items()},
                "health": {n: e["healthy"] for n, e in self._executors.items()}
            }
