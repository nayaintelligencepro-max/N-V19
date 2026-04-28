"""NAYA V19 - Plancher de valeur - Enforce le plancher sur toutes les operations"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.DOCTRINE.ENGINE_VALUE_FLOOR")

class EngineValueFloor:
    """Enforce le plancher sur toutes les operations."""

    def __init__(self):
        self._log: List[Dict] = []

    ABSOLUTE_FLOOR = 1000

    def enforce(self, value: float) -> float:
        return max(value, self.ABSOLUTE_FLOOR)

    def check(self, value: float) -> Dict:
        ok = value >= self.ABSOLUTE_FLOOR
        return {"valid": ok, "value": value, "floor": self.ABSOLUTE_FLOOR,
                "action": "OK" if ok else f"ADJUST to {self.ABSOLUTE_FLOOR}"}

    def batch_enforce(self, values: list) -> list:
        return [self.enforce(v) for v in values]

    def get_stats(self) -> Dict:
        return {"module": "engine_value_floor", "log_size": len(self._log)}
