"""
NAYA_CORE v5.0 — Discreet Business Engine
==========================================
Identification et exécution de deals discrets 100K-500K/jour.
Niveaux 1-3. Network elite.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timezone
import logging

log = logging.getLogger("NAYA.DISCREET")

class DiscreetLevel(Enum):
    LEVEL_1 = 1  # 100K-200K/jour — expertise sectorielle
    LEVEL_2 = 2  # 200K-350K/jour — recherche experte + réseau
    LEVEL_3 = 3  # 350K-500K/jour — accès elite uniquement

LEVEL_CONFIG = {
    DiscreetLevel.LEVEL_1: {"min": 100000, "max": 200000, "cred_required": 70, "discovery_hours": 48},
    DiscreetLevel.LEVEL_2: {"min": 200000, "max": 350000, "cred_required": 75, "discovery_hours": 72},
    DiscreetLevel.LEVEL_3: {"min": 350000, "max": 500000, "cred_required": 85, "discovery_hours": 96},
}

@dataclass
class DiscreetDeal:
    deal_id: str
    company_name: str
    estimated_daily: float
    level: DiscreetLevel
    deal_type: str  # equity, revenue_share, acquisition, jv
    status: str = "PIPELINE"
    structure: Optional[Dict] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class DiscreetBusinessEngine:
    def __init__(self, credibility_score: float = 75.0):
        self.credibility_score = credibility_score
        self.pipeline: List[DiscreetDeal] = []
        self.active_deals: List[DiscreetDeal] = []

    def classify(self, estimated_daily: float) -> Dict[str, Any]:
        for level, cfg in LEVEL_CONFIG.items():
            if cfg["min"] <= estimated_daily <= cfg["max"]:
                eligible = self.credibility_score >= cfg["cred_required"]
                return {
                    "level": level.value,
                    "daily_range": f"{cfg['min']:,} - {cfg['max']:,}",
                    "monthly_projection": estimated_daily * 22,
                    "discovery_hours": cfg["discovery_hours"],
                    "eligible": eligible,
                    "credibility_required": cfg["cred_required"],
                    "current_credibility": self.credibility_score,
                }
        return {"eligible": False, "reason": "Hors plage discrète (100K-500K/j)"}

    def add_to_pipeline(self, company_name: str, estimated_daily: float,
                        deal_type: str = "revenue_share") -> Optional[DiscreetDeal]:
        classification = self.classify(estimated_daily)
        if not classification.get("eligible"):
            return None
        import hashlib
        deal_id = f"DISC-{hashlib.md5(f'{company_name}{estimated_daily}'.encode()).hexdigest()[:8]}"
        level_enum = DiscreetLevel(classification["level"])
        deal = DiscreetDeal(deal_id=deal_id, company_name=company_name,
                            estimated_daily=estimated_daily, level=level_enum, deal_type=deal_type)
        self.pipeline.append(deal)
        return deal

    def get_portfolio_summary(self) -> Dict[str, Any]:
        total_daily = sum(d.estimated_daily for d in self.active_deals)
        return {"active_deals": len(self.active_deals), "pipeline_deals": len(self.pipeline),
                "total_daily_revenue": total_daily, "total_monthly_revenue": total_daily * 22,
                "credibility_score": self.credibility_score}


_ENGINE: Optional[DiscreetBusinessEngine] = None

def get_discreet_engine(credibility_score: float = 75.0) -> DiscreetBusinessEngine:
    global _ENGINE
    if _ENGINE is None: _ENGINE = DiscreetBusinessEngine(credibility_score)
    return _ENGINE
