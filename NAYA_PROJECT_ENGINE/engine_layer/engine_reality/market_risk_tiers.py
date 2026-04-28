"""NAYA V19 - Market Risk Tiers - Classification des marches par niveau de risque."""
import logging
from typing import Dict, List
log = logging.getLogger("NAYA.REALITY.RISK")

class MarketRiskTiers:
    """Classe les marches en tiers de risque pour guider les decisions."""

    RISK_PROFILES = {
        "low": {"sectors": ["restauration", "commerce", "artisan"], "max_investment": 5000, "expected_roi_months": 3},
        "medium": {"sectors": ["tech", "sante", "education", "pme"], "max_investment": 20000, "expected_roi_months": 6},
        "high": {"sectors": ["finance", "immobilier", "energie"], "max_investment": 100000, "expected_roi_months": 12},
        "very_high": {"sectors": ["gouvernement", "defense", "infrastructure"], "max_investment": 500000, "expected_roi_months": 18},
    }

    def classify(self, sector: str, deal_size: float) -> Dict:
        for tier, profile in self.RISK_PROFILES.items():
            if sector in profile["sectors"]:
                within_limit = deal_size <= profile["max_investment"]
                return {
                    "sector": sector, "risk_tier": tier,
                    "max_investment": profile["max_investment"],
                    "within_limit": within_limit,
                    "expected_roi_months": profile["expected_roi_months"],
                    "recommendation": "proceed" if within_limit else "review_with_caution"
                }
        return {"sector": sector, "risk_tier": "unknown", "recommendation": "research_required"}

    def get_low_risk_sectors(self) -> List[str]:
        return self.RISK_PROFILES["low"]["sectors"]

    def get_all_tiers(self) -> Dict:
        return self.RISK_PROFILES

    def get_stats(self) -> Dict:
        return {"tiers": len(self.RISK_PROFILES), "sectors_covered": sum(len(p["sectors"]) for p in self.RISK_PROFILES.values())}
