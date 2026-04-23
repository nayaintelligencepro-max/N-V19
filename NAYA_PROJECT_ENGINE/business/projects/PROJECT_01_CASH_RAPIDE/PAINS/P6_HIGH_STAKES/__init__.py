"""P6 HIGH STAKES — 500k€+ — Situations à enjeux critiques"""
from typing import Dict, List

P6_SERVICES = [
    {"id": "P6_01", "name": "Transformation globale groupe international",
     "price": 1500000, "timeline": "6-12 mois",
     "deliverable": "Nouveau modèle opérationnel mondial + culture + systèmes",
     "sectors": ["Multinationales", "Groupes cotés", "Fonds institutionnels"]},
    {"id": "P6_02", "name": "Écosystème IA propriétaire complet",
     "price": 750000, "timeline": "4-6 mois",
     "deliverable": "LLM propriétaire + orchestration + intégration métier + équipe IA",
     "sectors": ["Banques", "Assurances", "Groupes industriels", "Médias"]},
    {"id": "P6_03", "name": "Programme IPO/cession préparation",
     "price": 600000, "timeline": "3-6 mois",
     "deliverable": "Data room complète + VDD + management package + narrative investisseur",
     "sectors": ["Scale-ups", "ETI cession", "LBO secondaire"]},
    {"id": "P6_04", "name": "Crise opérationnelle — intervention d'urgence",
     "price": 500000, "timeline": "48H mobilisation + 30 jours intervention",
     "deliverable": "Stabilisation + plan de redressement + exécution 90 jours",
     "sectors": ["Toutes industries en situation critique"]},
]

def get_p6_engagement(crisis_level: str = "strategic") -> Dict:
    packages = {
        "operational_crisis": {"price": 500000, "mobilization_hours": 48, "duration_days": 30},
        "strategic":          {"price": 750000, "mobilization_hours": 72, "duration_days": 90},
        "global_transform":   {"price": 1500000, "mobilization_hours": 120, "duration_days": 365},
        "ipo_prep":           {"price": 600000, "mobilization_hours": 96, "duration_days": 120},
    }
    pkg = packages.get(crisis_level, packages["strategic"])
    return {**pkg, "type": crisis_level, "team_size": "5-15 experts",
            "engagement_model": "Forfait + intéressement résultats",
            "cancellation": "Pénalité 30% si annulation J-7"}

HIGH_STAKES_FLOOR = 500000
