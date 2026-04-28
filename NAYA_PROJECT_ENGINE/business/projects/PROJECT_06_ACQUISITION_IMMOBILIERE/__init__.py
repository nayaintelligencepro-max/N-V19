"""
PROJECT_06 — ACQUISITION IMMOBILIÈRE
Stratégies d'acquisition sous-valorisée et création de valeur
"""
from dataclasses import dataclass

@dataclass
class AcquisitionImmobiliereProject:
    id: str = "PROJECT_06_ACQUISITION_IMMOBILIERE"
    name: str = "Acquisition Immobilière Stratégique"
    description: str = "Identifier et acquérir des biens sous-valorisés pour création de valeur"
    active: bool = True
    
    strategies = {
        "distressed_assets": {"discount_avg": 0.25, "work_required": "Moyenne"},
        "motivated_seller": {"discount_avg": 0.20, "time_to_close": "3-6 semaines"},
        "succession_purchase": {"discount_avg": 0.15, "complexity": "Haute"},
    }
    
    services = {
        "chasseur_immobilier": {"fee_pct": 0.03, "min_fee": 3000},
        "audit_valorisation": {"price": 5000, "delivery": "72H"},
        "negociation_mandate": {"fee_pct": 0.05, "success_only": True},
    }

PROJECT_STATE = AcquisitionImmobiliereProject()
