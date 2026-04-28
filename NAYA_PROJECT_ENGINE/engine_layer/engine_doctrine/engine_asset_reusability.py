"""NAYA V19 - Reutilisabilite des assets - Score de reutilisabilite de chaque creation"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.DOCTRINE.ENGINE_ASSET_REUSABILITY")

class EngineAssetReusability:
    """Score de reutilisabilite de chaque creation."""

    def __init__(self):
        self._log: List[Dict] = []

    REUSABILITY_SCORES = {"chatbot": 0.95, "audit_template": 0.9, "saas": 0.85, "landing_page": 0.9, "report": 0.7, "custom_service": 0.5}

    def score(self, asset_type: str, sector: str) -> Dict:
        base = self.REUSABILITY_SCORES.get(asset_type, 0.6)
        sector_bonus = 0.1 if sector in ["tech", "pme", "commerce"] else 0.0
        return {"reusability": min(1.0, base + sector_bonus), "type": asset_type, "recyclable_sectors": self._find_sectors(asset_type)}

    def _find_sectors(self, asset_type: str) -> list:
        if asset_type in ("chatbot", "landing_page"): return ["tech", "pme", "commerce", "sante", "immobilier"]
        if asset_type == "audit_template": return ["pme", "industrie", "finance"]
        return ["general"]

    def get_stats(self) -> Dict:
        return {"module": "engine_asset_reusability", "log_size": len(self._log)}
