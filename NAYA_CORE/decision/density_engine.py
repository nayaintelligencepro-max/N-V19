"""NAYA V19 - Density Engine - Moteur de densite pour scoring des opportunites"""
import logging, time
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.DECISION.DENSITY_ENGINE")

class DensityEngine:
    """Moteur de densite pour scoring des opportunites."""

    def __init__(self):
        self._history: List[Dict] = []

    DENSITY_THRESHOLDS = {"excellent": 500, "good": 200, "acceptable": 100, "low": 50}

    def score(self, value_eur: float, effort_hours: float) -> Dict:
        density = value_eur / max(effort_hours, 0.1)
        level = "low"
        for lev, thresh in sorted(self.DENSITY_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if density >= thresh:
                level = lev
                break
        return {"density": round(density, 2), "level": level, "value": value_eur, "effort_h": effort_hours}

    def filter_minimum(self, opps: list, min_density: float = 100) -> list:
        return [o for o in opps if o.get("value", 0) / max(o.get("effort_h", 1), 0.1) >= min_density]

    def get_stats(self) -> Dict:
        return {"history": len(self._history)}
