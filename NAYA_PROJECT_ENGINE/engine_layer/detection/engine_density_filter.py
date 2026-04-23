"""NAYA V19 - Engine Density Filter - Filtre les opportunites par densite."""
import logging
from typing import Dict, List
log = logging.getLogger("NAYA.DENSITY")

class EngineDensityFilter:
    """Filtre les opportunites par densite de valeur (valeur/effort)."""

    MIN_DENSITY = 100  # EUR par heure d effort minimum

    def filter(self, opportunities: List[Dict]) -> List[Dict]:
        filtered = []
        for opp in opportunities:
            value = opp.get("value", 0)
            effort_hours = opp.get("effort_hours", 1)
            density = value / effort_hours if effort_hours > 0 else 0
            opp["density"] = round(density, 2)
            if density >= self.MIN_DENSITY:
                filtered.append(opp)
        filtered.sort(key=lambda x: x["density"], reverse=True)
        return filtered

    def rank(self, opportunities: List[Dict]) -> List[Dict]:
        for opp in opportunities:
            value = opp.get("value", 0)
            effort = opp.get("effort_hours", 1)
            opp["density_rank"] = round(value / max(effort, 0.1), 2)
        return sorted(opportunities, key=lambda x: x["density_rank"], reverse=True)

    def get_stats(self) -> Dict:
        return {"min_density": self.MIN_DENSITY}
