"""PAIN: Réparation Cutanée — PROJECT_03 NAYA BOTANICA"""
from typing import Dict, List

PAIN = {
    "name": "Réparation & Régénération Cutanée Naturelle",
    "description": "Femmes 30-55 ans souffrant de peau abîmée, sensible, déshydratée sans solutions naturelles efficaces",
    "urgency": "MEDIUM",
    "price_range": (45, 180),
    "target_segments": ["Peaux sensibles", "Post-acné", "Déshydratation chronique", "Rougeurs réactives"],
    "our_solution": "Gamme NAYA Botanica Repair — actifs 100% naturels certifiés COSMOS",
    "market_size_europe": 1200000,
    "satisfaction_current": 0.40,
    "margin_target": 0.72,
    "channels": ["Instagram beauty", "Pharmacies", "Parapharmacies", "Site DTC"],
}

REPAIR_PRODUCTS = [
    {"id": "NB_R01", "name": "Sérum Réparateur Nuit Botanica", "price": 68, "cost": 18, "volume": "30ml",
     "key_actives": ["Bakuchiol bio", "Huile rosehip", "Panthénol"], "routine": "Soir"},
    {"id": "NB_R02", "name": "Crème Barrière SOS", "price": 52, "cost": 14, "volume": "50ml",
     "key_actives": ["Centella asiatica", "Squalane végétal", "Bisabolol"], "routine": "Matin + soir"},
    {"id": "NB_R03", "name": "Masque Réparateur Intensif", "price": 45, "cost": 11, "volume": "75ml",
     "key_actives": ["Aloe vera 99%", "Argile blanche", "Huile camomille"], "routine": "2x/semaine"},
    {"id": "NB_R04", "name": "Starter Kit Réparation", "price": 148, "cost": 35,
     "includes": ["NB_R01", "NB_R02", "NB_R03"], "savings": 17},
]

def get_recommendation(skin_type: str = "sensitive") -> Dict:
    routines = {
        "sensitive":     ["NB_R02", "NB_R03"],
        "dehydrated":    ["NB_R01", "NB_R02"],
        "post_acne":     ["NB_R01", "NB_R03"],
        "reactive":      ["NB_R02"],
    }
    product_ids = routines.get(skin_type, ["NB_R02"])
    products = [p for p in REPAIR_PRODUCTS if p["id"] in product_ids]
    total = sum(p["price"] for p in products)
    return {"skin_type": skin_type, "products": products, "total": total,
            "results_in_days": 21, "guarantee": "Remboursement 30 jours si pas de résultat visible"}
