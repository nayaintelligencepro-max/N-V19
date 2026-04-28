"""
PROJECT_05 — MARCHÉS OUBLIÉS
Marchés sous-exploités avec forte demande non adressée
"""
from dataclasses import dataclass, field

@dataclass  
class MarchesOubliesProject:
    id: str = "PROJECT_05_MARCHES_OUBLIES"
    name: str = "Marchés Oubliés — Blue Ocean Business"
    description: str = "Marchés à forte demande avec offre structurée quasi-inexistante"
    active: bool = True
    
    target_markets = [
        "Séniors actifs digitaux", "Immigrants entrepreneurs",
        "Zones périurbaines sous-servies", "Artisans non digitalisés"
    ]
    
    monthly_revenue_target: float = 80000

PROJECT_STATE = MarchesOubliesProject()
