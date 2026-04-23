"""NAYA V19 - Orientation cash - Priorise les opportunites qui generent du cash rapide"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.DOCTRINE.ENGINE_CASH_ORIENTATION")

class EngineCashOrientation:
    """Priorise les opportunites qui generent du cash rapide."""

    def __init__(self):
        self._log: List[Dict] = []

    def prioritize(self, opportunities: list) -> list:
        for o in opportunities:
            cash_speed = 1.0 / max(o.get("days_to_cash", 1), 0.5)
            value = o.get("value", 0)
            o["cash_score"] = cash_speed * value
        return sorted(opportunities, key=lambda x: x["cash_score"], reverse=True)

    def is_cash_rapide(self, opp: Dict) -> bool:
        return opp.get("days_to_cash", 999) <= 3 and opp.get("value", 0) >= 1000

    def classify_speed(self, days: int) -> str:
        if days <= 3: return "flash"
        if days <= 7: return "rapide"
        if days <= 21: return "moyen"
        return "long_terme"

    def get_stats(self) -> Dict:
        return {"module": "engine_cash_orientation", "log_size": len(self._log)}
