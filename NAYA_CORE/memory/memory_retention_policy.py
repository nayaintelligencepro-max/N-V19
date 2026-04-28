"""NAYA V19 - MemoryRetentionPolicy - Politique de retention des souvenirs"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.MEMORY.MEMORY_RETENTION_POLICY")

class MemoryRetentionPolicy:
    """Politique de retention des souvenirs."""

    def __init__(self):
        self._log: List[Dict] = []

    MAX_SHORT_TERM = 500
    MAX_MEDIUM_TERM = 2000
    MAX_LONG_TERM = 10000

    def should_prune(self, level: str, current_count: int) -> bool:
        limits = {"short_term": self.MAX_SHORT_TERM, "medium_term": self.MAX_MEDIUM_TERM, "long_term": self.MAX_LONG_TERM}
        return current_count > limits.get(level, 1000)

    def prune_count(self, level: str, current_count: int) -> int:
        limits = {"short_term": self.MAX_SHORT_TERM, "medium_term": self.MAX_MEDIUM_TERM, "long_term": self.MAX_LONG_TERM}
        limit = limits.get(level, 1000)
        return max(0, current_count - int(limit * 0.8))

    def retention_hours(self, entry_type: str) -> int:
        HOURS = {"pain_detected": 8760, "revenue": 87600, "error": 168, "general": 720}
        return HOURS.get(entry_type, 720)

    def get_stats(self) -> Dict:
        return {"module": "memory_retention_policy"}
