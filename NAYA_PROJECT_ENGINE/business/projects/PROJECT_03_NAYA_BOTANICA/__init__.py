"""
PROJECT_03 — NAYA BOTANICA
Cosmétiques premium naturels — marchés sous-exploités
"""
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class NayaBotanicaProject:
    id: str = "PROJECT_03_NAYA_BOTANICA"
    name: str = "Naya Botanica — Cosmétiques Naturels Premium"
    description: str = "Marque cosmétique ciblant douleurs peau mal adressées"
    active: bool = True
    
    target_markets = ["Hyperpigmentation", "Réparation peau", "Fermeté corps"]
    price_range = (25, 250)  # € par produit
    distribution = ["Direct-to-consumer", "Instagram", "Pharmacies premium", "Spas"]
    
    product_lines = {
        "skin_repair": {"price": 65, "margin": 0.72, "reorder_rate": 0.65},
        "hyperpigmentation": {"price": 85, "margin": 0.75, "reorder_rate": 0.70},
        "firming_body": {"price": 55, "margin": 0.68, "reorder_rate": 0.60},
    }
    
    monthly_revenue_target: float = 30000
    customer_ltv_target: float = 500  # € sur 12 mois

PROJECT_STATE = NayaBotanicaProject()
