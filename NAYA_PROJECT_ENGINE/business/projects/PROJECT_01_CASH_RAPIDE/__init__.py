"""
PROJECT_01 — CASH RAPIDE
Services express premium : 24H / 48H / 72H
Plancher : 1 000€ | Ceiling : 150 000€+
"""
from dataclasses import dataclass, field
from typing import Dict, List
from enum import Enum

class CashPalier(Enum):
    P1_PREMIUM = "P1_PREMIUM"          # 1k-5k€, 24H
    P2_PREMIUM_PLUS = "P2_PREMIUM_PLUS" # 5k-25k€, 48H
    P3_EXECUTIVE = "P3_EXECUTIVE"       # 25k-75k€, 72H
    P4_ENTERPRISE = "P4_ENTERPRISE"     # 75k-200k€, 1 semaine
    P5_STRATEGIC = "P5_STRATEGIC"       # 200k-500k€, 2 semaines
    P6_HIGH_STAKES = "P6_HIGH_STAKES"   # 500k+€, 1 mois

@dataclass
class CashRapideProject:
    id: str = "PROJECT_01_CASH_RAPIDE"
    name: str = "Cash Rapide — Services Express Premium"
    description: str = "Génération de cash en 24-72H via services premium à haute valeur"
    active: bool = True
    paliers: List[str] = field(default_factory=lambda: [p.value for p in CashPalier])
    
    # Objectifs
    target_24h_min: float = 1000
    target_48h_min: float = 5000
    target_72h_min: float = 10000
    target_monthly_min: float = 50000

    # Services disponibles
    service_catalog = {
        "audit_express": {"price_range": (1500, 5000), "delivery": "24H", "palier": "P1"},
        "diagnostic_complet": {"price_range": (3000, 12000), "delivery": "48H", "palier": "P2"},
        "consulting_strategique": {"price_range": (8000, 30000), "delivery": "48H", "palier": "P3"},
        "implementation_express": {"price_range": (15000, 75000), "delivery": "72H", "palier": "P3"},
        "transformation_urgente": {"price_range": (50000, 200000), "delivery": "1 semaine", "palier": "P4"},
        "architecture_strategique": {"price_range": (100000, 500000), "delivery": "2 semaines", "palier": "P5"},
    }

    def get_service_for_palier(self, palier: str) -> List[Dict]:
        return [{"service": k, **v} for k, v in self.service_catalog.items()
                if v.get("palier", "")[1] == palier[-1]]

PROJECT_STATE = CashRapideProject()
