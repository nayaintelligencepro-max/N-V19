"""PAIN: Fermeté Corps — PROJECT_03 NAYA BOTANICA"""
from typing import Dict, List

PAIN = {
    "name": "Fermeté & Remodelage Corporel Naturel",
    "description": "Femmes 35-60 ans cherchant alternatives naturelles efficaces aux soins corps raffermissants — déception produits mass market",
    "urgency": "LOW",
    "price_range": (35, 150),
    "target_segments": ["Post-grossesse", "Perte de poids récente", "Anti-cellulite", "Fermeté bras/ventre"],
    "our_solution": "Gamme NAYA Botanica Corps — actifs tenseurs + drainants + raffermissants bio",
    "market_size_europe": 950000,
    "satisfaction_current": 0.35,
    "margin_target": 0.68,
    "channels": ["Instagram wellness", "Maternités (partenaires)", "Kinésithérapeutes", "Site DTC"],
}

BODY_PRODUCTS = [
    {"id": "NB_B01", "name": "Huile Raffermissante Corps", "price": 58, "cost": 15, "volume": "100ml",
     "key_actives": ["Caféine 2%", "Huile d'argan", "Centella asiatica", "Tocophérol"],
     "application": "Massage circulaire 5 min matin"},
    {"id": "NB_B02", "name": "Crème Ventre Post-Grossesse", "price": 65, "cost": 17, "volume": "200ml",
     "key_actives": ["Extrait de laminaire", "Beurre karité", "Huile jojoba", "Allantoine"],
     "application": "2x/jour sur ventre + seins"},
    {"id": "NB_B03", "name": "Gommage Sculptant Caféine", "price": 38, "cost": 9, "volume": "200ml",
     "key_actives": ["Caféine 3%", "Sucre de canne", "Café vert", "Huile coco"],
     "application": "3x/semaine sous douche"},
    {"id": "NB_B04", "name": "Kit Corps Fermeté 30 Jours", "price": 138, "cost": 32,
     "includes": ["NB_B01", "NB_B02", "NB_B03"], "savings": 23,
     "protocol": "Programme 30 jours inclus + guide massage"},
]

def get_body_protocol(concern: str = "general_firming") -> Dict:
    protocols = {
        "post_pregnancy":  {"products": ["NB_B02", "NB_B01"], "duration_weeks": 12},
        "cellulite":       {"products": ["NB_B03", "NB_B01"], "duration_weeks": 8},
        "general_firming": {"products": ["NB_B04"], "duration_weeks": 4},
        "post_weight_loss":{"products": ["NB_B01", "NB_B02", "NB_B03"], "duration_weeks": 16},
    }
    p = protocols.get(concern, protocols["general_firming"])
    products = [prod for prod in BODY_PRODUCTS if prod["id"] in p.get("products", ["NB_B04"])]
    return {**p, "concern": concern, "products_detail": products,
            "total_price": sum(prod["price"] for prod in products),
            "expected_results": "Fermeté +15-25% en 4-8 semaines",
            "guarantee": "Satisfait ou remboursé 30 jours"}
