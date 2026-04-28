"""NAYA V19 - History Store - Historique des actions systeme."""
import time, json, logging
from typing import Dict, List
from pathlib import Path
from collections import deque

log = logging.getLogger("NAYA.HISTORY")
HISTORY_FILE = Path("data/cache/action_history.json")

class HistoryStore:
    def __init__(self, max_entries: int = 2000):
        self._history = deque(maxlen=max_entries)
        self._load()

    def add(self, action: str, module: str, data: Dict = None) -> None:
        entry = {"action": action, "module": module, "data": data or {}, "ts": time.time()}
        self._history.append(entry)
        if len(self._history) % 50 == 0:
            self._save()

    def get_recent(self, n: int = 20, module: str = None) -> List:
        entries = list(self._history)
        if module:
            entries = [e for e in entries if e["module"] == module]
        return entries[-n:]

    def search(self, keyword: str) -> List:
        return [e for e in self._history if keyword.lower() in str(e).lower()]

    def _save(self):
        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            HISTORY_FILE.write_text(json.dumps(list(self._history)[-500:], default=str))
        except Exception:
            pass

    def _load(self):
        try:
            if HISTORY_FILE.exists():
                for e in json.loads(HISTORY_FILE.read_text()):
                    self._history.append(e)
        except Exception:
            pass

    def get_stats(self) -> Dict:
        return {"total_entries": len(self._history)}
