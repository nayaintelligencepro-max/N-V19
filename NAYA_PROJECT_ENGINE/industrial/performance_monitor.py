"""NAYA V19 - Industrial Performance Monitor."""
import time, logging
from typing import Dict, List

log = logging.getLogger("NAYA.INDUSTRIAL")

class IndustrialPerformanceMonitor:
    def __init__(self):
        self._metrics: List[Dict] = []
        self._kpis: Dict[str, float] = {}

    def record_kpi(self, name: str, value: float) -> None:
        self._kpis[name] = value
        self._metrics.append({"kpi": name, "value": value, "ts": time.time()})

    def get_performance(self) -> Dict:
        return {
            "kpis": self._kpis,
            "total_metrics": len(self._metrics),
            "health": "good" if all(v > 0.5 for v in self._kpis.values()) else "degraded"
        }

    def get_stats(self) -> Dict:
        return self.get_performance()

    def register_project(self, name: str) -> None:
        self._kpis[name] = 1.0

    def update_state(self, name: str, state) -> None:
        self._kpis[name] = 1.0
        self._metrics.append({"project": name, "state": str(state), "ts": time.time()})

    def get_project_metrics(self, name: str) -> Dict:
        return {"project": name, "kpi": self._kpis.get(name, 0)}

    def get_all_metrics(self) -> Dict:
        return {"projects": self._kpis, "total_metrics": len(self._metrics)}


# Alias expected by industrial_controller and __init__
PerformanceMonitor = IndustrialPerformanceMonitor
