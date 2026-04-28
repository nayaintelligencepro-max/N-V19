"""NAYA V19 - Adaptative Memory Controller - Controleur memoire adaptatif - ajuste la retention"""
import logging, time
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.DECISION.ADAPTATIVE_MEMORY_CONTROLLER")

class AdaptativeMemoryController:
    """Controleur memoire adaptatif - ajuste la retention."""

    def __init__(self):
        self._history: List[Dict] = []

    def adjust_retention(self, memory_usage_pct: float) -> Dict:
        if memory_usage_pct > 90:
            return {"action": "aggressive_prune", "keep_last": 100}
        elif memory_usage_pct > 75:
            return {"action": "moderate_prune", "keep_last": 500}
        return {"action": "normal", "keep_last": 2000}

    def should_retain(self, entry: Dict, age_hours: float) -> bool:
        if entry.get("type") == "pain" and entry.get("revenue", 0) > 0:
            return True
        return age_hours < 168

    def get_stats(self) -> Dict:
        return {"history": len(self._history)}
