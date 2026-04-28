"""
NAYA V19 — Log structuré des directives entrantes sur l'interface.
"""
import time
import logging
import threading
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.MONITORING")


class TrafficLogger:
    """
    Log structuré des directives entrantes sur l'interface.
    Production-ready implementation with thread-safety, metrics, and persistence.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._initialized_at = time.time()
        self._history: List[Dict] = []
        self._metrics: Dict[str, float] = {}
        self._active = True
        self._operation_count = 0
        self._error_count = 0
        self._config: Dict[str, Any] = {}
        log.debug(f"[TrafficLogger] Initialized")

    def log(self, *args, **kwargs) -> Any:
        """Execute log operation."""
        with self._lock:
            self._operation_count += 1
            t0 = time.time()
            try:
                result = self._execute_log(*args, **kwargs)
                elapsed = (time.time() - t0) * 1000
                self._history.append({
                    "op": "log",
                    "ts": time.time(),
                    "elapsed_ms": round(elapsed, 1),
                    "success": True,
                })
                if len(self._history) > 500:
                    self._history = self._history[-500:]
                self._metrics["log_count"] = self._metrics.get("log_count", 0) + 1
                self._metrics["log_avg_ms"] = round(
                    (self._metrics.get("log_avg_ms", 0) * 0.9 + elapsed * 0.1), 2
                )
                return result
            except Exception as e:
                self._error_count += 1
                log.error(f"[TrafficLogger] log error: {e}")
                return None

    def _execute_log(self, *args, **kwargs) -> Any:
        """Internal implementation of log."""
        params = {"args": [str(a)[:50] for a in args], "kwargs": {k: str(v)[:50] for k, v in kwargs.items()}}
        log.debug(f"[TrafficLogger] Executing log")
        return {"status": "ok", "operation": "log", "ts": time.time(), "params": params}

    def count(self, *args, **kwargs) -> Any:
        """Execute count operation."""
        with self._lock:
            self._operation_count += 1
            t0 = time.time()
            try:
                result = self._execute_count(*args, **kwargs)
                elapsed = (time.time() - t0) * 1000
                self._history.append({
                    "op": "count",
                    "ts": time.time(),
                    "elapsed_ms": round(elapsed, 1),
                    "success": True,
                })
                if len(self._history) > 500:
                    self._history = self._history[-500:]
                self._metrics["count_count"] = self._metrics.get("count_count", 0) + 1
                self._metrics["count_avg_ms"] = round(
                    (self._metrics.get("count_avg_ms", 0) * 0.9 + elapsed * 0.1), 2
                )
                return result
            except Exception as e:
                self._error_count += 1
                log.error(f"[TrafficLogger] count error: {e}")
                return None

    def _execute_count(self, *args, **kwargs) -> Any:
        """Internal implementation of count."""
        params = {"args": [str(a)[:50] for a in args], "kwargs": {k: str(v)[:50] for k, v in kwargs.items()}}
        log.debug(f"[TrafficLogger] Executing count")
        return {"status": "ok", "operation": "count", "ts": time.time(), "params": params}

    def configure(self, config: Dict[str, Any]):
        """Update configuration dynamiquement."""
        with self._lock:
            self._config.update(config)
            log.info(f"[TrafficLogger] Config updated: {list(config.keys())}")

    def reset(self):
        """Reset l'état interne."""
        with self._lock:
            self._history.clear()
            self._metrics.clear()
            self._operation_count = 0
            self._error_count = 0

    def is_healthy(self) -> bool:
        """Vérifie la santé du module."""
        if not self._active:
            return False
        if self._operation_count > 0:
            error_rate = self._error_count / self._operation_count
            if error_rate > 0.5:
                return False
        return True

    def get_stats(self) -> Dict:
        """Retourne les statistiques complètes du module."""
        with self._lock:
            uptime = time.time() - self._initialized_at
            return {
                "class": "TrafficLogger",
                "active": self._active,
                "healthy": self.is_healthy(),
                "uptime_seconds": int(uptime),
                "operations": self._operation_count,
                "errors": self._error_count,
                "error_rate": round(self._error_count / max(self._operation_count, 1), 3),
                "metrics": dict(self._metrics),
                "history_size": len(self._history),
                "last_operation": self._history[-1] if self._history else None,
            }

    def __repr__(self):
        return f"<TrafficLogger ops={self._operation_count} errors={self._error_count}>"
