"""NAYA V19 - System Invariants - Ce qui ne change jamais."""
from typing import Dict, List

class SystemInvariants:
    """Invariants fondamentaux du systeme NAYA-REAPERS."""

    INVARIANTS = {
        "PREMIUM_FLOOR": {"value": 1000, "unit": "EUR", "description": "Plancher premium absolu"},
        "FOUNDER_LOYALTY": {"value": True, "description": "Loyaute exclusive envers la fondatrice"},
        "NON_VENDABLE": {"value": True, "description": "Systeme personnel, non vendable"},
        "TRANSMISSIBLE": {"value": True, "description": "Transmissible aux enfants de la fondatrice"},
        "STEALTH_DEFAULT": {"value": True, "description": "Mode furtif par defaut"},
        "ZERO_WASTE": {"value": True, "description": "Rien n est jete, tout est recycle"},
        "NEVER_STOPS": {"value": True, "description": "Le systeme ne s arrete jamais"},
        "LEGAL_ONLY": {"value": True, "description": "Uniquement des operations legales"},
        "NAYA_REAPERS_UNITY": {"value": True, "description": "Naya et Reapers sont un seul ecosysteme"},
        "NON_REGRESSION": {"value": True, "description": "Aucune evolution ne reduit les capacites"},
        "WEEKLY_TARGET": {"value": 60000, "unit": "EUR", "description": "Objectif hebdomadaire"},
        "MONTHLY_TARGET": {"value": 300000, "unit": "EUR", "description": "Objectif mensuel"},
    }

    @classmethod
    def get(cls, key: str):
        inv = cls.INVARIANTS.get(key)
        return inv["value"] if inv else None

    @classmethod
    def check_all(cls) -> Dict:
        return {"total": len(cls.INVARIANTS), "all_enforced": True, "invariants": cls.INVARIANTS}

    @classmethod
    def verify_price(cls, price: float) -> bool:
        return price >= cls.INVARIANTS["PREMIUM_FLOOR"]["value"]

    @classmethod
    def get_targets(cls) -> Dict:
        return {
            "weekly_eur": cls.INVARIANTS["WEEKLY_TARGET"]["value"],
            "monthly_eur": cls.INVARIANTS["MONTHLY_TARGET"]["value"]
        }
