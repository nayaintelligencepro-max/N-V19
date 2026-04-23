"""PAIN: Estimation Complexe — PROJECT_06 ACQUISITION IMMOBILIÈRE"""
from typing import Dict, List

PAIN = {
    "name": "Estimation & Valorisation Immobilière Complexe",
    "description": "Investisseurs, notaires, promoteurs face à biens atypiques ou situations complexes où les outils standards échouent",
    "urgency": "MEDIUM",
    "price_range": (1500, 12000),
    "target_segments": [
        "Biens atypiques (châteaux, lofts, usines reconverties)",
        "Estimations judiciaires (divorce, succession contestée)",
        "Due diligence investissement",
        "Refinancement portfolios"
    ],
    "our_solution": "Estimation NAYA Expert — IA + expert terrain + rapport certifié en 72H",
    "market_size": 450000,  # estimations complexes/an FR
    "satisfaction_current": 0.28,
    "margin_target": 0.72,
    "channels": ["Avocats", "Notaires", "Tribunaux (expertise judiciaire)", "Fonds immo"],
}

ESTIMATION_TYPES = {
    "atypical_property": {
        "price": 3500, "timeline_hours": 72,
        "method": "Comparatif + revenu + DCF", "report_pages": 25,
        "admissible_court": True
    },
    "judicial_expertise": {
        "price": 8000, "timeline_hours": 120,
        "method": "Expertise contradictoire complète", "report_pages": 45,
        "admissible_court": True, "expert_testimony": True
    },
    "portfolio_valuation": {
        "price_per_unit": 800, "min_units": 5, "timeline_days": 14,
        "method": "Masse — comparatif standardisé + scoring",
        "discount_above_20_units": 0.25
    },
    "quick_expert_opinion": {
        "price": 1500, "timeline_hours": 24,
        "method": "Avis expert rapide", "report_pages": 8,
        "admissible_court": False, "use_case": "Négociation rapide"
    },
}

def get_estimation_quote(estimation_type: str = "atypical_property", units: int = 1) -> Dict:
    est = ESTIMATION_TYPES.get(estimation_type, ESTIMATION_TYPES["atypical_property"]).copy()
    if estimation_type == "portfolio_valuation":
        discount = est.get("discount_above_20_units", 0) if units >= 20 else 0
        est["price"] = round(est["price_per_unit"] * units * (1 - discount))
        est["units"] = units
    est["estimation_type"] = estimation_type
    est["certification"] = "Rapport signé expert certifié REV/MRICS"
    est["methodology_transparency"] = True
    est["revision_included"] = True
    return est
