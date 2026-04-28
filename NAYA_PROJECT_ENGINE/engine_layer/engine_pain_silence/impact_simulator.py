"""NAYA V19 - Simulateur d impact - Simule l impact de la resolution de la douleur"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.PAIN.IMPACT_SIMULATOR")

class ImpactSimulator:
    """Simule l impact de la resolution de la douleur."""

    def __init__(self):
        self._log: List[Dict] = []

    def simulate(self, current_cost: float, solution_price: float, timeline_months: int = 12) -> Dict:
        monthly_savings = current_cost / 12
        roi_month = solution_price / monthly_savings if monthly_savings > 0 else 999
        year_1_savings = monthly_savings * min(12, max(0, 12 - roi_month))
        return {"solution_price": solution_price, "annual_cost_eliminated": current_cost,
                "monthly_savings": round(monthly_savings, 2), "roi_months": round(roi_month, 1),
                "year_1_net_savings": round(year_1_savings - solution_price, 2),
                "5_year_savings": round(current_cost * 5 - solution_price, 2),
                "roi_multiplier": round(current_cost / solution_price, 1) if solution_price > 0 else 0}

    def get_stats(self) -> Dict:
        return {"module": "impact_simulator"}
