"""P1 PREMIUM — 1k-5k€ — Livraison 24H"""
from typing import Dict, List

P1_SERVICES = [
    {"id": "P1_01", "name": "Audit trésorerie express", "price": 2000, "hours": 4,
     "deliverable": "Rapport + plan action", "sectors": ["PME", "B2B", "Freelance"]},
    {"id": "P1_02", "name": "Diagnostic campagne ads", "price": 2500, "hours": 5,
     "deliverable": "Rapport + recommandations", "sectors": ["E-com", "SaaS"]},
    {"id": "P1_03", "name": "Audit référencement local", "price": 1500, "hours": 3,
     "deliverable": "Rapport GMB + SEO local", "sectors": ["Restaurant", "Médical", "Retail"]},
    {"id": "P1_04", "name": "Review contrat urgent", "price": 3000, "hours": 6,
     "deliverable": "Analyse + risques + recommandations", "sectors": ["B2B", "Immo"]},
    {"id": "P1_05", "name": "Diagnostic rentabilité restaurant", "price": 1500, "hours": 5,
     "deliverable": "Analyse + 5 quick wins", "sectors": ["Restaurant"]},
]

def get_p1_offer(pain: str, urgency: float = 0.7) -> Dict:
    best = sorted(P1_SERVICES, key=lambda s: abs(s["price"] - 2000))[0]
    return {"service": best, "price": best["price"] * (1 + urgency * 0.3),
            "timeline": "24H", "guarantee": "Satisfait ou remboursé 48H"}
