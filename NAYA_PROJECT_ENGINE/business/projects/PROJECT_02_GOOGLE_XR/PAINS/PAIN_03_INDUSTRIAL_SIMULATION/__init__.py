"""PAIN: Simulation Industrielle XR — PROJECT_02 GOOGLE XR"""
PAIN = {
    "name": "Simulation Industrielle & Jumeaux Numériques XR",
    "description": "Ingénieurs et techniciens sans outils de simulation 3D temps réel pour validation avant production",
    "urgency": "MEDIUM",
    "price_range": (60000, 200000),
    "timeline": "4-8 semaines",
    "target_sectors": ["Aéronautique", "Automobile", "Énergie", "Chimie", "BTP"],
    "our_solution": "Jumeau numérique ARCore + Unity Industrial + intégration CAD/PLM",
    "market_size": 8500000,
    "satisfaction_current": 0.20,
    "acquisition_channels": ["Salons industriels", "Éditeurs CAD (Dassault, Siemens)", "CCI industrielles"],
    "kpis": ["Réduction erreurs production", "Temps cycle validation", "ROI capex évité"],
}

SIMULATION_TIERS = {
    "starter":    {"price": 60000,  "assets": 20,  "users": 5,  "support_months": 3},
    "industrial": {"price": 120000, "assets": 100, "users": 20, "support_months": 6},
    "enterprise": {"price": 200000, "assets": -1,  "users": -1, "support_months": 12},
}

def get_offer(tier: str = "industrial") -> dict:
    config = SIMULATION_TIERS.get(tier, SIMULATION_TIERS["industrial"])
    return {**config, "tier": tier, "integrations": ["CATIA", "SolidWorks", "SAP PM"],
            "deployment": "Cloud + On-Premise hybride", "guarantee": "Précision simulation ±2% vs réel"}
