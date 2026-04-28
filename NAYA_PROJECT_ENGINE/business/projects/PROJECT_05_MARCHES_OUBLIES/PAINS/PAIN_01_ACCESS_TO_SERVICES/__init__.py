"""PAIN: Accès aux services — PROJECT_05 MARCHÉS OUBLIÉS"""
PAIN = {
    "name": "Accès services premium pour marchés sous-servis",
    "description": "Séniors actifs, immigrants entrepreneurs, zones périurbaines: absence d'offres adaptées",
    "market_size": 12000000,
    "segments": {
        "seniors_digitaux": {"size": 4500000, "avg_spend": 120, "pain_score": 0.75},
        "immigrants_entrepreneurs": {"size": 3200000, "avg_spend": 200, "pain_score": 0.85},
        "zones_periurbaines": {"size": 5000000, "avg_spend": 90, "pain_score": 0.70},
    },
    "our_solution": "Hub services adapté: accompagnement multilingue, horaires flexibles, proximité",
    "revenue_model": "Abonnement mensuel 49-149€ + services à la demande",
    "channels": ["Facebook groupes immigrants", "Mairies", "Associations culturelles"],
    "acquisition_cost": 35,
    "ltv": 1200,
}

def get_subscription(segment: str = "standard") -> dict:
    tiers = {
        "essentiel":  {"price": 49,  "services": 5, "support_hours": 4},
        "standard":   {"price": 89,  "services": 10, "support_hours": 8},
        "premium":    {"price": 149, "services": "Illimité", "support_hours": 20},
    }
    return {**tiers.get(segment, tiers["standard"]), "tier": segment,
            "languages": 6, "cancel_anytime": True}
