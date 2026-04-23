"""NAYA V19 - Dashboard State - Etat global du dashboard."""
import time, logging, threading
from typing import Dict, Any, Optional
log = logging.getLogger("NAYA.DASHBOARD.STATE")

class DashboardState:
    """Etat centralisere du dashboard TORI."""

    def __init__(self):
        self._state: Dict[str, Any] = {
            "current_view": "main",
            "theme": "dark",
            "notifications_enabled": True,
            "auto_refresh_s": 30,
            "panels_visible": ["system", "projects", "revenue", "monitoring"],
            "last_interaction": time.time()
        }
        self._lock = threading.RLock()
        self._change_log: list = []

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            old = self._state.get(key)
            self._state[key] = value
            self._state["last_interaction"] = time.time()
            self._change_log.append({"key": key, "old": old, "new": value, "ts": time.time()})

    def get_full_state(self) -> Dict:
        with self._lock:
            return self._state.copy()

    def toggle_panel(self, panel: str) -> bool:
        with self._lock:
            panels = self._state["panels_visible"]
            if panel in panels:
                panels.remove(panel)
                return False
            else:
                panels.append(panel)
                return True

    def get_stats(self) -> Dict:
        return {
            "current_view": self._state.get("current_view"),
            "panels": len(self._state.get("panels_visible", [])),
            "changes": len(self._change_log)
        }
