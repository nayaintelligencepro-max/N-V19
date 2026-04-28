"""NAYA CORE — System Watchdog"""
import time
import threading
import logging
from typing import Dict, Any, Optional, Callable

log = logging.getLogger("NAYA.MONITORING.WATCHDOG")

class SystemWatchdog:
    """Surveillance continue du système — détecte les anomalies et déclenche les actions correctives."""

    CHECK_INTERVAL_SECONDS = 30
    MAX_FAILURES = 3

    def __init__(self, runtime: Any = None):
        self.runtime = runtime
        self._running = False
        self._failures: Dict[str, int] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._thread: Optional[threading.Thread] = None
        self._checks_done = 0

    def monitor(self) -> Dict:
        """Single health check pass. Returns health status."""
        result = {"ok": True, "checks": {}, "ts": time.time()}
        if self.runtime:
            try:
                h = self.runtime.health_check()
                result["checks"]["runtime"] = h
                result["ok"] = h.get("ok", True) if isinstance(h, dict) else bool(h)
            except Exception as e:
                result["checks"]["runtime"] = {"ok": False, "error": str(e)}
                result["ok"] = False
        self._checks_done += 1
        return result

    def start(self) -> None:
        """Start continuous monitoring in background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="NAYA-WATCHDOG")
        self._thread.start()
        log.info("[WATCHDOG] Started")

    def stop(self) -> None:
        self._running = False
        log.info("[WATCHDOG] Stopped")

    def _loop(self) -> None:
        while self._running:
            try:
                result = self.monitor()
                if not result.get("ok"):
                    self._handle_failure("system", result)
                else:
                    self._failures.pop("system", None)
            except Exception as e:
                log.error(f"[WATCHDOG] Loop error: {e}")
            time.sleep(self.CHECK_INTERVAL_SECONDS)

    def _handle_failure(self, component: str, result: Dict) -> None:
        self._failures[component] = self._failures.get(component, 0) + 1
        count = self._failures[component]
        log.warning(f"[WATCHDOG] Failure #{count} for {component}")
        if count >= self.MAX_FAILURES:
            log.critical(f"[WATCHDOG] CRITICAL: {component} failed {count}x — triggering callback")
            cb = self._callbacks.get(component) or self._callbacks.get("*")
            if cb:
                try: cb(component, result)
                except Exception as e: log.error(f"[WATCHDOG] Callback error: {e}")

    def on_failure(self, component: str, callback: Callable) -> None:
        """Register callback for component failure (use '*' for any)."""
        self._callbacks[component] = callback

    @property
    def stats(self) -> Dict:
        return {"checks_done": self._checks_done, "active_failures": dict(self._failures), "running": self._running}
