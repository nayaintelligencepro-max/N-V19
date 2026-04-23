"""PAIN: Absence d'Offre Structurée — PROJECT_05 MARCHÉS OUBLIÉS"""
from typing import Dict

PAIN = {
    "name": "Absence d'Offre Structurée pour Marchés Sous-Servis",
    "description": "Communautés africaines, antillaises, maghrébines en Europe — pouvoir d'achat réel mais aucune offre structurée adaptée culturellement",
    "urgency": "HIGH",
    "price_range": (29, 299),  # abonnements + services
    "target_segments": [
        "Diaspora africaine (5M+ en Europe)",
        "Communautés caribéennes",
        "Entrepreneurs issus des diasporas",
        "PME ciblant ces marchés"
    ],
    "our_solution": "Plateforme multiservice diaspora — banque, transfert, marketplace, coaching business",
    "market_size_eu": 18000000,
    "satisfaction_current": 0.20,
    "margin_target": 0.62,
    "channels": ["Facebook groupes diaspora", "WhatsApp communities", "Radio africaine FR", "Mosquées / Églises"],
}

SERVICE_CATALOG = {
    "transfert_argent": {
        "fee_pct": 1.5, "competitors_avg_fee": 6.5, "saving_per_transfer": "5%",
        "monthly_active": "Récurrent fort"
    },
    "marketplace_produits": {
        "commission": 8, "avg_basket": 85, "categories": ["Alimentaire africain", "Beauté", "Mode", "Art"]
    },
    "coaching_business": {
        "price_monthly": 89, "includes": ["Mentor communautaire", "Accès réseau", "Formations"],
        "churn_rate_expected": 0.08
    },
    "compte_diaspora": {
        "price_monthly": 12, "features": ["IBAN EU", "Carte Visa", "Transferts gratuits x5/mois"],
        "ltv_estimate": 1800
    },
}

def get_offer_bundle(segment: str = "entrepreneur") -> Dict:
    bundles = {
        "particulier":   {"monthly": 29,  "services": ["compte_diaspora", "transfert_argent"]},
        "entrepreneur":  {"monthly": 89,  "services": ["compte_diaspora", "coaching_business", "marketplace_produits"]},
        "pme_partenaire":{"monthly": 299, "services": ["marketplace_produits", "coaching_business"],
                          "reach": "Accès 50K+ membres certifiés"},
    }
    b = bundles.get(segment, bundles["entrepreneur"])
    return {**b, "segment": segment, "trial_days": 30, "cancel_anytime": True}
