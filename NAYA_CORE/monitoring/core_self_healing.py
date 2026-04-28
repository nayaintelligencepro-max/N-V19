"""NAYA V19 - Core Self Healing - Auto-reparation des modules defaillants."""
import time, logging, threading
from typing import Dict, List, Optional, Callable

log = logging.getLogger("NAYA.HEALING")

class SelfHealingEngine:
    """Detecte et repare automatiquement les modules defaillants sans arret global."""

    CHECK_INTERVAL = 60

    def __init__(self):
        self._monitors: Dict[str, Dict] = {}
        self._repairs: List[Dict] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._total_healed = 0

    def register_module(self, name: str, health_fn: Callable, repair_fn: Callable,
                        critical: bool = True) -> None:
        self._monitors[name] = {
            "health_fn": health_fn, "repair_fn": repair_fn,
            "critical": critical, "status": "unknown",
            "failures": 0, "last_check": 0
        }

    def check_and_heal(self) -> Dict:
        results = {}
        for name, mon in self._monitors.items():
            try:
                healthy = mon["health_fn"]()
                mon["status"] = "healthy" if healthy else "degraded"
                mon["last_check"] = time.time()
                if not healthy:
                    mon["failures"] += 1
                    log.warning(f"[HEALING] {name} degraded (failures={mon['failures']})")
                    try:
                        mon["repair_fn"]()
                        mon["status"] = "repaired"
                        self._total_healed += 1
                        self._repairs.append({"module": name, "ts": time.time(), "success": True})
                        log.info(f"[HEALING] {name} repare avec succes")
                    except Exception as e:
                        mon["status"] = "failed"
                        self._repairs.append({"module": name, "ts": time.time(), "success": False, "error": str(e)})
                        log.error(f"[HEALING] {name} reparation echouee: {e}")
                else:
                    mon["failures"] = 0
                results[name] = mon["status"]
            except Exception as e:
                results[name] = "error"
                log.error(f"[HEALING] Check {name}: {e}")
        return results

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="SELF-HEAL", daemon=True)
        self._thread.start()
        log.info("[HEALING] Self-healing engine started")

    def stop(self):
        self._running = False

    def _loop(self):
        time.sleep(30)
        while self._running:
            try:
                self.check_and_heal()
            except Exception as e:
                log.error(f"[HEALING] Loop: {e}")
            time.sleep(self.CHECK_INTERVAL)

    def get_stats(self) -> Dict:
        return {
            "monitored_modules": len(self._monitors),
            "total_healed": self._total_healed,
            "total_repairs": len(self._repairs),
            "module_statuses": {n: m["status"] for n, m in self._monitors.items()},
            "running": self._running
        }

_heal = None
_heal_lock = threading.Lock()
def get_self_healing():
    global _heal
    if _heal is None:
        with _heal_lock:
            if _heal is None:
                _heal = SelfHealingEngine()
    return _heal
