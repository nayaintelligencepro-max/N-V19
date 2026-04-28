"""PAIN: Logement d'Urgence & Post-Catastrophe — PROJECT_04 TINY HOUSE"""
from typing import Dict, List

PAIN = {
    "name": "Hébergement d'Urgence & Résilience Post-Catastrophe",
    "description": "Collectivités, ONG, assureurs sans solutions de logement rapide, digne et durable post-sinistre",
    "urgency": "CRITICAL",
    "price_range": (15000, 45000),  # par unité, vente B2G/B2NGO
    "target_segments": ["Mairies", "Préfectures", "Assureurs sinistres", "Croix-Rouge", "ONG humanitaires"],
    "our_solution": "Module RAPID — Tiny House déployable 4H, sanitaire autonome, résiste vents 180km/h",
    "market_size_eu": 8000,  # unités/an marchés B2G
    "satisfaction_current": 0.20,
    "margin_target": 0.42,
    "channels": ["Appels d'offres publics", "ECHO EU", "Partenaires assureurs", "Sapeurs-pompiers fédérations"],
}

RAPID_MODULES = {
    "single_unit": {
        "price": 18500, "occupants": 4, "deploy_hours": 4,
        "autonomy_days": 21, "lifespan_years": 25,
        "certifications": ["NF HQE", "CE", "REACH"]
    },
    "family_plus": {
        "price": 27000, "occupants": 6, "deploy_hours": 6,
        "autonomy_days": 30, "lifespan_years": 25,
        "includes": ["Chambre parents", "Chambre enfants", "Cuisine", "Salle d'eau"]
    },
    "community_hub": {
        "price": 42000, "occupants": 20, "deploy_hours": 8,
        "autonomy_days": 45, "lifespan_years": 25,
        "includes": ["Dortoirs", "Cuisine collective", "Médical", "Wifi satcom"]
    },
}

def get_emergency_fleet(units: int = 10, unit_type: str = "single_unit") -> Dict:
    module = RAPID_MODULES.get(unit_type, RAPID_MODULES["single_unit"])
    unit_price = module["price"]
    volume_discount = 0.20 if units >= 50 else (0.12 if units >= 20 else (0.05 if units >= 10 else 0))
    total = units * unit_price * (1 - volume_discount)
    return {
        "units": units, "unit_type": unit_type,
        "unit_price": unit_price,
        "volume_discount_pct": int(volume_discount * 100),
        "total_price": round(total),
        "total_capacity": units * module["occupants"],
        "deployment_hours": module["deploy_hours"],
        "financing": "Leasing 5 ans disponible — éligible subventions FEDER",
        "maintenance_annual": round(total * 0.04),
        "warranty_years": 5,
    }
