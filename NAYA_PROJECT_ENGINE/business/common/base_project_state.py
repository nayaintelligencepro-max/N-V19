"""Shared base project state for business projects."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List


log = logging.getLogger("NAYA.CORE")


class BaseProjectState:
    """Thread-safe base state for project lifecycle methods."""

    def __init__(self, class_label: str = "ProjectState") -> None:
        self._class_label = class_label
        self._lock = threading.RLock()
        self._initialized_at = time.time()
        self._history: List[Dict] = []
        self._metrics: Dict[str, float] = {}
        self._active = True
        self._operation_count = 0
        self._error_count = 0
        self._config: Dict[str, Any] = {}
        log.debug("[%s] Initialized", self._class_label)

    def activate(self, *args: Any, **kwargs: Any) -> Any:
        return self._run("activate", self._execute_activate, *args, **kwargs)

    def complete_mission(self, *args: Any, **kwargs: Any) -> Any:
        return self._run("complete_mission", self._execute_complete_mission, *args, **kwargs)

    def to_dict(self, *args: Any, **kwargs: Any) -> Any:
        return self._run("to_dict", self._execute_to_dict, *args, **kwargs)

    def _execute_activate(self, *args: Any, **kwargs: Any) -> Any:
        params = {"args": [str(a)[:50] for a in args], "kwargs": {k: str(v)[:50] for k, v in kwargs.items()}}
        return {"status": "ok", "operation": "activate", "ts": time.time(), "params": params}

    def _execute_complete_mission(self, *args: Any, **kwargs: Any) -> Any:
        params = {"args": [str(a)[:50] for a in args], "kwargs": {k: str(v)[:50] for k, v in kwargs.items()}}
        return {"status": "ok", "operation": "complete_mission", "ts": time.time(), "params": params}

    def _execute_to_dict(self, *args: Any, **kwargs: Any) -> Any:
        params = {"args": [str(a)[:50] for a in args], "kwargs": {k: str(v)[:50] for k, v in kwargs.items()}}
        return {"status": "ok", "operation": "to_dict", "ts": time.time(), "params": params}

    def configure(self, config: Dict[str, Any]) -> None:
        with self._lock:
            self._config.update(config)
            log.info("[%s] Config updated: %s", self._class_label, list(config.keys()))

    def reset(self) -> None:
        with self._lock:
            self._history.clear()
            self._metrics.clear()
            self._operation_count = 0
            self._error_count = 0

    def is_healthy(self) -> bool:
        if not self._active:
            return False
        if self._operation_count > 0:
            return (self._error_count / self._operation_count) <= 0.5
        return True

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            uptime = time.time() - self._initialized_at
            return {
                "class": self._class_label,
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

    def _run(self, op_name: str, handler: Any, *args: Any, **kwargs: Any) -> Any:
        with self._lock:
            self._operation_count += 1
            t0 = time.time()
            try:
                result = handler(*args, **kwargs)
                elapsed = (time.time() - t0) * 1000
                self._history.append({
                    "op": op_name,
                    "ts": time.time(),
                    "elapsed_ms": round(elapsed, 1),
                    "success": True,
                })
                if len(self._history) > 500:
                    self._history = self._history[-500:]
                self._metrics[f"{op_name}_count"] = self._metrics.get(f"{op_name}_count", 0) + 1
                self._metrics[f"{op_name}_avg_ms"] = round(
                    (self._metrics.get(f"{op_name}_avg_ms", 0) * 0.9 + elapsed * 0.1), 2
                )
                return result
            except Exception as exc:
                self._error_count += 1
                log.error("[%s] %s error: %s", self._class_label, op_name, exc)
                return None

    def __repr__(self) -> str:
        return f"<{self._class_label} ops={self._operation_count} errors={self._error_count}>"
