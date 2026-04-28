"""
NAYA — Business Model Builder
Construit des modèles business complets et rentables automatiquement.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime, timezone

class ModelType(Enum):
    CASH_RAPIDE = "cash_rapide"
    SAAS = "saas"
    AGENCY = "agency"
    CONSULTING = "consulting"
    ECOMMERCE = "ecommerce"
    MARKETPLACE = "marketplace"
    PHYSICAL_PRODUCT = "physical_product"
    FRANCHISE = "franchise"

@dataclass
class BusinessModel:
    id: str; name: str; type: ModelType
    target_market: str; core_pain: str
    revenue_model: str; pricing: Dict
    avg_deal: float; deals_per_month: int
    mrr_potential: float; margin_pct: float
    startup_cost: float; time_to_revenue_days: int
    acquisition_channels: List[str] = field(default_factory=list)
    delivery_steps: List[str] = field(default_factory=list)
    automation_potential: float = 0.0
    scale_multiplier: float = 1.0

    @property
    def arr_potential(self): return self.mrr_potential * 12
    @property 
    def roi_score(self): 
        return (self.mrr_potential * self.margin_pct/100) / max(self.startup_cost,1) * 100

class BusinessModelEngine:
    """Construit et optimise des modèles business complets."""
    
    TEMPLATES = {
        ModelType.CASH_RAPIDE: {"margin": 0.85, "speed": 3, "scale": 1.5},
        ModelType.SAAS: {"margin": 0.80, "speed": 30, "scale": 10.0},
        ModelType.AGENCY: {"margin": 0.65, "speed": 14, "scale": 3.0},
        ModelType.CONSULTING: {"margin": 0.90, "speed": 7, "scale": 2.0},
        ModelType.ECOMMERCE: {"margin": 0.35, "speed": 21, "scale": 5.0},
    }

    def build(self, context: Dict) -> BusinessModel:
        mtype = ModelType(context.get("type", "consulting"))
        tmpl = self.TEMPLATES.get(mtype, self.TEMPLATES[ModelType.CONSULTING])
        base_revenue = context.get("target_monthly", 10000)
        return BusinessModel(
            id=f"BM_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            name=context.get("name", f"Business {mtype.value}"),
            type=mtype,
            target_market=context.get("target_market", "PME B2B"),
            core_pain=context.get("core_pain", "Inefficacité opérationnelle"),
            revenue_model=context.get("revenue_model", "Service + Retainer"),
            pricing=context.get("pricing", {"starter": 2000, "pro": 5000, "enterprise": 15000}),
            avg_deal=context.get("avg_deal", base_revenue / 4),
            deals_per_month=context.get("deals_pm", 4),
            mrr_potential=base_revenue,
            margin_pct=tmpl["margin"] * 100,
            startup_cost=context.get("startup_cost", 500),
            time_to_revenue_days=int(tmpl["speed"]),
            acquisition_channels=context.get("channels", ["LinkedIn", "Email", "Réseau"]),
            delivery_steps=context.get("delivery", ["Diagnostic", "Plan", "Livraison", "Suivi"]),
            automation_potential=context.get("automation", 0.6),
            scale_multiplier=tmpl["scale"],
        )

    def optimize_pricing(self, model: BusinessModel, pain_score: float) -> Dict:
        """Optimise le pricing basé sur l'intensité de la douleur."""
        multiplier = 1 + pain_score * 0.5
        return {tier: int(price * multiplier) 
                for tier, price in model.pricing.items()}

    def project_growth(self, model: BusinessModel, months: int = 12) -> List[Dict]:
        results = []
        mrr = 0
        for m in range(1, months + 1):
            new_clients = model.deals_per_month * (1 + m * 0.05)
            mrr += new_clients * model.avg_deal * (model.margin_pct/100)
            mrr = min(mrr, model.mrr_potential * model.scale_multiplier)
            results.append({"month": m, "mrr": round(mrr), "clients": int(new_clients * m)})
        return results
