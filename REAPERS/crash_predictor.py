"""NAYA V19 - Crash Predictor - Predit les crashs avant qu ils arrivent."""
import time, logging, threading
from typing import Dict, List, Optional
from collections import deque

log = logging.getLogger("NAYA.REAPERS.PREDICT")

class CrashPredictor:
    """Analyse les patterns pour predire les crashs imminents."""

    WINDOW_SIZE = 100
    ALERT_THRESHOLD = 0.7

    def __init__(self):
        self._error_window = deque(maxlen=self.WINDOW_SIZE)
        self._latency_window = deque(maxlen=self.WINDOW_SIZE)
        self._memory_window = deque(maxlen=self.WINDOW_SIZE)
        self._predictions: List[Dict] = []
        self._total_predictions = 0
        self._prevented_crashes = 0

    def record_metric(self, metric_type: str, value: float) -> None:
        ts = time.time()
        if metric_type == "error_rate":
            self._error_window.append((ts, value))
        elif metric_type == "latency":
            self._latency_window.append((ts, value))
        elif metric_type == "memory_usage":
            self._memory_window.append((ts, value))

    def predict(self) -> Dict:
        """Analyse les tendances et predit les risques de crash."""
        risk_score = 0.0
        factors = []

        # Error rate trend
        if len(self._error_window) >= 10:
            recent = [v for _, v in list(self._error_window)[-10:]]
            older = [v for _, v in list(self._error_window)[:10]]
            if older:
                avg_recent = sum(recent) / len(recent)
                avg_older = sum(older) / len(older) if sum(older) > 0 else 0.01
                if avg_recent > avg_older * 2:
                    risk_score += 0.4
                    factors.append("error_rate_increasing")

        # Latency trend
        if len(self._latency_window) >= 10:
            recent_lat = [v for _, v in list(self._latency_window)[-10:]]
            avg_lat = sum(recent_lat) / len(recent_lat)
            if avg_lat > 5.0:
                risk_score += 0.3
                factors.append("high_latency")

        # Memory trend
        if len(self._memory_window) >= 5:
            recent_mem = [v for _, v in list(self._memory_window)[-5:]]
            avg_mem = sum(recent_mem) / len(recent_mem)
            if avg_mem > 0.85:
                risk_score += 0.3
                factors.append("memory_pressure")

        risk_score = min(1.0, risk_score)
        prediction = {
            "risk_score": round(risk_score, 3),
            "crash_imminent": risk_score >= self.ALERT_THRESHOLD,
            "factors": factors,
            "recommendation": "PREVENTIVE_ACTION" if risk_score >= self.ALERT_THRESHOLD else "MONITOR",
            "ts": time.time()
        }

        if prediction["crash_imminent"]:
            self._predictions.append(prediction)
            self._total_predictions += 1
            log.warning(f"[PREDICTOR] Crash imminent! Score={risk_score:.2f} Facteurs={factors}")

        return prediction

    def record_prevented(self) -> None:
        self._prevented_crashes += 1

    def get_stats(self) -> Dict:
        return {
            "data_points": {
                "errors": len(self._error_window),
                "latency": len(self._latency_window),
                "memory": len(self._memory_window)
            },
            "total_predictions": self._total_predictions,
            "prevented_crashes": self._prevented_crashes,
            "last_prediction": self._predictions[-1] if self._predictions else None
        }
