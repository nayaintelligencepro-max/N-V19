"""NAYA V19 - Performance Tracker - Suivi des performances systeme."""
import time, logging
from typing import Dict, List
from collections import deque
log = logging.getLogger("NAYA.PERF")

class PerformanceTracker:
    """Track les metriques de performance cles du systeme."""

    def __init__(self, window_size: int = 100):
        self._metrics: Dict[str, deque] = {}
        self._window = window_size
        self._baselines: Dict[str, float] = {}

    def record(self, metric: str, value: float) -> None:
        if metric not in self._metrics:
            self._metrics[metric] = deque(maxlen=self._window)
        self._metrics[metric].append({"value": value, "ts": time.time()})

    def set_baseline(self, metric: str, value: float) -> None:
        self._baselines[metric] = value

    def get_current(self, metric: str) -> float:
        data = self._metrics.get(metric)
        if not data:
            return 0
        return data[-1]["value"]

    def get_average(self, metric: str, last_n: int = 0) -> float:
        data = list(self._metrics.get(metric, []))
        if last_n > 0:
            data = data[-last_n:]
        if not data:
            return 0
        return sum(d["value"] for d in data) / len(data)

    def get_trend(self, metric: str) -> str:
        data = list(self._metrics.get(metric, []))
        if len(data) < 10:
            return "insufficient_data"
        recent = sum(d["value"] for d in data[-5:]) / 5
        older = sum(d["value"] for d in data[:5]) / 5
        if recent > older * 1.1:
            return "improving"
        elif recent < older * 0.9:
            return "declining"
        return "stable"

    def detect_anomaly(self, metric: str) -> Dict:
        avg = self.get_average(metric)
        current = self.get_current(metric)
        if avg == 0:
            return {"anomaly": False}
        deviation = abs(current - avg) / avg
        return {
            "anomaly": deviation > 0.5,
            "deviation": round(deviation, 3),
            "current": current, "average": round(avg, 3)
        }

    def get_dashboard_summary(self) -> Dict:
        summary = {}
        for metric in self._metrics:
            summary[metric] = {
                "current": round(self.get_current(metric), 3),
                "average": round(self.get_average(metric), 3),
                "trend": self.get_trend(metric),
                "anomaly": self.detect_anomaly(metric)["anomaly"]
            }
        return summary

    def get_stats(self) -> Dict:
        return {
            "metrics_tracked": len(self._metrics),
            "baselines_set": len(self._baselines),
            "summary": self.get_dashboard_summary()
        }

    def is_degraded(self) -> bool:
        """Retourne True si un indicateur de dégradation est détecté."""
        for metric in list(self._metrics.keys()):
            if self.detect_anomaly(metric).get("anomaly"):
                return True
        return False

    def track(self, metrics: Dict) -> None:
        """Enregistre un dict de métriques."""
        for name, value in metrics.items():
            if isinstance(value, (int, float)):
                self.record(name, float(value))


# Module-level singleton and convenience function
_tracker = PerformanceTracker()


def track(metrics: Dict) -> None:
    """Enregistre un snapshot de métriques dans le tracker de performance."""
    for name, value in metrics.items():
        if isinstance(value, (int, float)):
            _tracker.record(name, float(value))
