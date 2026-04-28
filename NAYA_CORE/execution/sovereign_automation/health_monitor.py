"""NAYA V19 - Health Monitor - Monitore la sante de l automatisation."""
import time, logging, threading
from typing import Dict, List, Optional
log = logging.getLogger("NAYA.HEALTH.MON")

class AutomationHealthMonitor:
    """Surveille la sante de tous les composants d automatisation."""

    CHECK_INTERVAL = 60

    def __init__(self):
        self._components: Dict[str, Dict] = {}
        self._alerts: List[Dict] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def register_component(self, name: str, check_fn=None) -> None:
        self._components[name] = {
            "check_fn": check_fn, "status": "unknown",
            "last_check": 0, "consecutive_failures": 0
        }

    def check_all(self) -> Dict:
        results = {}
        for name, comp in self._components.items():
            try:
                if comp["check_fn"]:
                    healthy = comp["check_fn"]()
                else:
                    healthy = True
                comp["status"] = "healthy" if healthy else "unhealthy"
                comp["last_check"] = time.time()
                if not healthy:
                    comp["consecutive_failures"] += 1
                    if comp["consecutive_failures"] >= 3:
                        self._alerts.append({
                            "component": name, "type": "persistent_failure",
                            "failures": comp["consecutive_failures"], "ts": time.time()
                        })
                else:
                    comp["consecutive_failures"] = 0
                results[name] = comp["status"]
            except Exception as e:
                comp["status"] = "error"
                results[name] = "error"
        return results

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="HEALTH-MON", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                self.check_all()
            except Exception as e:
                log.error(f"[HEALTH] {e}")
            time.sleep(self.CHECK_INTERVAL)

    def get_alerts(self, limit: int = 20) -> List[Dict]:
        return self._alerts[-limit:]

    def get_stats(self) -> Dict:
        healthy = sum(1 for c in self._components.values() if c["status"] == "healthy")
        return {
            "components": len(self._components),
            "healthy": healthy,
            "alerts": len(self._alerts),
            "running": self._running
        }
