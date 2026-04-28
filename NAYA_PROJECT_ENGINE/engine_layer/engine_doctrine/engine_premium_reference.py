"""NAYA V19 - Reference premium - Maintient les references de prix premium"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.DOCTRINE.ENGINE_PREMIUM_REFERENCE")

class EnginePremiumReference:
    """Maintient les references de prix premium."""

    def __init__(self):
        self._log: List[Dict] = []

    PREMIUM_REFS = {
        "audit_express": {"floor": 1000, "avg": 3000, "ceiling": 10000},
        "chatbot_ia": {"floor": 2000, "avg": 7000, "ceiling": 25000},
        "saas_custom": {"floor": 5000, "avg": 15000, "ceiling": 50000},
        "diagnostic_strategique": {"floor": 3000, "avg": 8000, "ceiling": 30000},
        "transformation_digitale": {"floor": 10000, "avg": 40000, "ceiling": 100000},
        "mega_projet": {"floor": 15000000, "avg": 25000000, "ceiling": 40000000},
    }

    def get_reference(self, offer_type: str) -> Dict:
        return self.PREMIUM_REFS.get(offer_type, {"floor": 1000, "avg": 5000, "ceiling": 20000})

    def validate_price(self, offer_type: str, price: float) -> Dict:
        ref = self.get_reference(offer_type)
        return {"valid": price >= ref["floor"], "floor": ref["floor"], "vs_avg": round(price / ref["avg"], 2)}

    def get_stats(self) -> Dict:
        return {"module": "engine_premium_reference", "log_size": len(self._log)}
