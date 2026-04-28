"""NAYA V19 - Economic Spectrum - Spectre economique et classification des opportunites."""
import logging
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger("NAYA.EXEC.SPECTRUM")

class EconomicTier(Enum):
    MICRO = "micro"           # 1k-5k EUR
    SMALL = "small"           # 5k-20k EUR
    MEDIUM = "medium"         # 20k-100k EUR
    LARGE = "large"           # 100k-500k EUR
    ENTERPRISE = "enterprise" # 500k-5M EUR
    MEGA = "mega"             # 5M-40M EUR

TIER_CONFIG = {
    EconomicTier.MICRO: {"min": 1000, "max": 5000, "effort_days": 1, "parallel_max": 4, "margin_pct": 80},
    EconomicTier.SMALL: {"min": 5000, "max": 20000, "effort_days": 3, "parallel_max": 3, "margin_pct": 75},
    EconomicTier.MEDIUM: {"min": 20000, "max": 100000, "effort_days": 14, "parallel_max": 2, "margin_pct": 70},
    EconomicTier.LARGE: {"min": 100000, "max": 500000, "effort_days": 30, "parallel_max": 1, "margin_pct": 65},
    EconomicTier.ENTERPRISE: {"min": 500000, "max": 5000000, "effort_days": 90, "parallel_max": 1, "margin_pct": 60},
    EconomicTier.MEGA: {"min": 5000000, "max": 40000000, "effort_days": 180, "parallel_max": 1, "margin_pct": 55},
}

class EconomicSpectrum:
    """Classe les opportunites par tier economique et optimise l allocation."""

    def classify(self, value_eur: float) -> Dict:
        for tier, cfg in TIER_CONFIG.items():
            if cfg["min"] <= value_eur < cfg["max"]:
                return {
                    "tier": tier.value, "config": cfg,
                    "value": value_eur, "density": value_eur / max(1, cfg["effort_days"])
                }
        if value_eur >= TIER_CONFIG[EconomicTier.MEGA]["max"]:
            return {"tier": "mega_plus", "value": value_eur}
        return {"tier": "below_floor", "value": value_eur, "action": "reject_or_batch"}

    def optimal_mix(self, budget_hours: int = 160) -> Dict:
        """Calcule le mix optimal d opportunites pour maximiser le revenu mensuel."""
        mix = {}
        remaining = budget_hours
        for tier in [EconomicTier.MICRO, EconomicTier.SMALL, EconomicTier.MEDIUM]:
            cfg = TIER_CONFIG[tier]
            effort_h = cfg["effort_days"] * 8
            if effort_h <= remaining:
                count = min(cfg["parallel_max"], remaining // effort_h)
                mix[tier.value] = {
                    "count": count, "effort_h_each": effort_h,
                    "revenue_each": (cfg["min"] + cfg["max"]) / 2,
                    "total_revenue": count * (cfg["min"] + cfg["max"]) / 2
                }
                remaining -= count * effort_h
        total_rev = sum(m["total_revenue"] for m in mix.values())
        return {"mix": mix, "total_projected_revenue": total_rev, "hours_used": budget_hours - remaining}

    def get_stats(self) -> Dict:
        return {"tiers": len(TIER_CONFIG), "floor": 1000, "ceiling": 40000000}
