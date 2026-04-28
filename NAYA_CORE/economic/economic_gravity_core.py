"""NAYA V19 - Economic Gravity - Attraction des opportunites haute valeur."""
import logging, math
from typing import Dict, List

log = logging.getLogger("NAYA.ECONOMIC.GRAVITY")

class EconomicGravityCore:
    """Modele gravitationnel: les grosses opportunites attirent plus de ressources."""

    GRAVITY_CONSTANT = 0.1

    def __init__(self):
        self._mass_map: Dict[str, float] = {}

    def set_opportunity_mass(self, opp_id: str, value_eur: float, urgency: float = 0.5) -> None:
        mass = value_eur * (1 + urgency)
        self._mass_map[opp_id] = mass

    def calculate_pull(self, opp_id: str) -> float:
        mass = self._mass_map.get(opp_id, 0)
        if mass <= 0:
            return 0
        return self.GRAVITY_CONSTANT * math.log1p(mass)

    def rank_by_gravity(self) -> List[Dict]:
        ranked = []
        for oid, mass in self._mass_map.items():
            pull = self.calculate_pull(oid)
            ranked.append({"id": oid, "mass": mass, "pull": round(pull, 3)})
        ranked.sort(key=lambda x: x["pull"], reverse=True)
        return ranked

    def allocate_resources(self, total_resources: int = 10) -> Dict[str, int]:
        ranked = self.rank_by_gravity()
        total_pull = sum(r["pull"] for r in ranked) or 1
        allocation = {}
        for r in ranked:
            share = max(1, int(total_resources * r["pull"] / total_pull))
            allocation[r["id"]] = share
        return allocation

    def get_stats(self) -> Dict:
        return {
            "tracked": len(self._mass_map),
            "total_mass": sum(self._mass_map.values()),
            "top_5": self.rank_by_gravity()[:5]
        }
