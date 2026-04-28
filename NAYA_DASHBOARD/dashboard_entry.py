"""NAYA V19 - Dashboard Entry - Point d entree du dashboard."""
import logging
from typing import Dict
log = logging.getLogger("NAYA.DASHBOARD")

class NayaDashboard:
    """Alias souverain pour DashboardEntry — point d'entrée dashboard NAYA."""

    def __init__(self):
        self._entry = DashboardEntry()

    def initialize(self):
        return self._entry.initialize()

    def get_component(self, name: str):
        return self._entry.get_component(name)

    def get_stats(self):
        return self._entry.get_stats()


class DashboardEntry:
    """Point d entree principal du dashboard TORI."""

    def __init__(self):
        self._initialized = False
        self._components: Dict[str, object] = {}

    def initialize(self) -> Dict:
        loaded = []
        components = [
            ("state", "NAYA_DASHBOARD.dashboard_state", "DashboardState"),
            ("bridge", "NAYA_DASHBOARD.dashboard_bridge", "DashboardBridge"),
            ("alerts", "NAYA_DASHBOARD.NAYA_MONITORING.alerts_engine", "AlertsEngine"),
            ("performance", "NAYA_DASHBOARD.NAYA_MONITORING.performance_tracker", "PerformanceTracker"),
        ]
        for name, mod_path, cls_name in components:
            try:
                mod = __import__(mod_path, fromlist=[cls_name])
                cls = getattr(mod, cls_name)
                self._components[name] = cls()
                loaded.append(name)
            except Exception as e:
                log.warning(f"[DASHBOARD] {name}: {e}")
        self._initialized = True
        return {"initialized": True, "loaded": loaded, "total": len(loaded)}

    def get_component(self, name: str):
        return self._components.get(name)

    def get_stats(self) -> Dict:
        return {"initialized": self._initialized, "components": list(self._components.keys())}

# Alias for backward compatibility
NayaDashboard = DashboardEntry
