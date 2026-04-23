"""NAYA V19 - Cost Pressure Index - Mesure la pression financiere de la douleur"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.PAIN.COST_PRESSURE_INDEX")

class CostPressureIndex:
    """Mesure la pression financiere de la douleur."""

    def __init__(self):
        self._log: List[Dict] = []

    def calculate(self, annual_cost: float, revenue: float, trend: str = "stable") -> Dict:
        ratio = annual_cost / revenue if revenue > 0 else 0
        trend_mult = {"growing": 1.3, "stable": 1.0, "shrinking": 0.8}.get(trend, 1.0)
        pressure = min(1.0, ratio * 10 * trend_mult)
        return {"pressure_index": round(pressure, 3), "cost_ratio": round(ratio, 4), "severity": "critical" if pressure > 0.7 else "moderate" if pressure > 0.4 else "low"}

    def is_actionable(self, pressure: float) -> bool:
        return pressure >= 0.4

    def get_stats(self) -> Dict:
        return {"module": "cost_pressure_index"}
