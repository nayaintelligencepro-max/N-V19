"""
NAYA V19 — Runtime anti-debug & suspicious environment detection.
"""
import os
import sys
import time
import logging
import threading
from typing import Dict, List, Any

log = logging.getLogger("NAYA.REAPERS.WATCHDOG")


class RuntimeWatchdog:
    """
    Anti-debug and runtime environment validation.
    debugger_detected() and suspicious_environment() return bool.
    Thread-safe. Tracks metrics.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._initialized_at = time.time()
        self._history: List[Dict] = []
        self._metrics: Dict[str, float] = {}
        self._active = True
        self._operation_count = 0
        self._error_count = 0
        log.debug("[RuntimeWatchdog] Initialized")

    # ------------------------------------------------------------------
    # PUBLIC API — returns bool
    # ------------------------------------------------------------------

    def debugger_detected(self) -> bool:
        """
        Return True if a debugger or tracing tool is attached to this process.
        Checks sys.gettrace() and known debugger environment variables.
        """
        with self._lock:
            self._operation_count += 1
            try:
                result = self._execute_debugger_detected()
                self._record_history("debugger_detected", result)
                return result
            except Exception as e:
                self._error_count += 1
                log.error(f"[RuntimeWatchdog] debugger_detected error: {e}")
                return False

    def suspicious_environment(self) -> bool:
        """
        Return True if the runtime environment looks suspicious
        (VM indicators, sandbox markers, CI/test runner env vars active in prod).
        """
        with self._lock:
            self._operation_count += 1
            try:
                result = self._execute_suspicious_environment()
                self._record_history("suspicious_environment", result)
                return result
            except Exception as e:
                self._error_count += 1
                log.error(f"[RuntimeWatchdog] suspicious_environment error: {e}")
                return False

    # ------------------------------------------------------------------
    # INTERNAL — real detection logic
    # ------------------------------------------------------------------

    def _execute_debugger_detected(self) -> bool:
        """Detect active debugger/tracer."""
        # Python trace hook set (pdb, coverage, debugpy, etc.)
        if sys.gettrace() is not None:
            log.debug("[RuntimeWatchdog] sys.gettrace() active — debugger suspected")
            return True
        # Known debugger env vars
        debugger_env_vars = ["PYDEVD_USE_FRAME_EVAL", "PYCHARM_DEBUG", "VSCODE_DEBUGGER",
                             "PYTHONINSPECT", "PYTHONDEBUG"]
        for var in debugger_env_vars:
            if os.environ.get(var):
                log.debug(f"[RuntimeWatchdog] Debugger env var set: {var}")
                return True
        return False

    def _execute_suspicious_environment(self) -> bool:
        """Detect VM / sandbox / unexpected runtime environment."""
        suspicious_vars = [
            "FAKETIME",          # libfaketime
            "LD_PRELOAD",        # lib injection
            "DYLD_INSERT_LIBRARIES",  # macOS lib injection
        ]
        for var in suspicious_vars:
            val = os.environ.get(var, "")
            if val and "naya" not in val.lower():
                log.debug(f"[RuntimeWatchdog] Suspicious env var: {var}={val[:40]}")
                return True
        return False

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _record_history(self, op: str, result: bool) -> None:
        self._history.append({"op": op, "ts": time.time(), "result": result})
        if len(self._history) > 500:
            self._history = self._history[-500:]
        key = f"{op}_count"
        self._metrics[key] = self._metrics.get(key, 0) + 1

    # ------------------------------------------------------------------
    # HEALTH / STATS
    # ------------------------------------------------------------------

    def is_healthy(self) -> bool:
        if not self._active:
            return False
        if self._operation_count > 0:
            if self._error_count / self._operation_count > 0.5:
                return False
        return True

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "class": "RuntimeWatchdog",
                "active": self._active,
                "healthy": self.is_healthy(),
                "uptime_seconds": int(time.time() - self._initialized_at),
                "operations": self._operation_count,
                "errors": self._error_count,
                "metrics": dict(self._metrics),
                "last_operation": self._history[-1] if self._history else None,
            }

    def __repr__(self):
        return f"<RuntimeWatchdog ops={self._operation_count} errors={self._error_count}>"
