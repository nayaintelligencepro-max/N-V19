"""NAYA V19 - MemoryHierarchy - Hierarchie de memoire: court/moyen/long terme"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.MEMORY.MEMORY_HIERARCHY")

class MemoryHierarchy:
    """Hierarchie de memoire: court/moyen/long terme."""

    def __init__(self):
        self._log: List[Dict] = []

    def __init__(self):
        self._log = []
        self._short_term = []
        self._medium_term = []
        self._long_term = []

    def store(self, entry: Dict, importance: float = 0.5) -> str:
        if importance >= 0.8: self._long_term.append(entry); return "long_term"
        if importance >= 0.4: self._medium_term.append(entry); return "medium_term"
        self._short_term.append(entry); return "short_term"

    def promote(self) -> int:
        promoted = 0
        for e in self._short_term[:]:
            if e.get("access_count", 0) >= 3:
                self._medium_term.append(e); self._short_term.remove(e); promoted += 1
        return promoted

    def get_stats(self) -> Dict:
        return {"module": "memory_hierarchy"}
