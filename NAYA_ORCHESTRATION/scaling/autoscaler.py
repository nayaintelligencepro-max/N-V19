"""NAYA V19 - Autoscaler - Scaling dynamique base sur les metriques."""
import time, logging, threading
from typing import Dict, Optional

log = logging.getLogger("NAYA.AUTOSCALE")

class Autoscaler:
    """Scale automatiquement les ressources selon la charge."""

    MIN_WORKERS = 1
    MAX_WORKERS = 10
    SCALE_UP_THRESHOLD = 0.75
    SCALE_DOWN_THRESHOLD = 0.25
    COOLDOWN_SECONDS = 120

    def __init__(self):
        self._current_workers = self.MIN_WORKERS
        self._last_scale_action = 0.0
        self._metrics_history: list = []
        self._total_scale_ups = 0
        self._total_scale_downs = 0

    def evaluate(self, current_load: float, queue_size: int = 0,
                 active_hunts: int = 0) -> Dict:
        """Evalue si un scaling est necessaire."""
        now = time.time()
        self._metrics_history.append({
            "load": current_load, "queue": queue_size,
            "hunts": active_hunts, "workers": self._current_workers, "ts": now
        })
        if len(self._metrics_history) > 500:
            self._metrics_history = self._metrics_history[-250:]

        if now - self._last_scale_action < self.COOLDOWN_SECONDS:
            return {"action": "cooldown", "workers": self._current_workers}

        action = "none"
        if current_load > self.SCALE_UP_THRESHOLD and self._current_workers < self.MAX_WORKERS:
            self._current_workers += 1
            self._total_scale_ups += 1
            self._last_scale_action = now
            action = "scale_up"
            log.info(f"[AUTOSCALE] Scale UP -> {self._current_workers} workers (load={current_load:.2f})")
        elif current_load < self.SCALE_DOWN_THRESHOLD and self._current_workers > self.MIN_WORKERS:
            self._current_workers -= 1
            self._total_scale_downs += 1
            self._last_scale_action = now
            action = "scale_down"
            log.info(f"[AUTOSCALE] Scale DOWN -> {self._current_workers} workers (load={current_load:.2f})")

        return {
            "action": action, "workers": self._current_workers,
            "load": current_load, "queue": queue_size
        }

    def get_stats(self) -> Dict:
        return {
            "current_workers": self._current_workers,
            "min": self.MIN_WORKERS, "max": self.MAX_WORKERS,
            "total_scale_ups": self._total_scale_ups,
            "total_scale_downs": self._total_scale_downs,
            "metrics_points": len(self._metrics_history)
        }
