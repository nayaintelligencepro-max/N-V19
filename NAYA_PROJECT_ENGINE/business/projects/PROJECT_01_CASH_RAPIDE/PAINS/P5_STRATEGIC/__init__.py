"""P5 STRATEGIC — 200k-500k€ — Livraison 2 semaines"""
from typing import Dict, List

P5_SERVICES = [
    {"id": "P5_01", "name": "Programme transformation stratégique groupe",
     "price": 350000, "timeline": "2 semaines stratégie + 3 mois exécution",
     "deliverable": "Nouveau modèle business + feuille de route 3 ans + équipe coachée",
     "sectors": ["Groupes industriels", "ETI", "Divisions corporate"]},
    {"id": "P5_02", "name": "Architecture SaaS enterprise + migration cloud",
     "price": 280000, "timeline": "2 semaines architecture + 6 semaines implémentation",
     "deliverable": "Architecture cloud + migration + DevOps + équipe formée",
     "sectors": ["Éditeurs logiciels", "Fintech", "Healthtech"]},
    {"id": "P5_03", "name": "Stratégie M&A + due diligence accélérée",
     "price": 450000, "timeline": "2 semaines",
     "deliverable": "Rapport DD complet + valorisation + plan intégration",
     "sectors": ["Holdings", "Fonds PE", "Directions financières"]},
]

def get_p5_offer(scope: str = "full") -> Dict:
    pricing = {"light": 220000, "standard": 350000, "full": 450000, "custom": 500000}
    return {"price": pricing.get(scope, 350000), "scope": scope,
            "timeline": "2 semaines conception + plan exécution 90 jours",
            "team": "Partner senior + 2 consultants experts",
            "guarantee": "Jalons contractuels avec pénalités"}

STRATEGIC_PACKAGES = {
    "M&A_ACCELERATED": {"price": 450000, "duration_days": 14, "output": "Due diligence + valuation"},
    "TRANSFORMATION_90": {"price": 350000, "duration_days": 90, "output": "Transformation complète"},
    "CLOUD_ENTERPRISE": {"price": 280000, "duration_days": 60, "output": "Migration + DevOps"},
}
