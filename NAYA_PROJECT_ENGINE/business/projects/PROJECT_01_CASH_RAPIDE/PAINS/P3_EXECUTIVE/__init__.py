"""P3 EXECUTIVE — 25k-75k€ — Livraison 72H"""
from typing import Dict

P3_SERVICES = [
    {"id": "P3_01", "name": "Transformation digitale PME", "price": 40000,
     "deliverable": "Architecture complète + implémentation + 3 mois suivi"},
    {"id": "P3_02", "name": "Stratégie revenue growth SaaS", "price": 35000,
     "deliverable": "Audit + roadmap + implémentation 90j + team training"},
    {"id": "P3_03", "name": "Système recouvrement enterprise", "price": 25000,
     "deliverable": "Process + outils + équipe formée + 6 mois suivi"},
    {"id": "P3_04", "name": "Revenue management hôtellerie", "price": 50000,
     "deliverable": "Stratégie + outils + pilotage 6 mois"},
]

def get_p3_offer(pain: str) -> Dict:
    return {"services": P3_SERVICES, "min_price": 25000, "max_price": 75000,
            "timeline": "72H conception + implémentation progressive"}
