"""
PROJECT_02 — GOOGLE XR SOLUTIONS
Solutions XR enterprise — Google ecosystem
"""
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class GoogleXRProject:
    id: str = "PROJECT_02_GOOGLE_XR"
    name: str = "Google XR Solutions — Enterprise AR/VR/MR"
    description: str = "Solutions XR enterprise via écosystème Google (ARCore, Glass Enterprise)"
    active: bool = True

    xr_services: Dict = field(default_factory=lambda: {
        "enterprise_ar_deployment": {"price": 85000, "timeline": "4 semaines", "margin": 0.45},
        "xr_training_program":      {"price": 35000, "timeline": "2 semaines", "margin": 0.55},
        "industrial_simulation":    {"price": 120000, "timeline": "6 semaines", "margin": 0.40},
        "data_visualization_xr":    {"price": 55000, "timeline": "3 semaines", "margin": 0.50},
        "custom_xr_platform":       {"price": 200000, "timeline": "3 mois",    "margin": 0.38},
    })

    target_sectors: List = field(default_factory=lambda: [
        "Industrie", "Médecine", "Formation professionnelle",
        "Architecture", "Retail premium", "Défense"
    ])

    google_partnership_level: str = "Reseller Partner"
    monthly_revenue_target: float = 250000
    pipeline_value: float = 0.0

PROJECT_STATE = GoogleXRProject()
