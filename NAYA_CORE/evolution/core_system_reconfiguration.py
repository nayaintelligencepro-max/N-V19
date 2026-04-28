"""NAYA V19 - Core System Reconfiguration - Reconfiguration dynamique du systeme."""
import logging, time
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.EVOLUTION.RECONFIG")

class CoreSystemReconfiguration:
    """Reconfigure le systeme dynamiquement sans arret."""

    def __init__(self):
        self._configs: Dict[str, Dict] = {}
        self._history: List[Dict] = []

    def register_configurable(self, module: str, params: Dict) -> None:
        self._configs[module] = {"params": params, "updated_at": time.time()}

    def reconfigure(self, module: str, new_params: Dict) -> Dict:
        old = self._configs.get(module, {}).get("params", {})
        self._configs[module] = {"params": new_params, "updated_at": time.time()}
        change = {"module": module, "old": old, "new": new_params, "ts": time.time()}
        self._history.append(change)
        log.info(f"[RECONFIG] {module} reconfigure: {list(new_params.keys())}")
        return change

    def rollback(self, module: str) -> Optional[Dict]:
        for change in reversed(self._history):
            if change["module"] == module:
                self._configs[module] = {"params": change["old"], "updated_at": time.time()}
                log.info(f"[RECONFIG] {module} rollback")
                return change["old"]
        return None

    def get_config(self, module: str) -> Dict:
        return self._configs.get(module, {}).get("params", {})

    def get_stats(self) -> Dict:
        return {
            "configurable_modules": len(self._configs),
            "total_reconfigurations": len(self._history),
            "modules": list(self._configs.keys())
        }
