"""PAIN: Besoin Liquidité Vendeur — PROJECT_06 ACQUISITION IMMOBILIÈRE"""
from typing import Dict

PAIN = {
    "name": "Vendeurs en Besoin Urgent de Liquidité",
    "description": "Propriétaires contraints de vendre rapidement (succession, divorce, dette, déménagement) — acceptent décote pour vitesse",
    "urgency": "CRITICAL",
    "price_range": (0, 0),  # Modèle achat-revente, marge sur spread
    "target_segments": [
        "Successions bloquées",
        "Divorces contentieux",
        "Propriétaires en difficulté financière",
        "Expatriés devant vendre à distance"
    ],
    "our_solution": "Offre Cash Express NAYA — offre ferme sous 48H, paiement 30 jours, discrétion totale",
    "market_size_fr": 85000,  # transactions/an avec décote urgence
    "avg_discount_acquired": 0.22,
    "avg_hold_months": 8,
    "avg_resale_uplift": 0.35,
    "margin_target": 0.13,  # sur valeur marché
    "channels": ["Avocats succession/divorce", "Huissiers", "Banques crédit immo", "Notaires urgence"],
}

def analyze_opportunity(market_value: float, urgency_level: str = "high", condition: str = "good") -> Dict:
    urgency_discounts = {"critical": 0.28, "high": 0.22, "medium": 0.15}
    condition_adjustments = {"excellent": -0.03, "good": 0, "average": 0.05, "poor": 0.12}
    base_discount = urgency_discounts.get(urgency_level, 0.22)
    condition_adj = condition_adjustments.get(condition, 0)
    total_discount = base_discount + condition_adj
    acquisition_price = market_value * (1 - total_discount)
    renovation_budget = market_value * (0.08 if condition == "poor" else 0.03)
    resale_target = market_value * 1.05
    gross_margin = resale_target - acquisition_price - renovation_budget
    gross_margin_pct = gross_margin / market_value
    return {
        "market_value": market_value,
        "acquisition_price": round(acquisition_price),
        "discount_pct": round(total_discount * 100, 1),
        "renovation_budget": round(renovation_budget),
        "resale_target": round(resale_target),
        "gross_margin": round(gross_margin),
        "gross_margin_pct": round(gross_margin_pct * 100, 1),
        "hold_months_estimated": 8,
        "offer_validity_hours": 48,
        "closing_days": 30,
        "go": gross_margin_pct >= 0.10,
    }
