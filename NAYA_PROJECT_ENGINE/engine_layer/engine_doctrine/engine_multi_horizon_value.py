"""NAYA V19 - Valeur multi-horizon - Evalue sur court/moyen/long terme"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.DOCTRINE.ENGINE_MULTI_HORIZON_VALUE")

class EngineMultiHorizonValue:
    """Evalue sur court/moyen/long terme."""

    def __init__(self):
        self._log: List[Dict] = []

    def evaluate(self, opp: Dict) -> Dict:
        short = opp.get("value_30d", 0)
        medium = opp.get("value_90d", 0)
        long_term = opp.get("value_365d", 0)
        total = short + medium * 0.8 + long_term * 0.5
        horizon = "short" if short > medium else "medium" if medium > long_term else "long"
        return {"total_weighted_value": round(total, 2), "dominant_horizon": horizon,
                "short": short, "medium": medium, "long": long_term}

    def prioritize_by_horizon(self, opps: list, target: str = "balanced") -> list:
        weights = {"short": (0.6, 0.25, 0.15), "balanced": (0.33, 0.33, 0.34), "long": (0.15, 0.25, 0.6)}
        ws, wm, wl = weights.get(target, weights["balanced"])
        for o in opps:
            o["horizon_score"] = o.get("value_30d",0)*ws + o.get("value_90d",0)*wm + o.get("value_365d",0)*wl
        return sorted(opps, key=lambda x: x["horizon_score"], reverse=True)

    def get_stats(self) -> Dict:
        return {"module": "engine_multi_horizon_value", "log_size": len(self._log)}
