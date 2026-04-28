"""
PROJECT_04 — TINY HOUSE
Habitat alternatif premium — off-grid, mobilité, résilience
"""
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class TinyHouseProject:
    id: str = "PROJECT_04_TINY_HOUSE"
    name: str = "Tiny House Premium — Habitat Alternatif"
    description: str = "Solutions habitat alternatif pour vivants nomades et off-grid"
    active: bool = True
    
    models = {
        "off_grid_autonome": {"price": 75000, "delivery_weeks": 16, "margin": 0.30},
        "mobile_pro": {"price": 55000, "delivery_weeks": 12, "margin": 0.28},
        "disaster_resilient": {"price": 45000, "delivery_weeks": 8, "margin": 0.25},
    }
    
    services = {
        "consulting_terrain": {"price": 3000, "duration": "2 jours"},
        "accompagnement_permis": {"price": 5000, "duration": "3 semaines"},
        "formation_autonomie": {"price": 2000, "duration": "1 semaine"},
    }
    
    monthly_revenue_target: float = 150000

PROJECT_STATE = TinyHouseProject()
