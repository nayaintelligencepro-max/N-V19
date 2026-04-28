"""NAYA V19 - MemoryClusterBridge - Pont memoire entre les noeuds du cluster"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.MEMORY.MEMORY_CLUSTER_BRIDGE")

class MemoryClusterBridge:
    """Pont memoire entre les noeuds du cluster."""

    def __init__(self):
        self._log: List[Dict] = []

    def __init__(self):
        self._log = []
        self._sync_queue = []

    def queue_sync(self, memory_entry: Dict, target_node: str = "all") -> None:
        self._sync_queue.append({"entry": memory_entry, "target": target_node, "ts": time.time()})

    def get_pending_syncs(self) -> list:
        return self._sync_queue.copy()

    def mark_synced(self, idx: int) -> None:
        if 0 <= idx < len(self._sync_queue):
            self._sync_queue.pop(idx)

    def get_stats(self) -> Dict:
        return {"module": "memory_cluster_bridge"}
