"""PAIN: Off-Grid Living — PROJECT_04 TINY HOUSE"""
from typing import Dict

PAIN = {
    "name": "Autonomie Énergétique & Vie Hors-Réseau",
    "description": "Personnes souhaitant vie autonome — bloquées par coût, complexité technique, manque d'offres clé-en-main",
    "urgency": "MEDIUM",
    "price_range": (35000, 120000),
    "target_segments": ["Retraités anticipés", "Néo-ruraux", "Militants écologiques", "Familles résilience"],
    "our_solution": "Tiny House Off-Grid complète — solaire 3kWc + récup eau + compost + cuisine autonome",
    "market_size": 45000,  # unités/an Europe
    "satisfaction_current": 0.30,
    "margin_target": 0.38,
    "channels": ["Salons habitat alternatif", "YouTube eco-construction", "Communautés intentionnelles"],
}

OFF_GRID_PACKAGES = {
    "starter":  {
        "price": 38000, "solar_kwp": 2.0, "battery_kwh": 10,
        "water_recovery_l": 5000, "autonomy_days": 7,
        "surface_m2": 20, "desc": "Couple sans enfant, usage saisonnier"
    },
    "family":   {
        "price": 68000, "solar_kwp": 4.5, "battery_kwh": 20,
        "water_recovery_l": 15000, "autonomy_days": 14,
        "surface_m2": 35, "desc": "Famille 4 pers, résidence principale"
    },
    "premium":  {
        "price": 115000, "solar_kwp": 8.0, "battery_kwh": 40,
        "water_recovery_l": 30000, "autonomy_days": 30,
        "surface_m2": 50, "desc": "Autonomie totale 12 mois, confort premium"
    },
}

def get_package(profile: str = "family", customizations: list = None) -> Dict:
    pkg = OFF_GRID_PACKAGES.get(profile, OFF_GRID_PACKAGES["family"]).copy()
    if customizations:
        upgrades = {"well": 8000, "biogas": 5000, "greenhouse": 12000, "workshop": 9000}
        for c in customizations:
            pkg["price"] += upgrades.get(c, 0)
        pkg["customizations"] = customizations
    pkg["profile"] = profile
    pkg["permitting_support"] = True
    pkg["warranty_years"] = 10
    pkg["co2_saved_kg_per_year"] = pkg["solar_kwp"] * 800
    return pkg
