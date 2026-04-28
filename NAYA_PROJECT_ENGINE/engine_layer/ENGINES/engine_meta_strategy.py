"""NAYA V19 - Engine Meta Strategy - Strategie meta pour le project engine."""
import logging
from typing import Dict, List
log = logging.getLogger("NAYA.ENGINE.META")

class EngineMetaStrategy:
    """Strategie meta: decide quel moteur utiliser pour quelle opportunite."""

    ENGINE_MAP = {
        "cash_rapide": {"engine": "Engine_cash_rapide", "priority": 1, "max_parallel": 4},
        "mega_project": {"engine": "mega_project_hunter", "priority": 2, "max_parallel": 1},
        "ecommerce": {"engine": "business_model_engine", "priority": 3, "max_parallel": 2},
        "immobilier": {"engine": "acquisition_engine", "priority": 4, "max_parallel": 1},
        "marche_oublie": {"engine": "forgotten_market_conqueror", "priority": 3, "max_parallel": 2},
    }

    def route_opportunity(self, opp_type: str) -> Dict:
        config = self.ENGINE_MAP.get(opp_type)
        if not config:
            return {"engine": "cash_rapide", "reason": "default fallback"}
        return config

    def get_parallel_capacity(self) -> int:
        return sum(e["max_parallel"] for e in self.ENGINE_MAP.values())

    def get_stats(self) -> Dict:
        return {"engines": len(self.ENGINE_MAP), "total_capacity": self.get_parallel_capacity()}
