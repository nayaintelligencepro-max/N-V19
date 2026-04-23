"""NAYA V19 - Continuite du pipeline - Garantit que le pipeline ne se vide jamais"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.DOCTRINE.ENGINE_PIPELINE_CONTINUITY")

class EnginePipelineContinuity:
    """Garantit que le pipeline ne se vide jamais."""

    def __init__(self):
        self._log: List[Dict] = []

    MIN_PIPELINE_SIZE = 5
    REFILL_TRIGGER = 3

    def check_pipeline(self, pipeline_size: int, active_hunts: int) -> Dict:
        healthy = pipeline_size >= self.MIN_PIPELINE_SIZE
        needs_refill = pipeline_size <= self.REFILL_TRIGGER
        return {"healthy": healthy, "size": pipeline_size, "needs_refill": needs_refill,
                "action": "HUNT_NOW" if needs_refill else "MAINTAIN",
                "active_hunts": active_hunts}

    def recommend_hunt_intensity(self, pipeline_size: int) -> str:
        if pipeline_size <= 2: return "aggressive"
        if pipeline_size <= 5: return "active"
        if pipeline_size <= 10: return "moderate"
        return "passive"

    def get_stats(self) -> Dict:
        return {"module": "engine_pipeline_continuity", "log_size": len(self._log)}
