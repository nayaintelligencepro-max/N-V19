"""
NAYA — Supplier Intelligence Engine
Évalue et optimise les fournisseurs pour maximaliser la marge.
"""
from dataclasses import dataclass
from typing import Dict, List
from enum import Enum

class SupplierTier(Enum):
    ELITE = "elite"       # Score 85+
    PREFERRED = "preferred"  # 70-85
    STANDARD = "standard"    # 50-70
    RISKY = "risky"          # <50

@dataclass
class Supplier:
    id: str; name: str; category: str
    quality_score: float; cost_index: float  # 0-100 (100=très cher)
    reliability_score: float; speed_score: float
    margin_impact: float  # % marge qu'il génère

    @property
    def overall_score(self):
        return (self.quality_score * 0.35 + (100-self.cost_index) * 0.30 +
                self.reliability_score * 0.25 + self.speed_score * 0.10)

    @property
    def tier(self):
        s = self.overall_score
        if s >= 85: return SupplierTier.ELITE
        if s >= 70: return SupplierTier.PREFERRED
        if s >= 50: return SupplierTier.STANDARD
        return SupplierTier.RISKY

class SupplierIntelligenceEngine:
    """Évalue et sélectionne les meilleurs fournisseurs."""

    def evaluate_supplier(self, quality_score: float, cost: float, 
                          reliability_score: float, speed: float = 70) -> float:
        return round((quality_score*0.35 + (100-cost)*0.30 + 
                      reliability_score*0.25 + speed*0.10), 2)

    def rank_suppliers(self, suppliers: List[Supplier]) -> List[Supplier]:
        return sorted(suppliers, key=lambda s: s.overall_score, reverse=True)

    def find_best_for_margin(self, suppliers: List[Supplier], 
                              min_quality: float = 70) -> List[Supplier]:
        eligible = [s for s in suppliers if s.quality_score >= min_quality]
        return sorted(eligible, key=lambda s: s.margin_impact, reverse=True)

    def negotiate_bundle(self, suppliers: List[Supplier], 
                          volume_commitment: float) -> Dict:
        savings = sum(s.cost_index * 0.05 * volume_commitment/10000 
                     for s in suppliers if s.tier in (SupplierTier.PREFERRED, SupplierTier.ELITE))
        return {"estimated_savings": round(savings), "suppliers": len(suppliers),
                "recommended_bundle": [s.name for s in suppliers[:3]]}
