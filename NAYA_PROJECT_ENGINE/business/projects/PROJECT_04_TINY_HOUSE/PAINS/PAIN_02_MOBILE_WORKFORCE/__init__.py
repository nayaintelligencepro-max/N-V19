"""PAIN: Workforce Mobile — PROJECT_04 TINY HOUSE"""
from typing import Dict

PAIN = {
    "name": "Logement Mobile Workforce & Nomades Digitaux",
    "description": "Travailleurs nomades, remote workers, contractors en mission — coût logement exorbitant, instabilité, perte productivité",
    "urgency": "HIGH",
    "price_range": (800, 2500),  # Location mensuelle
    "target_segments": ["Remote workers", "Contractors BTP/Industrie", "Saisonniers qualifiés", "Digital nomads"],
    "our_solution": "Fleet Tiny Houses mobiles — location mensuelle tout inclus avec WiFi fibre + bureau intégré",
    "market_size": 180000,  # locataires potentiels
    "satisfaction_current": 0.22,
    "margin_target": 0.55,
    "channels": ["LinkedIn Remote Work communities", "Entreprises partenaires (mise à dispo équipes)", "AirBnB pro"],
}

RENTAL_TIERS = {
    "solo_basic":   {"monthly": 890,  "surface_m2": 18, "wifi_mbps": 100, "office_setup": False},
    "solo_pro":     {"monthly": 1290, "surface_m2": 24, "wifi_mbps": 500, "office_setup": True,
                     "includes": ["Bureau ergonomique", "Écran 27\"", "Imprimante"]},
    "couple":       {"monthly": 1590, "surface_m2": 32, "wifi_mbps": 500, "office_setup": True,
                     "includes": ["2 bureaux", "Espace commun", "Cuisine équipée"]},
    "corporate":    {"monthly": 2400, "surface_m2": 40, "wifi_mbps": 1000, "office_setup": True,
                     "includes": ["Salle réunion", "2 bureaux doubles", "ménage hebdo", "Voiture vélo"]},
}

def get_rental_quote(profile: str = "solo_pro", months: int = 3) -> Dict:
    tier = RENTAL_TIERS.get(profile, RENTAL_TIERS["solo_pro"]).copy()
    discount = 0.10 if months >= 6 else (0.05 if months >= 3 else 0)
    total = tier["monthly"] * months * (1 - discount)
    return {**tier, "profile": profile, "months": months,
            "discount_pct": int(discount * 100),
            "total": round(total),
            "deposit": tier["monthly"] * 1.5,
            "utilities_included": True,
            "delivery_radius_km": 500,
            "setup_days": 2}
