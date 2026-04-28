"""NAYA V19 - State Repository - Persistence de l etat systeme."""
import json, time, logging
from typing import Dict, Optional, Any
from pathlib import Path

log = logging.getLogger("NAYA.STATE.REPO")

STATE_FILE = Path("data/db/naya_state.json")

class StateRepository:
    """Repository pour persister et recuperer l etat du systeme."""

    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._load()

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value
        self._state["_updated_at"] = time.time()
        self._save()

    def get_all(self) -> Dict[str, Any]:
        return self._state.copy()

    def delete(self, key: str) -> bool:
        if key in self._state:
            del self._state[key]
            self._save()
            return True
        return False

    def increment(self, key: str, amount: float = 1) -> float:
        current = self._state.get(key, 0)
        new_val = current + amount
        self.set(key, new_val)
        return new_val

    def get_snapshot(self) -> Dict:
        return {
            "total_keys": len(self._state),
            "updated_at": self._state.get("_updated_at"),
            "keys": list(self._state.keys())
        }

    def _save(self) -> None:
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(json.dumps(self._state, indent=2, default=str))
        except Exception as e:
            log.debug(f"[STATE] Save: {e}")

    def _load(self) -> None:
        try:
            if STATE_FILE.exists():
                self._state = json.loads(STATE_FILE.read_text())
                log.info(f"[STATE] {len(self._state)} keys loaded")
        except Exception as e:
            log.debug(f"[STATE] Load: {e}")
            self._state = {}

_repo = None
def get_state_repo() -> StateRepository:
    global _repo
    if _repo is None:
        _repo = StateRepository()
    return _repo
