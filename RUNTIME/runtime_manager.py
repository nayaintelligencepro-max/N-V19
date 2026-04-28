"""
NAYA — Runtime Manager
========================
Gère le cycle de vie du runtime NAYA: boot, health, shutdown.
"""
import os, time, logging, threading
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from datetime import datetime

log = logging.getLogger("NAYA.RUNTIME")

class RuntimePhase(Enum):
    INITIALIZING = "INITIALIZING"
    BOOTING      = "BOOTING"
    RUNNING      = "RUNNING"
    DEGRADED     = "DEGRADED"
    SHUTTING_DOWN= "SHUTTING_DOWN"
    STOPPED      = "STOPPED"

class RuntimeManager:
    """Gestionnaire du runtime NAYA — singleton."""

    _instance: Optional["RuntimeManager"] = None

    def __new__(cls):
        if cls._instance is None: cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"): return
        self._initialized = True
        self._phase = RuntimePhase.INITIALIZING
        self._start_time = time.time()
        self._health_checks: List[Callable[[], bool]] = []
        self._shutdown_hooks: List[Callable[[], None]] = []
        self._metrics: Dict[str, Any] = {}
        self._lock = threading.Lock()
        log.info("RuntimeManager initialized")

    # ---- Lifecycle ----

    def boot(self) -> bool:
        self._phase = RuntimePhase.BOOTING
        try:
            from NAYA_CORE.state.state_manager import get_state_manager
            state = get_state_manager()
            state.update("instance_id", f"NAYA-{int(self._start_time)}")
            self._phase = RuntimePhase.RUNNING
            log.info("Runtime RUNNING")
            return True
        except Exception as e:
            log.error(f"Boot failed: {e}")
            self._phase = RuntimePhase.DEGRADED
            return False

    def shutdown(self) -> None:
        self._phase = RuntimePhase.SHUTTING_DOWN
        for hook in self._shutdown_hooks:
            try: hook()
            except Exception as e: log.error(f"Shutdown hook error: {e}")
        self._phase = RuntimePhase.STOPPED
        log.info("Runtime STOPPED")

    # ---- Health ----

    def register_health_check(self, check: Callable[[], bool]) -> None:
        self._health_checks.append(check)

    def register_shutdown_hook(self, hook: Callable[[], None]) -> None:
        self._shutdown_hooks.append(hook)

    def health_check(self) -> Dict[str, Any]:
        results = []
        for check in self._health_checks:
            try: results.append(check())
            except Exception: results.append(False)
        all_healthy = all(results) if results else True
        if not all_healthy and self._phase == RuntimePhase.RUNNING:
            self._phase = RuntimePhase.DEGRADED
        return {
            "phase": self._phase.value,
            "healthy": all_healthy,
            "checks": len(self._health_checks),
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "uptime_hours": round((time.time() - self._start_time) / 3600, 2),
        }

    # ---- Metrics ----

    def record_metric(self, name: str, value: Any) -> None:
        with self._lock: self._metrics[name] = {"value": value, "ts": time.time()}

    def get_metrics(self) -> Dict[str, Any]:
        return dict(self._metrics)

    def get_status(self) -> Dict[str, Any]:
        return {
            "phase": self._phase.value,
            "started_at": datetime.fromtimestamp(self._start_time).isoformat(),
            "uptime_hours": round((time.time() - self._start_time) / 3600, 2),
            "health": self.health_check(),
            "metrics": self.get_metrics(),
            "environment": os.getenv("NAYA_ENV", "local"),
        }

    @property
    def is_running(self) -> bool:
        return self._phase in [RuntimePhase.RUNNING, RuntimePhase.DEGRADED]


def get_runtime() -> RuntimeManager:
    return RuntimeManager()
