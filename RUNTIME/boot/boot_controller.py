"""NAYA V19 - Boot Controller - Controleur de demarrage unifie."""
import logging, time
from typing import Dict, List, Callable
log = logging.getLogger("NAYA.BOOT")

class BootController:
    def __init__(self):
        self._phases: List[Dict] = []
        self._boot_time: float = 0
        self._booted = False

    def add_phase(self, name: str, fn: Callable, critical: bool = True) -> None:
        self._phases.append({"name": name, "fn": fn, "critical": critical})

    def boot(self) -> Dict:
        start = time.time()
        results = []
        for phase in self._phases:
            t0 = time.time()
            try:
                phase["fn"]()
                results.append({"name": phase["name"], "status": "ok", "ms": round((time.time()-t0)*1000)})
            except Exception as e:
                results.append({"name": phase["name"], "status": "failed", "error": str(e)})
                if phase["critical"]:
                    log.error(f"[BOOT] Critical phase {phase['name']} failed: {e}")
        self._boot_time = time.time() - start
        self._booted = True
        return {"phases": results, "total_ms": round(self._boot_time * 1000), "booted": self._booted}
