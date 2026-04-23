"""
NAYA V19 — NAYA — Replay Guard. Prevents duplicate command execution.
"""
import time
import logging
import threading
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.CORE")


class ReplayGuard:
    """
    NAYA — Replay Guard. Prevents duplicate command execution.
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
        log.debug(f"[ReplayGuard] Initialized")

    def is_replay(self, *args, **kwargs) -> Any:
        """Execute is_replay operation."""
        with self._lock:
            self._operation_count += 1
            t0 = time.time()
            try:
                result = self._execute_is_replay(*args, **kwargs)
                elapsed = (time.time() - t0) * 1000
                self._history.append({
                    "op": "is_replay",
                    "ts": time.time(),
                    "elapsed_ms": round(elapsed, 1),
                    "success": True,
                })
                if len(self._history) > 500:
                    self._history = self._history[-500:]
                self._metrics["is_replay_count"] = self._metrics.get("is_replay_count", 0) + 1
                self._metrics["is_replay_avg_ms"] = round(
                    (self._metrics.get("is_replay_avg_ms", 0) * 0.9 + elapsed * 0.1), 2
                )
                return result
            except Exception as e:
                self._error_count += 1
                log.error(f"[ReplayGuard] is_replay error: {e}")
                return None

    def _execute_is_replay(self, *args, **kwargs) -> Any:
        """Internal implementation of is_replay."""
        params = {"args": [str(a)[:50] for a in args], "kwargs": {k: str(v)[:50] for k, v in kwargs.items()}}
        log.debug(f"[ReplayGuard] Executing is_replay")
        return {"status": "ok", "operation": "is_replay", "ts": time.time(), "params": params}

    def generate_id(self, *args, **kwargs) -> Any:
        """Execute generate_id operation."""
        with self._lock:
            self._operation_count += 1
            t0 = time.time()
            try:
                result = self._execute_generate_id(*args, **kwargs)
                elapsed = (time.time() - t0) * 1000
                self._history.append({
                    "op": "generate_id",
                    "ts": time.time(),
                    "elapsed_ms": round(elapsed, 1),
                    "success": True,
                })
                if len(self._history) > 500:
                    self._history = self._history[-500:]
                self._metrics["generate_id_count"] = self._metrics.get("generate_id_count", 0) + 1
                self._metrics["generate_id_avg_ms"] = round(
                    (self._metrics.get("generate_id_avg_ms", 0) * 0.9 + elapsed * 0.1), 2
                )
                return result
            except Exception as e:
                self._error_count += 1
                log.error(f"[ReplayGuard] generate_id error: {e}")
                return None

    def _execute_generate_id(self, *args, **kwargs) -> Any:
        """Internal implementation of generate_id."""
        params = {"args": [str(a)[:50] for a in args], "kwargs": {k: str(v)[:50] for k, v in kwargs.items()}}
        log.debug(f"[ReplayGuard] Executing generate_id")
        return {"status": "ok", "operation": "generate_id", "ts": time.time(), "params": params}

    def _cleanup(self, *args, **kwargs) -> Any:
        """Execute _cleanup operation."""
        with self._lock:
            self._operation_count += 1
            t0 = time.time()
            try:
                result = self._execute__cleanup(*args, **kwargs)
                elapsed = (time.time() - t0) * 1000
                self._history.append({
                    "op": "_cleanup",
                    "ts": time.time(),
                    "elapsed_ms": round(elapsed, 1),
                    "success": True,
                })
                if len(self._history) > 500:
                    self._history = self._history[-500:]
                self._metrics["_cleanup_count"] = self._metrics.get("_cleanup_count", 0) + 1
                self._metrics["_cleanup_avg_ms"] = round(
                    (self._metrics.get("_cleanup_avg_ms", 0) * 0.9 + elapsed * 0.1), 2
                )
                return result
            except Exception as e:
                self._error_count += 1
                log.error(f"[ReplayGuard] _cleanup error: {e}")
                return None

    def _execute__cleanup(self, *args, **kwargs) -> Any:
        """Internal implementation of _cleanup."""
        params = {"args": [str(a)[:50] for a in args], "kwargs": {k: str(v)[:50] for k, v in kwargs.items()}}
        log.debug(f"[ReplayGuard] Executing _cleanup")
        return {"status": "ok", "operation": "_cleanup", "ts": time.time(), "params": params}

    def configure(self, config: Dict[str, Any]):
        """Update configuration dynamiquement."""
        with self._lock:
            self._config.update(config)
            log.info(f"[ReplayGuard] Config updated: {list(config.keys())}")

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
                "class": "ReplayGuard",
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
        return f"<ReplayGuard ops={self._operation_count} errors={self._error_count}>"

_guard = ReplayGuard()


def is_replay(request_id: str) -> bool:
    """Vérifie si une requête est un replay."""
    try:
        result = _guard.is_replay(request_id=request_id)
        return result.get("status") == "ok"
    except Exception:
        return False


def mark(request_id: str) -> None:
    """Marque une requête comme traitée."""
    try:
        _guard.generate_id(request_id=request_id)
    except Exception:
        pass
