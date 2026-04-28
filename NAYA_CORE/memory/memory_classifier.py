"""NAYA V19 - MemoryClassifier - Classifie les souvenirs par type et importance"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.MEMORY.MEMORY_CLASSIFIER")

class MemoryClassifier:
    """Classifie les souvenirs par type et importance."""

    def __init__(self):
        self._log: List[Dict] = []

    CATEGORIES = {"pain_detected": "business", "revenue_event": "financial", "system_error": "technical", "evolution": "growth"}

    def classify(self, entry: Dict) -> str:
        entry_type = entry.get("type", "unknown")
        return self.CATEGORIES.get(entry_type, "general")

    def should_retain(self, entry: Dict) -> bool:
        if entry.get("revenue", 0) > 0: return True
        if entry.get("type") == "pain_detected": return True
        return entry.get("importance", 0.5) > 0.3

    def get_stats(self) -> Dict:
        return {"module": "memory_classifier"}
