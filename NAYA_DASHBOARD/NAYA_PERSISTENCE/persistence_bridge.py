"""NAYA V19 - Persistence Bridge - Pont entre dashboard et persistence."""
import logging, time
from typing import Dict, Any, Optional
log = logging.getLogger("NAYA.PERSIST.BRIDGE")

class PersistenceBridge:
    """Pont entre le dashboard et le systeme de persistence."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._writes = 0
        self._reads = 0

    def save_dashboard_state(self, state: Dict) -> bool:
        try:
            from PERSISTENCE.database.db_manager import get_db
            db = get_db()
            db.execute("INSERT OR REPLACE INTO dashboard_state (key, value) VALUES (?, ?)",
                      ("current_state", str(state)))
            self._writes += 1
            return True
        except Exception as e:
            self._cache["last_state"] = state
            log.debug(f"[PERSIST-BRIDGE] DB save failed, cached: {e}")
            return False

    def load_dashboard_state(self) -> Dict:
        self._reads += 1
        try:
            from PERSISTENCE.database.db_manager import get_db
            result = get_db().fetch_one("SELECT value FROM dashboard_state WHERE key = ?", ("current_state",))
            return eval(result[0]) if result else {}
        except Exception:
            return self._cache.get("last_state", {})

    def save_user_preference(self, key: str, value: Any) -> None:
        self._cache[f"pref_{key}"] = value
        self._writes += 1

    def get_user_preference(self, key: str, default: Any = None) -> Any:
        self._reads += 1
        return self._cache.get(f"pref_{key}", default)

    def get_stats(self) -> Dict:
        return {"writes": self._writes, "reads": self._reads, "cache_keys": len(self._cache)}
