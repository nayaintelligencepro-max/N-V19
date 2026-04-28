"""NAYA V19 - Premium Floor Enforcement"""
import logging
from typing import Dict, Optional

log = logging.getLogger("NAYA.CONSTITUTION.FLOOR")

class PremiumFloor:
    """Enforce le plancher premium sur toutes les operations."""

    ABSOLUTE_FLOOR = 1000  # EUR
    TIERS = {
        "cash_rapide": 1000,
        "premium": 5000,
        "executive": 20000,
        "enterprise": 50000,
        "strategic": 100000,
        "high_stakes": 500000,
        "mega_project": 15000000,
    }

    @classmethod
    def enforce(cls, price: float, tier: str = "cash_rapide") -> float:
        floor = cls.TIERS.get(tier, cls.ABSOLUTE_FLOOR)
        if price < floor:
            log.warning(f"[FLOOR] Prix {price} EUR sous plancher {tier} ({floor} EUR) -> ajuste")
            return float(floor)
        return price

    @classmethod
    def validate(cls, price: float) -> Dict:
        if price < cls.ABSOLUTE_FLOOR:
            return {"valid": False, "price": price, "floor": cls.ABSOLUTE_FLOOR,
                    "message": f"Prix {price} EUR sous le plancher absolu {cls.ABSOLUTE_FLOOR} EUR"}
        tier = "cash_rapide"
        for t, f in sorted(cls.TIERS.items(), key=lambda x: x[1], reverse=True):
            if price >= f:
                tier = t
                break
        return {"valid": True, "price": price, "tier": tier, "floor": cls.TIERS[tier]}

    @classmethod
    def get_tier_for_value(cls, value: float) -> str:
        for tier, floor in sorted(cls.TIERS.items(), key=lambda x: x[1], reverse=True):
            if value >= floor:
                return tier
        return "cash_rapide"

    @classmethod
    def get_all_tiers(cls) -> Dict:
        return cls.TIERS.copy()
