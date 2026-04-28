"""NAYA V19 - Execution Trigger - Declencheur d execution des decisions"""
import logging, time
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.DECISION.EXECUTION_TRIGGER")

class ExecutionTrigger:
    """Declencheur d execution des decisions."""

    def __init__(self):
        self._history: List[Dict] = []

    TRIGGER_CONDITIONS = {
        "immediate": {"min_urgency": 0.8, "min_solvability": 0.7},
        "scheduled": {"min_urgency": 0.5, "min_solvability": 0.5},
        "deferred": {"min_urgency": 0.0, "min_solvability": 0.3},
    }

    def should_trigger(self, urgency: float, solvability: float) -> str:
        for mode, conds in self.TRIGGER_CONDITIONS.items():
            if urgency >= conds["min_urgency"] and solvability >= conds["min_solvability"]:
                return mode
        return "deferred"

    def trigger(self, decision_id: str, mode: str) -> Dict:
        return {"decision_id": decision_id, "mode": mode, "triggered_at": time.time(), "status": "triggered"}

    def get_stats(self) -> Dict:
        return {"history": len(self._history)}
