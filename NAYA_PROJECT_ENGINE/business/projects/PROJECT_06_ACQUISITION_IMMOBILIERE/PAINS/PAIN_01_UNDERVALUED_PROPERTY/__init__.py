"""PAIN: Biens Sous-Évalués — PROJECT_06 ACQUISITION IMMOBILIÈRE"""
from typing import Dict

PAIN = {
    "name": "Acquisition Biens Immobiliers Sous-Évalués",
    "description": "Investisseurs et acheteurs incapables d'identifier et sécuriser des biens à forte décote avant les autres",
    "urgency": "HIGH",
    "price_range": (2000, 15000),  # honoraires conseil
    "target_segments": ["Investisseurs immobilier", "Marchands de biens", "Family offices", "SCI patrimoniales"],
    "our_solution": "Intelligence Immobilière NAYA — sourcing off-market + scoring décote + négociation stratégique",
    "market_size": 12000000000,  # EUR transactions annuelles FR
    "satisfaction_current": 0.30,
    "margin_target": 0.70,
    "channels": ["Notaires partenaires", "LinkedIn Investisseurs", "Clubs investissement", "Mandataires indépendants"],
    "avg_deal_size": 280000,
    "avg_discount_pct": 18,
}

SOURCING_SERVICES = {
    "market_scan": {
        "price": 2000, "scope": "Analyse zone géo ciblée — 50 biens scorés",
        "timeline_days": 7, "deliverable": "Rapport + top 10 opportunités"
    },
    "sourcing_mandate": {
        "price_pct_deal": 2.0, "min_fee": 5000, "max_fee": 15000,
        "scope": "Sourcing off-market + négociation + suivi compromis",
        "success_only": True
    },
    "portfolio_scan": {
        "price": 8000, "scope": "Analyse portefeuille existant — optimisation et cessions",
        "timeline_days": 14, "deliverable": "Stratégie portefeuille + 3 scénarios"
    },
    "data_access_monthly": {
        "price": 490, "scope": "Accès flux off-market + alertes décote > 15%",
        "update": "Quotidien", "zones_included": 3
    },
}

def get_investment_analysis(property_value: float = 300000, zone: str = "IDF") -> Dict:
    zone_multipliers = {"IDF": 1.2, "Lyon": 1.0, "Bordeaux": 1.0, "Marseille": 0.9, "Province": 0.8}
    mult = zone_multipliers.get(zone, 1.0)
    expected_discount = 0.18 * mult
    potential_gain = property_value * expected_discount
    service_fee = max(5000, min(15000, property_value * 0.02))
    roi = (potential_gain - service_fee) / service_fee
    return {
        "property_value": property_value, "zone": zone,
        "expected_discount_pct": round(expected_discount * 100, 1),
        "expected_gain": round(potential_gain),
        "service_fee": round(service_fee),
        "net_roi_x": round(roi, 1),
        "timeline_weeks": 4,
        "success_rate_pct": 72,
    }
