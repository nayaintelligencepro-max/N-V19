"""NAYA V19 - Specialization Manager - Gere les specialisations par secteur."""
import time, logging
from typing import Dict, List
log = logging.getLogger("NAYA.SPECIALIZATION")

class SpecializationManager:
    """Gere les specialisations que NAYA developpe au fil des succes."""

    def __init__(self):
        self._specializations: Dict[str, Dict] = {}
        self._experience_log: List[Dict] = []

    def record_experience(self, sector: str, offer_type: str,
                          success: bool, revenue: float = 0) -> None:
        if sector not in self._specializations:
            self._specializations[sector] = {
                "attempts": 0, "successes": 0, "revenue": 0,
                "offer_types": {}, "expertise_level": "novice"
            }
        spec = self._specializations[sector]
        spec["attempts"] += 1
        if success:
            spec["successes"] += 1
            spec["revenue"] += revenue
        spec["offer_types"][offer_type] = spec["offer_types"].get(offer_type, 0) + 1
        # Update expertise level
        if spec["successes"] >= 20:
            spec["expertise_level"] = "master"
        elif spec["successes"] >= 10:
            spec["expertise_level"] = "expert"
        elif spec["successes"] >= 5:
            spec["expertise_level"] = "competent"
        elif spec["successes"] >= 1:
            spec["expertise_level"] = "beginner"
        self._experience_log.append({
            "sector": sector, "offer_type": offer_type,
            "success": success, "revenue": revenue, "ts": time.time()
        })

    def get_top_specializations(self, n: int = 5) -> List[Dict]:
        ranked = sorted(
            [{"sector": s, **d} for s, d in self._specializations.items()],
            key=lambda x: x["revenue"], reverse=True
        )
        return ranked[:n]

    def get_expertise_level(self, sector: str) -> str:
        spec = self._specializations.get(sector)
        return spec["expertise_level"] if spec else "unknown"

    def get_best_offer_type(self, sector: str) -> str:
        spec = self._specializations.get(sector)
        if not spec or not spec["offer_types"]:
            return "service_premium_custom"
        return max(spec["offer_types"], key=spec["offer_types"].get)

    def get_stats(self) -> Dict:
        return {
            "sectors": len(self._specializations),
            "total_experience": len(self._experience_log),
            "top_sectors": self.get_top_specializations(3)
        }
