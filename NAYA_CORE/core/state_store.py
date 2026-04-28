"""NAYA V19 - Core State Store - Etat en memoire du systeme."""
import time, logging, threading
from typing import Dict, Any, Optional

log = logging.getLogger("NAYA.STATE")

class CoreStateStore:
    """Store d etat central en memoire avec historique."""

    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._history: list = []
        self._lock = threading.RLock()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            old = self._state.get(key)
            self._state[key] = value
            self._history.append({"key": key, "old": old, "new": value, "ts": time.time()})
            if len(self._history) > 1000:
                self._history = self._history[-500:]

    def get_all(self) -> Dict:
        with self._lock:
            return self._state.copy()

    def get_history(self, key: str = None, limit: int = 20) -> list:
        with self._lock:
            h = self._history if key is None else [e for e in self._history if e["key"] == key]
            return h[-limit:]

    def get_stats(self) -> Dict:
        with self._lock:
            return {"keys": len(self._state), "history_size": len(self._history)}

_store = None
_lock = threading.Lock()
def get_state_store():
    global _store
    if _store is None:
        with _lock:
            if _store is None:
                _store = CoreStateStore()
    return _store
