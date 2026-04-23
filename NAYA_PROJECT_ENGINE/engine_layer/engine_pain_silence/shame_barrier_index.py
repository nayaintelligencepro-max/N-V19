"""NAYA V19 - Shame Barrier Index - Mesure la barriere de honte des prospects."""
import logging
from typing import Dict
log = logging.getLogger("NAYA.PAIN.SHAME")

class ShameBarrierIndex:
    """Les douleurs les plus rentables sont celles dont on a honte de parler."""

    SECTOR_SHAME = {
        "finance": 0.8, "sante": 0.7, "gouvernement": 0.9,
        "industrie": 0.6, "tech": 0.4, "restaurant": 0.3,
        "immobilier": 0.5, "education": 0.6,
    }

    PAIN_SHAME_MULTIPLIERS = {
        "perte_argent": 1.5, "incompetence": 2.0, "non_conformite": 1.8,
        "inefficacite": 1.2, "retard": 1.0, "securite": 1.7,
    }

    def calculate_index(self, sector: str, pain_type: str) -> Dict:
        base = self.SECTOR_SHAME.get(sector, 0.5)
        mult = self.PAIN_SHAME_MULTIPLIERS.get(pain_type, 1.0)
        index = min(1.0, base * mult)
        return {
            "shame_index": round(index, 3),
            "discretion_required": index > 0.6,
            "premium_potential": "high" if index > 0.7 else "medium" if index > 0.4 else "low",
            "approach": "ultra_discret" if index > 0.7 else "discret" if index > 0.4 else "standard"
        }

    def get_stats(self) -> Dict:
        return {"sectors": len(self.SECTOR_SHAME), "pain_types": len(self.PAIN_SHAME_MULTIPLIERS)}
