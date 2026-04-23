"""NAYA V19 - Runtime Loop - Boucle principale du runtime."""
import time, logging, threading
from typing import Dict, Callable, List
log = logging.getLogger("NAYA.LOOP")

class RuntimeLoop:
    """Boucle principale qui orchestre les ticks du systeme."""
    def __init__(self, interval: float = 60):
        self._interval = interval
        self._running = False
        self._thread = None
        self._handlers: List[Callable] = []
        self._tick_count = 0

    def register(self, handler: Callable) -> None:
        self._handlers.append(handler)

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="RUNTIME-LOOP")
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            self._tick_count += 1
            for handler in self._handlers:
                try:
                    handler()
                except Exception as e:
                    log.error(f"[LOOP] Handler error: {e}")
            time.sleep(self._interval)

    def get_stats(self) -> Dict:
        return {"running": self._running, "ticks": self._tick_count, "handlers": len(self._handlers)}
