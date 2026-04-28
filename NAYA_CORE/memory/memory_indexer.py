"""NAYA V19 - MemoryIndexer - Indexe les souvenirs pour recherche rapide"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.MEMORY.MEMORY_INDEXER")

class MemoryIndexer:
    """Indexe les souvenirs pour recherche rapide."""

    def __init__(self):
        self._log: List[Dict] = []

    def __init__(self):
        self._log = []
        self._index = {}

    def index(self, entry_id: str, keywords: list) -> None:
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower not in self._index: self._index[kw_lower] = []
            self._index[kw_lower].append(entry_id)

    def search(self, keyword: str) -> list:
        return self._index.get(keyword.lower(), [])

    def get_indexed_count(self) -> int:
        return sum(len(v) for v in self._index.values())

    def get_stats(self) -> Dict:
        return {"module": "memory_indexer"}
