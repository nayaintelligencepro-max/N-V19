"""PAIN: Potentiel Urbain Sous-Estimé — PROJECT_05 MARCHÉS OUBLIÉS"""
from typing import Dict

PAIN = {
    "name": "Potentiel Économique Urbain Sous-Estimé",
    "description": "Quartiers populaires en Europe — pouvoir d'achat agrégé immense ignoré par acteurs mainstream, créant des déserts commerciaux",
    "urgency": "MEDIUM",
    "price_range": (500, 50000),  # Conseil + implantation B2B
    "target_segments": [
        "Collectivités cherchant revitalisation",
        "Investisseurs immobilier commercial",
        "Franchiseurs cherchant expansion",
        "Banques microfinance"
    ],
    "our_solution": "Urban Intelligence Platform — cartographie pouvoir d'achat + stratégie implantation + réseau distributeurs locaux",
    "market_size_eu": 35000000,  # EUR addressable
    "satisfaction_current": 0.15,
    "margin_target": 0.65,
    "channels": ["Mairies QPV", "BPI France", "Fédérations commerçants", "CDC / Action Logement"],
}

INTELLIGENCE_PRODUCTS = {
    "market_audit": {
        "price": 8000, "deliverable": "Cartographie complète pouvoir d'achat + gaps offre",
        "timeline_days": 14, "coverage": "1 quartier / arrondissement"
    },
    "implantation_strategy": {
        "price": 25000, "deliverable": "Stratégie implantation + réseau distributeurs identifiés + plan go-to-market",
        "timeline_days": 30
    },
    "full_ecosystem": {
        "price": 50000, "deliverable": "Audit + stratégie + accompagnement 6 mois + KPIs",
        "timeline_days": 180, "roi_guarantee": "CA additionnel minimum 200K€ en 12 mois"
    },
    "data_subscription": {
        "price_monthly": 500, "deliverable": "Dashboard live — flux, achats, démographie, tendances",
        "update_frequency": "Mensuel"
    },
}

def get_urban_intel_quote(scope: str = "market_audit", zones: int = 1) -> Dict:
    product = INTELLIGENCE_PRODUCTS.get(scope, INTELLIGENCE_PRODUCTS["market_audit"]).copy()
    if scope in ["market_audit", "implantation_strategy"] and zones > 1:
        multi_zone_discount = 0.20 if zones >= 5 else 0.10
        product["price"] = round(product["price"] * zones * (1 - multi_zone_discount))
    product["scope"] = scope
    product["zones"] = zones
    product["report_language"] = ["FR", "EN", "AR"]
    return product
