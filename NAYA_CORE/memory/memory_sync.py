"""NAYA V19 - MemorySync - Synchronisation memoire entre modules"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.MEMORY.MEMORY_SYNC")

class MemorySync:
    """Synchronisation memoire entre modules."""

    def __init__(self):
        self._log: List[Dict] = []

    def __init__(self):
        self._log = []
        self._pending = []

    def request_sync(self, source: str, target: str, data: Dict) -> Dict:
        req = {"source": source, "target": target, "data": data, "ts": time.time(), "synced": False}
        self._pending.append(req)
        return req

    def process_pending(self) -> int:
        processed = 0
        for req in self._pending:
            if not req["synced"]:
                req["synced"] = True; processed += 1
        return processed

    def get_pending_count(self) -> int:
        return sum(1 for r in self._pending if not r["synced"])

    def get_stats(self) -> Dict:
        return {"module": "memory_sync"}
