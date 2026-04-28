"""NAYA V19 - Carte des besoins non exprimes - Mappe les besoins que les prospects n expriment pas"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.PAIN.UNSPOKEN_NEEDS_MAP")

class UnspokenNeedsMap:
    """Mappe les besoins que les prospects n expriment pas."""

    def __init__(self):
        self._log: List[Dict] = []

    UNSPOKEN_MAP = {
        "restaurant": ["automatisation commandes", "reduction gaspillage", "fidelisation client"],
        "pme": ["visibilite en ligne", "automatisation admin", "retention employes"],
        "sante": ["conformite RGPD", "gestion planning", "patient experience"],
        "immobilier": ["estimation precise", "generation leads", "gestion locative"],
        "finance": ["compliance automatisee", "detection fraude", "reporting temps reel"],
    }

    def get_unspoken(self, sector: str) -> list:
        return self.UNSPOKEN_MAP.get(sector, ["optimisation processus", "reduction couts", "croissance"])

    def match_solution(self, sector: str, available_solutions: list) -> list:
        needs = self.get_unspoken(sector)
        matches = []
        for need in needs:
            for sol in available_solutions:
                if any(k in sol.lower() for k in need.split()):
                    matches.append({"need": need, "solution": sol})
        return matches

    def get_stats(self) -> Dict:
        return {"module": "unspoken_needs_map"}
