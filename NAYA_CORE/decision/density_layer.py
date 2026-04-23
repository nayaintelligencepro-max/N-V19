"""NAYA V19 - Density Layer - Couche de densite - filtre par densite valeur/effort"""
import logging, time
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.DECISION.DENSITY_LAYER")

class DensityLayer:
    """Couche de densite - filtre par densite valeur/effort."""

    def __init__(self):
        self._history: List[Dict] = []

    def calculate_density(self, value: float, effort_hours: float) -> float:
        return value / max(effort_hours, 0.1)

    def filter_by_density(self, opps: list, min_density: float = 100) -> list:
        return [o for o in opps if self.calculate_density(o.get("value", 0), o.get("effort_h", 1)) >= min_density]

    def rank(self, opps: list) -> list:
        for o in opps:
            o["density"] = self.calculate_density(o.get("value", 0), o.get("effort_h", 1))
        return sorted(opps, key=lambda x: x["density"], reverse=True)

    def get_stats(self) -> Dict:
        return {"history": len(self._history)}
