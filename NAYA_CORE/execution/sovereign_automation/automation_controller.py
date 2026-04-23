"""NAYA V19 - Automation Controller - Controleur central d automatisation."""
import time, logging
from typing import Dict, List, Optional, Callable
log = logging.getLogger("NAYA.AUTOMATION")

class AutomationController:
    """Orchestre les automatisations souveraines du systeme."""

    def __init__(self):
        self._automations: Dict[str, Dict] = {}
        self._running: Dict[str, bool] = {}
        self._total_runs = 0

    def register(self, name: str, handler: Callable, interval_seconds: int = 3600,
                 enabled: bool = True) -> None:
        self._automations[name] = {
            "handler": handler, "interval": interval_seconds,
            "enabled": enabled, "last_run": 0, "runs": 0, "errors": 0
        }
        self._running[name] = enabled

    def tick(self) -> List[str]:
        """Execute les automatisations dont l intervalle est ecoule."""
        now = time.time()
        executed = []
        for name, auto in self._automations.items():
            if not auto["enabled"]:
                continue
            if now - auto["last_run"] >= auto["interval"]:
                try:
                    auto["handler"]()
                    auto["last_run"] = now
                    auto["runs"] += 1
                    self._total_runs += 1
                    executed.append(name)
                except Exception as e:
                    auto["errors"] += 1
                    log.error(f"[AUTO] {name}: {e}")
        return executed

    def enable(self, name: str) -> None:
        if name in self._automations:
            self._automations[name]["enabled"] = True
            self._running[name] = True

    def disable(self, name: str) -> None:
        if name in self._automations:
            self._automations[name]["enabled"] = False
            self._running[name] = False

    def get_stats(self) -> Dict:
        return {
            "total_automations": len(self._automations),
            "enabled": sum(1 for a in self._automations.values() if a["enabled"]),
            "total_runs": self._total_runs,
            "automations": {n: {"runs": a["runs"], "errors": a["errors"], "enabled": a["enabled"]}
                           for n, a in self._automations.items()}
        }
