"""NAYA V19 - Filtre d acceptabilite solution - Filtre si le prospect peut accepter la solution"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.PAIN.SOLUTION_ACCEPTABILITY_FILTER")

class SolutionAcceptabilityFilter:
    """Filtre si le prospect peut accepter la solution."""

    def __init__(self):
        self._log: List[Dict] = []

    def filter(self, prospect: Dict, solution: Dict) -> Dict:
        budget_ok = prospect.get("estimated_budget", 0) >= solution.get("price", 0) * 0.7
        tech_ok = prospect.get("tech_maturity", 0.5) >= solution.get("tech_requirement", 0.3)
        timing_ok = not prospect.get("in_freeze", False)
        acceptable = budget_ok and tech_ok and timing_ok
        blockers = []
        if not budget_ok: blockers.append("budget_insufficient")
        if not tech_ok: blockers.append("tech_maturity_low")
        if not timing_ok: blockers.append("budget_freeze")
        return {"acceptable": acceptable, "blockers": blockers, "recommendation": "PROCEED" if acceptable else "NURTURE"}

    def get_stats(self) -> Dict:
        return {"module": "solution_acceptability_filter"}
