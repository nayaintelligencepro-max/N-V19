"""NAYA V19 - Core Runtime - Runtime d execution du core."""
import time, logging, threading
from typing import Dict
log = logging.getLogger("NAYA.CORE.RUNTIME")

class NayaCoreRuntime:
    def __init__(self):
        self._running = False
        self._start_time = 0.0
        self._cycle_count = 0

    def start(self) -> None:
        self._running = True
        self._start_time = time.time()
        log.info("[CORE-RT] Runtime started")

    def stop(self) -> None:
        self._running = False

    def tick(self) -> None:
        self._cycle_count += 1

    def get_uptime(self) -> float:
        return time.time() - self._start_time if self._running else 0

    def get_stats(self) -> Dict:
        return {
            "running": self._running,
            "uptime_s": round(self.get_uptime(), 1),
            "cycles": self._cycle_count
        }
