"""PAIN: Hyperpigmentation — PROJECT_03 NAYA BOTANICA"""
from typing import Dict

PAIN = {
    "name": "Hyperpigmentation & Taches Brunes",
    "description": "Femmes peau foncée/mate avec taches post-inflammatoires, mélasma, taches solaires — marché sous-servi",
    "urgency": "HIGH",
    "price_range": (55, 220),
    "target_segments": ["Peaux foncées (III-VI Fitzpatrick)", "Mélasma hormonal", "Taches solaires", "PIH post-acné"],
    "our_solution": "Gamme NAYA Botanica Eclat — brightening naturel sans hydroquinone",
    "market_size_europe": 2800000,
    "satisfaction_current": 0.25,  # Marché très sous-servi
    "margin_target": 0.74,
    "channels": ["Instagram (community beauté noire/métisse)", "Afrobella influenceurs", "Pharmacies afro", "Site DTC"],
}

ECLAT_PRODUCTS = [
    {"id": "NB_E01", "name": "Sérum Eclat Unifiant", "price": 78, "cost": 20, "volume": "30ml",
     "key_actives": ["Alpha-arbutine 2%", "Niacinamide 10%", "Acide tranexamique", "Vitamine C stable"],
     "results": "Première amélioration visible J+14"},
    {"id": "NB_E02", "name": "Masque Brightening Hebdomadaire", "price": 55, "cost": 14, "volume": "75ml",
     "key_actives": ["Papaye enzymes", "Acide lactique 5%", "Réglisse extrait"],
     "results": "Éclat immédiat + unifiant progressif"},
    {"id": "NB_E03", "name": "SPF50 Invisible Peau Foncée", "price": 48, "cost": 13, "volume": "50ml",
     "key_actives": ["Filtres minéraux transparents", "Niacinamide", "Aloé vera"],
     "results": "Protection + pas de cast blanc"},
    {"id": "NB_E04", "name": "Protocole Hyperpigmentation 90J", "price": 198, "cost": 43,
     "includes": ["NB_E01 x2", "NB_E02", "NB_E03"], "savings": 20,
     "protocol_weeks": 12, "expected_improvement": "60-80% réduction taches"},
]

def get_hyperpig_protocol(severity: str = "moderate") -> Dict:
    protocols = {
        "mild":     {"duration_weeks": 8,  "products": ["NB_E01", "NB_E03"], "price": 126},
        "moderate": {"duration_weeks": 12, "products": ["NB_E01", "NB_E02", "NB_E03"], "price": 181},
        "severe":   {"duration_weeks": 16, "products": ["NB_E04"], "price": 198,
                     "dermo_referral": True},
    }
    return {**protocols.get(severity, protocols["moderate"]), "severity": severity,
            "guarantee": "Visible improvement in 30 days or refund"}
